# utils.py
# Small helpers so core classes stay readable.

from __future__ import annotations
import os
import pygame

def asset_path(*parts: str) -> str:
    """Build a path relative to the project root."""
    here = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(here, "assets", *parts)

def load_image(*parts: str) -> pygame.Surface:
    """Load an image with per-pixel alpha."""
    path = asset_path("images", *parts)
    return pygame.image.load(path).convert_alpha()

def load_sound(*parts: str) -> pygame.mixer.Sound:
    path = asset_path("audio", *parts)
    return pygame.mixer.Sound(path)

def slice_sprite_sheet_row(sheet: pygame.Surface, row: int, frame_w: int, frame_h: int, num_frames: int) -> list[pygame.Surface]:
    """
    Slice frames from a single row of a sprite sheet.

    This is a common beginner-friendly format:
    - multiple rows = different animations
    - each row has N frames
    """
    frames = []
    y = row * frame_h
    for i in range(num_frames):
        x = i * frame_w
        frame = sheet.subsurface(pygame.Rect(x, y, frame_w, frame_h))
        frames.append(frame)
    return frames

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
