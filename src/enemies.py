# enemies.py
# NormalEnemy + BossEnemy (updated to use Animation class + float movement)

from __future__ import annotations
import pygame
from .utils import load_image, slice_sprite_sheet_row
from .animation import Animation
from . import settings
from .weapon import Weapon


# ------------------------------------------------------------
# NORMAL ENEMY
# ------------------------------------------------------------

class NormalEnemy(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("enemy_sheet.png")

        frames = slice_sprite_sheet_row(sheet, row=0, frame_w=32, frame_h=32, num_frames=6, stride_x=64, start_x=0, start_y=0, clamp=True)

        # Animation (slow and readable)
        self.walk_anim = Animation(frames, frame_duration=0.05, loop=True)
        self.current_anim = self.walk_anim

        self.image = self.current_anim.image
        self.rect = self.image.get_rect(topleft=pos)

        # Float position (prevents grounding flicker)
        self.pos = pygame.Vector2(self.rect.topleft)

        self.vel = pygame.Vector2(-80.0, 0.0)
        self.health = 30
        self.on_ground = False
        self.facing = 1

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def update(self, dt: float, level, player) -> None:

        # --- Gravity ---
        self.vel.y += settings.GRAVITY * dt

        # --- Horizontal movement (float) ---
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        if level.rect_collides_solid(self.rect):
            self.pos.x -= self.vel.x * dt
            self.rect.x = round(self.pos.x)
            self.vel.x *= -1
            self.facing *= -1

        # --- Vertical movement (float) ---
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)

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

            self.pos.y = self.rect.y

        # Ground probe (stabilises idle ground state)
        if not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        # --- Animation ---
        self.current_anim.update(dt)

        img = self.current_anim.image
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        self.image = img

        # --- Kill if fallen ---
        if self.rect.top > level.pixel_height + 200:
            self.kill()


# ------------------------------------------------------------
# BOSS ENEMY
# ------------------------------------------------------------

class BossEnemy(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("boss_sheet.png")
        frames = slice_sprite_sheet_row(sheet, row=0, frame_w=64, frame_h=64, num_frames=2, stride_x=64, start_x=0, start_y=0, clamp=True)

        self.anim = Animation(frames, frame_duration=0.30, loop=True)
        self.image = self.anim.image

        self.rect = self.image.get_rect(midbottom=(pos[0] + 32, pos[1] + 32))

        self.pos = pygame.Vector2(self.rect.topleft)

        self.health = 180
        self.max_health = 180

        self.vel = pygame.Vector2(0.0, 0.0)
        self.speed = 110.0

        self.weapon = Weapon()
        self.weapon.cooldown = 0.6

        self.on_ground = False
        self.facing = 1

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def update(self, dt: float, level, player, boss_bullets) -> None:

        # --- Simple chase ---
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.vel.x = self.speed * direction
        self.facing = direction

        # --- Gravity ---
        self.vel.y += settings.GRAVITY * dt

        # --- Horizontal ---
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        if level.rect_collides_solid(self.rect):
            self.pos.x -= self.vel.x * dt
            self.rect.x = round(self.pos.x)
            self.vel.x = 0

        # --- Vertical ---
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)

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

            self.pos.y = self.rect.y

        # Ground probe
        if not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        # --- Animation ---
        self.anim.update(dt)

        img = self.anim.image
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        self.image = img

        # --- Shooting ---
        self.weapon.update(dt)
        if self.weapon.can_shoot():
            muzzle = pygame.Vector2(
                self.rect.centerx + 18 * direction,
                self.rect.centery - 8
            )
            self.weapon.shoot(boss_bullets, muzzle, direction)