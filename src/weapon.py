# weapon.py
# Weapon + Bullet classes.
#
# Note for students:
# - A Weapon decides *how to shoot* (fire rate, bullet speed, spread, etc.)
# - A Bullet is a small moving object with lifetime + collisions.

from __future__ import annotations
import pygame
from . import settings

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos: pygame.Vector2, direction: int):
        super().__init__()
        self.image = pygame.Surface((10, 4), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 230, 120), (0, 0, 10, 4))
        self.rect = self.image.get_rect(center=(pos.x, pos.y))

        self.vel = pygame.Vector2(settings.BULLET_SPEED * direction, 0.0)
        self.lifetime = settings.BULLET_LIFETIME
        self.alive_time = 0.0

    def update(self, dt: float, level) -> None:
        # move
        self.rect.x += int(self.vel.x * dt)
        self.rect.y += int(self.vel.y * dt)

        # despawn after lifetime
        self.alive_time += dt
        if self.alive_time >= self.lifetime:
            self.kill()
            return

        # collide with solid tiles
        if level.rect_collides_solid(self.rect):
            self.kill()

class Weapon:
    """Basic semi-auto weapon."""
    def __init__(self):
        self.cooldown = 0.15   # seconds between shots
        self.time_since_shot = 999.0

    def update(self, dt: float) -> None:
        self.time_since_shot += dt

    def can_shoot(self) -> bool:
        return self.time_since_shot >= self.cooldown

    def shoot(self, bullets_group: pygame.sprite.Group, pos: pygame.Vector2, direction: int) -> None:
        if not self.can_shoot():
            return
        self.time_since_shot = 0.0
        bullets_group.add(Bullet(pos, direction))
