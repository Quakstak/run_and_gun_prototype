# pickup.py
# Pickups/Powerups. Add more types by extending PickUp and overriding apply().

from __future__ import annotations
import pygame
from .utils import load_image, slice_sprite_sheet_row

class PickUp(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int,int], kind: str = "health"):
        super().__init__()
        self.kind = kind

        sheet = load_image("pickup_sheet.png")
        self.frames = slice_sprite_sheet_row(sheet, row=0, frame_w=32, frame_h=32, num_frames=2)
        self.frame_i = 0
        self.frame_time = 0.0

        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=pos)

    def apply(self, player) -> None:
        """What happens when the player collects this pickup."""
        if self.kind == "health":
            player.heal(25)

    def update(self, dt: float, *_args) -> None:
        # tiny animation loop
        self.frame_time += dt
        if self.frame_time >= 0.25:
            self.frame_time = 0.0
            self.frame_i = (self.frame_i + 1) % len(self.frames)
            self.image = self.frames[self.frame_i]
