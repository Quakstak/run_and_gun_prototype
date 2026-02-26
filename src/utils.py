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

def slice_sprite_sheet_row(
    sheet: pygame.Surface,
    row: int,
    frame_w: int,
    frame_h: int,
    num_frames: int,
    *,
    stride_x: int,
    start_x: int = 0,
    start_y: int = 0,
    clamp: bool = True
) -> list[pygame.Surface]:
    """
    Slice frames from a sprite sheet row using an explicit horizontal stride.

    stride_x is the distance in pixels from one frame's left edge to the next.
    Example for [32 sprite][32 blank] repeating: stride_x = 64.

    clamp=True  -> stop slicing when we'd go out of bounds (safe).
    clamp=False -> raise ValueError if requested frames exceed sheet bounds.
    """
    frames: list[pygame.Surface] = []
    sheet_w, sheet_h = sheet.get_size()

    y = start_y + row * frame_h
    if y + frame_h > sheet_h:
        raise ValueError(f"Row {row} out of bounds: y={y}, sheet_h={sheet_h}, frame_h={frame_h}")

    for i in range(num_frames):
        x = start_x + i * stride_x
        if x + frame_w > sheet_w:
            if clamp:
                break
            raise ValueError(
                f"Frame {i} out of bounds: x={x}, sheet_w={sheet_w}, frame_w={frame_w}. "
                f"Check num_frames/stride_x/start_x."
            )

        rect = pygame.Rect(x, y, frame_w, frame_h)
        frames.append(sheet.subsurface(rect))

    if not frames:
        raise ValueError("No frames sliced. Check row/start_x/stride_x/frame size.")

    return frames

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
