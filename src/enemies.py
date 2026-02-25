# enemies.py
# NormalEnemy + BossEnemy.
#
# Design goal:
# - Keep behaviour simple and readable for first-year students.
# - Use small, clearly-named methods students can modify.

from __future__ import annotations
import pygame
from .utils import load_image, slice_sprite_sheet_row
from . import settings
from .weapon import Weapon

class NormalEnemy(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int,int]):
        super().__init__()
        sheet = load_image("enemy_sheet.png")
        self.frames = slice_sprite_sheet_row(sheet, row=0, frame_w=32, frame_h=32, num_frames=2)
        self.frame_i = 0
        self.frame_time = 0.0

        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=pos)

        self.vel = pygame.Vector2(-80.0, 0.0)  # patrol left
        self.health = 30
        self.on_ground = False

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def update(self, dt: float, level, player) -> None:
        # animate
        self.frame_time += dt
        if self.frame_time >= 0.25:
            self.frame_time = 0.0
            self.frame_i = (self.frame_i + 1) % len(self.frames)
            self.image = self.frames[self.frame_i]

        # gravity
        self.vel.y += settings.GRAVITY * dt

        # horizontal move + simple edge/obstacle turn-around
        self.rect.x += int(self.vel.x * dt)
        if level.rect_collides_solid(self.rect):
            # undo and turn around
            self.rect.x -= int(self.vel.x * dt)
            self.vel.x *= -1

        # vertical collisions
        self.rect.y += int(self.vel.y * dt)
        self.on_ground = False
        hits = level.get_solid_hits(self.rect)
        for tile_rect in hits:
            if self.vel.y > 0:  # falling
                self.rect.bottom = tile_rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:  # jumping up (rare)
                self.rect.top = tile_rect.bottom
                self.vel.y = 0

        # Don't let enemies wander off into the void
        if self.rect.top > level.pixel_height + 200:
            self.kill()

class BossEnemy(pygame.sprite.Sprite):
    """A simple boss with more health + ranged shots."""
    def __init__(self, pos: tuple[int,int]):
        super().__init__()
        sheet = load_image("boss_sheet.png")
        self.frames = slice_sprite_sheet_row(sheet, row=0, frame_w=64, frame_h=64, num_frames=2)
        self.frame_i = 0
        self.frame_time = 0.0

        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(pos[0]+32, pos[1]+32))  # slightly centred

        self.health = 180
        self.max_health = 180

        self.vel = pygame.Vector2(0.0, 0.0)
        self.speed = 110.0

        self.weapon = Weapon()
        self.weapon.cooldown = 0.6  # slower shots

        self.on_ground = False

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def update(self, dt: float, level, player, boss_bullets) -> None:
        # animate
        self.frame_time += dt
        if self.frame_time >= 0.35:
            self.frame_time = 0.0
            self.frame_i = (self.frame_i + 1) % len(self.frames)
            self.image = self.frames[self.frame_i]

        # simple horizontal chase within arena
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.vel.x = self.speed * direction

        # gravity
        self.vel.y += settings.GRAVITY * dt

        # horizontal collision
        self.rect.x += int(self.vel.x * dt)
        if level.rect_collides_solid(self.rect):
            self.rect.x -= int(self.vel.x * dt)
            self.vel.x = 0

        # vertical collision
        self.rect.y += int(self.vel.y * dt)
        self.on_ground = False
        hits = level.get_solid_hits(self.rect)
        for tile_rect in hits:
            if self.vel.y > 0:
                self.rect.bottom = tile_rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = tile_rect.bottom
                self.vel.y = 0

        # shoot towards player
        self.weapon.update(dt)
        if self.weapon.can_shoot():
            muzzle = pygame.Vector2(self.rect.centerx + 18*direction, self.rect.centery - 8)
            self.weapon.shoot(boss_bullets, muzzle, direction)
