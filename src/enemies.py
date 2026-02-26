# enemies.py
from __future__ import annotations
import random
import pygame
from .utils import load_image, slice_sprite_sheet_row
from .animation import Animation
from .weapon import Weapon
from . import settings


class EnemyBase(pygame.sprite.Sprite):
    """Shared functionality for simple enemies (health, animation, optional facing)."""
    def __init__(self):
        super().__init__()
        self.health = 1
        self.facing = 1  # 1 right, -1 left

        self.current_anim: Animation | None = None
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def apply_anim(self, dt: float) -> None:
        """Advance current animation and apply facing flip."""
        if not self.current_anim:
            return
        self.current_anim.update(dt)
        img = self.current_anim.image
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        self.image = img

    def face_player(self, player) -> int:
        self.facing = 1 if player.rect.centerx > self.rect.centerx else -1
        return self.facing


class NormalEnemy(EnemyBase):
    """Simple patrol enemy."""
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("enemy_runner_sheet.png")
        frames = slice_sprite_sheet_row(
            sheet, row=0, frame_w=32, frame_h=32,
            num_frames=6, stride_x=64, start_x=0, start_y=0, clamp=True
        )

        self.walk_anim = Animation(frames, frame_duration=0.10, loop=True)
        self.current_anim = self.walk_anim

        self.image = self.current_anim.image
        self.rect = self.image.get_rect(topleft=pos)

        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel = pygame.Vector2(-80.0, 0.0)

        self.health = 30
        self.on_ground = False
        self.facing = 1

    def update(self, dt: float, level, player) -> None:
        # gravity
        self.vel.y += settings.GRAVITY * dt

        # horizontal (float)
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        if level.rect_collides_solid(self.rect):
            self.pos.x -= self.vel.x * dt
            self.rect.x = round(self.pos.x)
            self.vel.x *= -1
            self.facing *= -1

        # vertical (float)
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

        # ground probe
        if not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        # animation
        self.apply_anim(dt)

        # fell off world
        if self.rect.top > level.pixel_height + 200:
            self.kill()


class ShooterEnemy(EnemyBase):
    """
    Stationary shooter (e.g., turret/guard).
    Shoots towards the player with some inaccuracy (spread).
    """
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("enemy_shooter_sheet.png")  # or reuse enemy_sheet.png if you prefer

        # Example: row 0 = idle, row 1 = shoot (optional)
        idle_frames = slice_sprite_sheet_row(sheet, row=0, frame_w=32, frame_h=32, num_frames=8, stride_x=95, start_x=0, start_y=0, clamp=True)

        self.idle_anim = Animation(idle_frames, frame_duration=0.25, loop=True)
        self.current_anim = self.idle_anim

        self.image = self.current_anim.image
        self.rect = self.image.get_rect(topleft=pos)

        self.health = 20

        # Weapon tuning for "not very accurate"
        self.weapon = Weapon()
        self.weapon.cooldown = 0.9  # slower than player

        # Spread controls vertical aim error (pixels at spawn). Increase for worse accuracy.
        self.spread_px = 14

        # Optional: only shoot if player is roughly in range
        self.range_px = 520

    def update(self, dt: float, level, player, enemy_bullets: pygame.sprite.Group) -> None:
        # Face player
        direction = self.face_player(player)

        # Animate idle
        self.apply_anim(dt)

        # Update weapon timer
        self.weapon.update(dt)

        # Optional range check
        dx = abs(player.rect.centerx - self.rect.centerx)
        if dx > self.range_px:
            return

        if self.weapon.can_shoot():
            # Always shoot from the shooter's own centre height
            muzzle = pygame.Vector2(
                self.rect.centerx + 16 * direction,   # 16 = half of 32px sprite
                self.rect.centery + 4                 # tweak vertical offset if needed
            )

            self.weapon.shoot(enemy_bullets, muzzle, direction)


class BossEnemy(EnemyBase):
    """A simple boss with more health + ranged shots."""
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("enemy_boss_sheet.png")
        frames = slice_sprite_sheet_row(sheet, row=0, frame_w=64, frame_h=64, num_frames=2, stride_x=64, start_x=0, start_y=0, clamp=True)

        self.anim = Animation(frames, frame_duration=0.30, loop=True)
        self.current_anim = self.anim

        self.image = self.current_anim.image
        self.rect = self.image.get_rect(midbottom=(pos[0] + 32, pos[1] + 32))
        self.pos = pygame.Vector2(self.rect.topleft)

        self.health = 180
        self.max_health = 180

        self.vel = pygame.Vector2(0.0, 0.0)
        self.speed = 110.0

        self.weapon = Weapon()
        self.weapon.cooldown = 0.6

        self.on_ground = False

    def update(self, dt: float, level, player, boss_bullets) -> None:
        direction = self.face_player(player)
        self.vel.x = self.speed * direction

        self.vel.y += settings.GRAVITY * dt

        # horizontal
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        if level.rect_collides_solid(self.rect):
            self.pos.x -= self.vel.x * dt
            self.rect.x = round(self.pos.x)
            self.vel.x = 0

        # vertical
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

        if not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        # animation
        self.apply_anim(dt)

        # shoot
        self.weapon.update(dt)
        if self.weapon.can_shoot():
            muzzle = pygame.Vector2(self.rect.centerx + 18 * direction, self.rect.centery - 8)
            self.weapon.shoot(boss_bullets, muzzle, direction)