# tools/level_editor.py
#
# Simple CSV + tilesheet level editor for Pygame-CE.
# - Loads a tileset (multiple tiles in a grid)
# - Loads/Saves a CSV where each cell is two-digit tile id (00..99)
# - Lets you paint tiles, erase, and place special marker IDs.
#
# Intended for teaching: readable + hackable.

from __future__ import annotations
import os
import csv
from dataclasses import dataclass
import pygame


# ----------------------------
# CONFIG (match your project)
# ----------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
LEVELS_DIR = os.path.join(ASSETS_DIR, "levels")

TILESET_PATH = os.path.join(IMAGES_DIR, "tileset.png")
LEVEL_PATH = os.path.join(LEVELS_DIR, "level1.csv")

TILE_SIZE = 16  # 16x16 tiles (as requested)

# CSV uses two-digit IDs, but we parse to int in memory.
EMPTY = 0

# Choose which IDs are "solid tiles" / normal paintable tiles.
# You can expand these if you add more tile IDs.
# These IDs are what your *game* interprets.
PAINT_TILE_IDS = list(range(1, 50))  # 01..49 typical "tile" range

# Special marker IDs (not drawn from tileset unless you choose to)
PLAYER_SPAWN = 90
ENEMY_SPAWN = 91
PICKUP_HEALTH = 92
BOSS_SPAWN = 93
EXIT_FLAG = 94


# ----------------------------
# Helper functions
# ----------------------------

def load_csv_level(path: str) -> list[list[int]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        grid = [[int(cell.strip()) for cell in row] for row in reader]
    return grid


def save_csv_level(path: str, grid: list[list[int]]) -> None:
    # Save as two-digit IDs (00..99)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in grid:
            writer.writerow([f"{max(0, min(99, v)):02d}" for v in row])


def slice_tilesheet(sheet: pygame.Surface, tile_size: int) -> list[pygame.Surface]:
    sheet_w, sheet_h = sheet.get_size()
    cols = sheet_w // tile_size
    rows = sheet_h // tile_size
    tiles = []
    for y in range(rows):
        for x in range(cols):
            r = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            tiles.append(sheet.subsurface(r).copy())
    return tiles


def ensure_rect_in_bounds(x: int, y: int, w: int, h: int) -> tuple[int, int]:
    return max(0, min(w - 1, x)), max(0, min(h - 1, y))


@dataclass
class UIState:
    selected_id: int = 1
    show_grid: bool = True
    show_help: bool = True
    show_specials: bool = True
    brush_size: int = 1  # 1..4
    camera_x: int = 0
    camera_y: int = 0


# ----------------------------
# Main editor
# ----------------------------

def main():
    pygame.init()
    pygame.display.set_caption("CSV Level Editor (tilesheet + two-digit IDs)")

    screen = pygame.display.set_mode((1100, 700))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    font_big = pygame.font.SysFont("consolas", 20, bold=True)

    # Load tileset
    if not os.path.exists(TILESET_PATH):
        raise FileNotFoundError(f"Missing tileset: {TILESET_PATH}")

    tileset = pygame.image.load(TILESET_PATH).convert_alpha()
    tiles = slice_tilesheet(tileset, TILE_SIZE)

    # Load level CSV
    if not os.path.exists(LEVEL_PATH):
        raise FileNotFoundError(f"Missing level CSV: {LEVEL_PATH}")

    grid = load_csv_level(LEVEL_PATH)
    grid_h = len(grid)
    grid_w = len(grid[0]) if grid_h else 0

    ui = UIState(selected_id=PAINT_TILE_IDS[0] if PAINT_TILE_IDS else 1)

    # Layout
    palette_w = 320
    canvas_rect = pygame.Rect(0, 0, screen.get_width() - palette_w, screen.get_height())
    palette_rect = pygame.Rect(canvas_rect.right, 0, palette_w, screen.get_height())

    # Palette settings
    thumb = 32  # palette thumbnail size
    pad = 10
    cols = (palette_rect.width - pad * 2) // (thumb + 6)
    if cols < 1:
        cols = 1

    dragging_pan = False
    pan_start = (0, 0)
    cam_start = (0, 0)

    def world_to_grid(mx: int, my: int) -> tuple[int, int]:
        wx = mx + ui.camera_x
        wy = my + ui.camera_y
        gx = wx // TILE_SIZE
        gy = wy // TILE_SIZE
        return int(gx), int(gy)

    def paint_at(gx: int, gy: int, tile_id: int):
        for dy in range(ui.brush_size):
            for dx in range(ui.brush_size):
                x = gx + dx
                y = gy + dy
                if 0 <= x < grid_w and 0 <= y < grid_h:
                    grid[y][x] = tile_id

    def draw_canvas():
        # background
        screen.fill((18, 18, 22), canvas_rect)

        # visible tile range (simple culling)
        start_gx = max(0, ui.camera_x // TILE_SIZE)
        start_gy = max(0, ui.camera_y // TILE_SIZE)
        end_gx = min(grid_w, (ui.camera_x + canvas_rect.width) // TILE_SIZE + 2)
        end_gy = min(grid_h, (ui.camera_y + canvas_rect.height) // TILE_SIZE + 2)

        # draw tiles
        for gy in range(start_gy, end_gy):
            for gx in range(start_gx, end_gx):
                tile_id = grid[gy][gx]

                sx = gx * TILE_SIZE - ui.camera_x
                sy = gy * TILE_SIZE - ui.camera_y

                # draw normal tiles from tileset if mapped
                if tile_id in PAINT_TILE_IDS:
                    # Simple mapping: tile_id 01 -> tiles[0], 02 -> tiles[1], ...
                    idx = tile_id - 1
                    if 0 <= idx < len(tiles):
                        screen.blit(tiles[idx], (sx, sy))
                    else:
                        # unknown tile id => draw magenta box
                        pygame.draw.rect(screen, (255, 0, 255), (sx, sy, TILE_SIZE, TILE_SIZE), 1)

                # specials drawn as overlay markers
                if ui.show_specials:
                    if tile_id == PLAYER_SPAWN:
                        pygame.draw.rect(screen, (80, 200, 255), (sx, sy, TILE_SIZE, TILE_SIZE), 2)
                        screen.blit(font.render("P", True, (80, 200, 255)), (sx + 3, sy + 1))
                    elif tile_id == ENEMY_SPAWN:
                        pygame.draw.rect(screen, (255, 120, 120), (sx, sy, TILE_SIZE, TILE_SIZE), 2)
                        screen.blit(font.render("E", True, (255, 120, 120)), (sx + 3, sy + 1))
                    elif tile_id == PICKUP_HEALTH:
                        pygame.draw.rect(screen, (90, 235, 130), (sx, sy, TILE_SIZE, TILE_SIZE), 2)
                        screen.blit(font.render("+", True, (90, 235, 130)), (sx + 4, sy + 1))
                    elif tile_id == BOSS_SPAWN:
                        pygame.draw.rect(screen, (180, 90, 255), (sx, sy, TILE_SIZE, TILE_SIZE), 2)
                        screen.blit(font.render("B", True, (180, 90, 255)), (sx + 3, sy + 1))
                    elif tile_id == EXIT_FLAG:
                        pygame.draw.rect(screen, (80, 240, 180), (sx, sy, TILE_SIZE, TILE_SIZE), 2)
                        screen.blit(font.render("X", True, (80, 240, 180)), (sx + 3, sy + 1))

        # grid overlay
        if ui.show_grid:
            grid_col = (45, 45, 55)
            for gx in range(start_gx, end_gx):
                x = gx * TILE_SIZE - ui.camera_x
                pygame.draw.line(screen, grid_col, (x, 0), (x, canvas_rect.height))
            for gy in range(start_gy, end_gy):
                y = gy * TILE_SIZE - ui.camera_y
                pygame.draw.line(screen, grid_col, (0, y), (canvas_rect.width, y))

        # border
        pygame.draw.rect(screen, (70, 70, 90), canvas_rect, 2)

        # status line
        mx, my = pygame.mouse.get_pos()
        if canvas_rect.collidepoint(mx, my):
            gx, gy = world_to_grid(mx, my)
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                tid = grid[gy][gx]
                status = f"Mouse: ({gx},{gy})  Cell:{tid:02d}  Selected:{ui.selected_id:02d}  Brush:{ui.brush_size}  Cam:({ui.camera_x},{ui.camera_y})"
            else:
                status = f"Mouse: ({gx},{gy})  Selected:{ui.selected_id:02d}"
        else:
            status = f"Selected:{ui.selected_id:02d}  Brush:{ui.brush_size}  Cam:({ui.camera_x},{ui.camera_y})"

        s = font.render(status, True, (230, 230, 230))
        screen.blit(s, (10, canvas_rect.height - 22))

        if ui.show_help:
            help_lines = [
                "LMB: paint   RMB: erase (00)   MMB drag: pan",
                "[ / ]: brush size   G: grid   H: help   S: specials overlay",
                "Ctrl+S: save   R: reload from disk",
                "1..5: select special marker (Player/Enemy/Pickup/Boss/Exit)",
                "ESC: quit",
            ]
            y = 10
            for line in help_lines:
                t = font.render(line, True, (210, 210, 210))
                screen.blit(t, (10, y))
                y += 18

    def draw_palette():
        screen.fill((24, 24, 30), palette_rect)
        pygame.draw.rect(screen, (70, 70, 90), palette_rect, 2)

        title = font_big.render("Palette (Tiles + Specials)", True, (240, 240, 240))
        screen.blit(title, (palette_rect.x + 10, 10))

        # Normal tile palette (01..)
        y0 = 44
        screen.blit(font.render("Tiles (click to select):", True, (200, 200, 200)), (palette_rect.x + 10, y0))
        y0 += 22

        for i, tile_id in enumerate(PAINT_TILE_IDS):
            row = i // cols
            col = i % cols
            x = palette_rect.x + pad + col * (thumb + 6)
            y = y0 + row * (thumb + 6)

            r = pygame.Rect(x, y, thumb, thumb)

            idx = tile_id - 1
            if 0 <= idx < len(tiles):
                img = pygame.transform.scale(tiles[idx], (thumb, thumb))
                screen.blit(img, r.topleft)
            else:
                pygame.draw.rect(screen, (255, 0, 255), r, 2)

            if tile_id == ui.selected_id:
                pygame.draw.rect(screen, (255, 255, 255), r, 3)
            else:
                pygame.draw.rect(screen, (60, 60, 75), r, 1)

            id_txt = font.render(f"{tile_id:02d}", True, (230, 230, 230))
            screen.blit(id_txt, (x + 3, y + 3))

        # Specials
        y_special = palette_rect.bottom - 170
        pygame.draw.line(screen, (60, 60, 75), (palette_rect.x + 10, y_special), (palette_rect.right - 10, y_special), 1)
        y_special += 10

        screen.blit(font.render("Special markers (keys 1..5):", True, (200, 200, 200)), (palette_rect.x + 10, y_special))
        y_special += 20

        specials = [
            (PLAYER_SPAWN, "1 Player spawn (90)", (80, 200, 255)),
            (ENEMY_SPAWN, "2 Enemy spawn (91)", (255, 120, 120)),
            (PICKUP_HEALTH, "3 Health pickup (92)", (90, 235, 130)),
            (BOSS_SPAWN, "4 Boss spawn (93)", (180, 90, 255)),
            (EXIT_FLAG, "5 Exit flag (94)", (80, 240, 180)),
        ]
        yy = y_special
        for tid, label, col in specials:
            box = pygame.Rect(palette_rect.x + 10, yy, 18, 18)
            pygame.draw.rect(screen, col, box, 2)
            if ui.selected_id == tid:
                pygame.draw.rect(screen, (255, 255, 255), box.inflate(6, 6), 2)
            screen.blit(font.render(label, True, (220, 220, 220)), (palette_rect.x + 38, yy + 1))
            yy += 24

        # Save hint
        screen.blit(font.render(f"Loaded: {os.path.basename(LEVEL_PATH)}", True, (180, 180, 200)),
                    (palette_rect.x + 10, palette_rect.bottom - 26))

    def palette_hit(mx: int, my: int) -> int | None:
        if not palette_rect.collidepoint(mx, my):
            return None

        # check tile thumbnails
        y0 = 44 + 22
        for i, tile_id in enumerate(PAINT_TILE_IDS):
            row = i // cols
            col = i % cols
            x = palette_rect.x + pad + col * (thumb + 6)
            y = y0 + row * (thumb + 6)
            r = pygame.Rect(x, y, thumb, thumb)
            if r.collidepoint(mx, my):
                return tile_id

        # specials: click boxes too (rough area)
        specials_area = pygame.Rect(palette_rect.x + 10, palette_rect.bottom - 150, palette_rect.width - 20, 130)
        if specials_area.collidepoint(mx, my):
            # detect which line
            rel_y = my - (palette_rect.bottom - 150)
            idx = rel_y // 24
            if idx == 0:
                return PLAYER_SPAWN
            if idx == 1:
                return ENEMY_SPAWN
            if idx == 2:
                return PICKUP_HEALTH
            if idx == 3:
                return BOSS_SPAWN
            if idx == 4:
                return EXIT_FLAG

        return None

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                if event.key == pygame.K_ESCAPE:
                    running = False

                # save / reload
                if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    save_csv_level(LEVEL_PATH, grid)
                    pygame.display.set_caption("Saved ✓  " + os.path.basename(LEVEL_PATH))

                if event.key == pygame.K_r:
                    grid = load_csv_level(LEVEL_PATH)
                    pygame.display.set_caption("Reloaded  " + os.path.basename(LEVEL_PATH))

                # toggles
                if event.key == pygame.K_g:
                    ui.show_grid = not ui.show_grid
                if event.key == pygame.K_h:
                    ui.show_help = not ui.show_help
                if event.key == pygame.K_s and not (mods & pygame.KMOD_CTRL):
                    ui.show_specials = not ui.show_specials

                # brush size
                if event.key == pygame.K_LEFTBRACKET:
                    ui.brush_size = max(1, ui.brush_size - 1)
                if event.key == pygame.K_RIGHTBRACKET:
                    ui.brush_size = min(4, ui.brush_size + 1)

                # quick special selection 1..5
                if event.key == pygame.K_1:
                    ui.selected_id = PLAYER_SPAWN
                if event.key == pygame.K_2:
                    ui.selected_id = ENEMY_SPAWN
                if event.key == pygame.K_3:
                    ui.selected_id = PICKUP_HEALTH
                if event.key == pygame.K_4:
                    ui.selected_id = BOSS_SPAWN
                if event.key == pygame.K_5:
                    ui.selected_id = EXIT_FLAG

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # click palette to select
                sel = palette_hit(mx, my)
                if sel is not None:
                    ui.selected_id = sel

                # middle mouse drag pans
                if event.button == 2 and canvas_rect.collidepoint(mx, my):
                    dragging_pan = True
                    pan_start = (mx, my)
                    cam_start = (ui.camera_x, ui.camera_y)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    dragging_pan = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_pan:
                    mx, my = event.pos
                    dx = mx - pan_start[0]
                    dy = my - pan_start[1]
                    ui.camera_x = max(0, min(grid_w * TILE_SIZE - canvas_rect.width, cam_start[0] - dx))
                    ui.camera_y = max(0, min(grid_h * TILE_SIZE - canvas_rect.height, cam_start[1] - dy))

        # paint/erase while holding mouse
        mx, my = pygame.mouse.get_pos()
        buttons = pygame.mouse.get_pressed(3)

        if canvas_rect.collidepoint(mx, my) and not dragging_pan:
            gx, gy = world_to_grid(mx, my)
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                if buttons[0]:  # LMB paint
                    paint_at(gx, gy, ui.selected_id)
                if buttons[2]:  # RMB erase
                    paint_at(gx, gy, EMPTY)

        draw_canvas()
        draw_palette()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()