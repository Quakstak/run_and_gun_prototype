# animation.py
from __future__ import annotations
import pygame


class Animation:
    """
    Time-based sprite animation.

    - frame_duration is seconds per frame (e.g., 0.20).
    - speed multiplier: 1.0 = normal, 2.0 = twice as fast, 0.5 = half speed.
    - Call update(dt) every frame, and use image for drawing.
    """

    def __init__(
        self,
        frames: list[pygame.Surface],
        frame_duration: float = 0.12,
        loop: bool = True,
    ):
        if not frames:
            raise ValueError("Animation requires at least one frame.")

        self.frames = frames
        self.frame_duration = max(0.001, float(frame_duration))
        self.loop = loop

        self.index = 0
        self.timer = 0.0
        self.finished = False

    @property
    def image(self) -> pygame.Surface:
        return self.frames[self.index]

    def reset(self) -> None:
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt: float, speed: float = 1.0) -> None:
        if self.finished:
            return

        speed = max(0.0, float(speed))
        if speed == 0.0:
            return

        # Prevent hitch frames from skipping many frames (looks like tearing/flicker)
        dt = min(float(dt), 1 / 30)

        self.timer += dt * speed

        # Advance at most ONE frame per update (stable & readable)
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.index += 1

            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True