# player.py
# Improved jump responsiveness:
# - Jump buffer
# - Coyote time
# - Variable jump height (short hop)

from __future__ import annotations
import pygame
from .utils import load_image, slice_sprite_sheet_row
from .weapon import Weapon
from . import settings


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        # Sprite sheet: row 0 idle, row 1 run, row 2 jump
        sheet = load_image("player_sheet.png")
        self.anim_idle = slice_sprite_sheet_row(sheet, 4, 32, 32, 6)
        self.anim_run  = slice_sprite_sheet_row(sheet, 3, 32, 32, 8)
        self.anim_jump = slice_sprite_sheet_row(sheet, 5, 32, 32, 8)

        self.image = self.anim_idle[0]
        self.rect = self.image.get_rect(topleft=pos)

        # Physics
        self.vel = pygame.Vector2(0.0, 0.0)
        self.on_ground = False
        self.facing = 1

        # Jump feel improvements
        self.jump_buffer_time = 0.12
        self.jump_buffer = 0.0

        self.coyote_time = 0.10
        self.coyote_timer = 0.0

        # Combat
        self.weapon = Weapon()
        self.health = settings.PLAYER_MAX_HEALTH
        self.max_health = settings.PLAYER_MAX_HEALTH
        self.invuln_time = 0.0

        # Animation
        self.frame_i = 0
        self.frame_time = 0.0
        self.current_anim = self.anim_idle

    # --------------------------
    # Health
    # --------------------------

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount: int) -> None:
        if self.invuln_time > 0:
            return
        self.health -= amount
        self.invuln_time = 0.6
        if self.health < 0:
            self.health = 0

    def is_dead(self) -> bool:
        return self.health <= 0

    # --------------------------
    # Input
    # --------------------------

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.vel.x = 0.0

        if keys[pygame.K_a]:
            self.vel.x -= settings.PLAYER_SPEED
            self.facing = -1

        if keys[pygame.K_d]:
            self.vel.x += settings.PLAYER_SPEED
            self.facing = 1

    def queue_jump(self) -> None:
        """Called on key press. Stores jump for short time."""
        self.jump_buffer = self.jump_buffer_time

    def cut_jump(self) -> None:
        """Called on key release for variable jump height."""
        if self.vel.y < 0:
            self.vel.y *= 0.45

    def try_shoot(self, bullets_group: pygame.sprite.Group) -> bool:
        muzzle = pygame.Vector2(
            self.rect.centerx + 16 * self.facing,
            self.rect.centery - 6
        )
        before = len(bullets_group)
        self.weapon.shoot(bullets_group, muzzle, self.facing)
        return len(bullets_group) > before

    # --------------------------
    # Update
    # --------------------------

    def update(self, dt: float, level) -> None:

        # Timers
        if self.invuln_time > 0:
            self.invuln_time = max(0.0, self.invuln_time - dt)

        if self.jump_buffer > 0:
            self.jump_buffer = max(0.0, self.jump_buffer - dt)

        if self.coyote_timer > 0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        self.weapon.update(dt)

        # Gravity
        self.vel.y += settings.GRAVITY * dt

        # Horizontal movement
        self.rect.x += int(self.vel.x * dt)
        hits = level.get_solid_hits(self.rect)
        for tile_rect in hits:
            if self.vel.x > 0:
                self.rect.right = tile_rect.left
            elif self.vel.x < 0:
                self.rect.left = tile_rect.right

        # Vertical movement
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

        # Coyote time reset
        if self.on_ground:
            self.coyote_timer = self.coyote_time

        # Buffered jump
        can_jump = self.on_ground or self.coyote_timer > 0.0
        if self.jump_buffer > 0 and can_jump:
            self.vel.y = -settings.JUMP_SPEED
            self.on_ground = False
            self.coyote_timer = 0.0
            self.jump_buffer = 0.0

        # Animation
        if not self.on_ground:
            self.set_anim(self.anim_jump, dt, speed=1.0)
        elif abs(self.vel.x) > 1:
            self.set_anim(self.anim_run, dt, speed=1.0)
        else:
            self.set_anim(self.anim_idle, dt, speed=1.0)

    # --------------------------
    # Animation helper
    # --------------------------

    def set_anim(self, frames: list[pygame.Surface], dt: float, speed: float) -> None:
        if self.current_anim is not frames:
            self.current_anim = frames
            self.frame_i = 0
            self.frame_time = 0.0

        self.frame_time += dt * speed
        if self.frame_time >= 1.0:
            self.frame_time = 0.0
            self.frame_i = (self.frame_i + 1) % len(frames)

        img = frames[self.frame_i]

        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)

        self.image = img