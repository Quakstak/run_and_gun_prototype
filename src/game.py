# game.py
# The Game class owns the main loop and high-level states:
# START -> PLAYING -> (GAME_OVER or LEVEL_COMPLETE) -> PLAYING ...

from __future__ import annotations
import pygame

from . import settings
from .level import Level
from .player import Player
from .utils import load_sound, asset_path, clamp

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # --- Window (scaled) + render surface (logical) ---
        self.window = pygame.display.set_mode(
            (settings.WIDTH * settings.SCALE, settings.HEIGHT * settings.SCALE)
        )
        pygame.display.set_caption("Run & Gun Prototype (Pygame-CE)")

        # Draw everything to this surface first (same coords as before)
        self.screen = pygame.Surface((settings.WIDTH, settings.HEIGHT)).convert_alpha()

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.big_font = pygame.font.SysFont("consolas", 44, bold=True)

        # Audio
        self.sfx_shoot = load_sound("shoot.wav")
        self.sfx_pickup = load_sound("pickup.wav")
        self.sfx_hurt = load_sound("hurt.wav")
        self.sfx_shoot.set_volume(settings.SFX_VOLUME)
        self.sfx_pickup.set_volume(settings.SFX_VOLUME)
        self.sfx_hurt.set_volume(settings.SFX_VOLUME)

        music_path = asset_path("audio", "music.wav")
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
        if not settings.SOUND_OFF:
            pygame.mixer.music.play(-1)  # loop

        # Game state
        self.state = "START"  # START, PLAYING, GAME_OVER, LEVEL_COMPLETE
        self.running = True

        # Camera
        self.camera_x = 0.0
        self.camera_y = 0.0

        # World content
        self.level_index = 1
        self.level = None
        self.player = None

        self.bullets = pygame.sprite.Group()
        self.boss_bullets = pygame.sprite.Group()

        self.load_level(self.level_index, f"level{self.level_index}.csv")

    def load_level(self, index: int, level_file: str = "level1.csv") -> None:
        # You can expand this into a list of levels later.
        self.level = Level(level_file)
        self.player = Player(self.level.player_spawn)
        self.bullets.empty()
        self.boss_bullets.empty()

        # Reset camera so the start feels consistent
        self.camera_x = 0.0
        self.camera_y = 0.0

    # ------------------ Main loop ------------------
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            dt = min(dt, 1/30)  # clamp if debugging causes huge dt

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()

    # ------------------ Events ------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if self.state == "START":
                    if event.key == pygame.K_RETURN:
                        self.state = "PLAYING"

                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_r:
                        self.load_level(self.level_index)
                        self.state = "PLAYING"

                elif self.state == "LEVEL_COMPLETE":
                    if event.key == pygame.K_RETURN:
                        self.load_level(self.level_index)
                        self.state = "PLAYING"

                if self.state == "PLAYING":
                    if event.key in (pygame.K_w, pygame.K_SPACE):
                        self.player.queue_jump()

                    if event.key == pygame.K_j:
                        fired = self.player.try_shoot(self.bullets)
                        if fired and not settings.SOUND_OFF:
                            self.sfx_shoot.play()

            if event.type == pygame.KEYUP and self.state == "PLAYING":
                if event.key in (pygame.K_w, pygame.K_SPACE):
                    self.player.cut_jump()

    # ------------------ Update ------------------
    def update(self, dt: float) -> None:
        if self.state != "PLAYING":
            return

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)

        self.player.update(dt, self.level)

        # Update bullets (player and boss)
        for b in list(self.bullets):
            b.update(dt, self.level)

        for b in list(self.boss_bullets):
            b.update(dt, self.level)

        # Update level entities and bullet hits
        self.level.update(dt, self.player, self.bullets, self.boss_bullets)

        # --- Player vs pickups
        hit_pickups = pygame.sprite.spritecollide(self.player, self.level.pickups, dokill=True)
        if hit_pickups:
            for p in hit_pickups:
                p.apply(self.player)
            if not settings.SOUND_OFF:
                self.sfx_pickup.play()

        # --- Player vs enemies contact damage
        if pygame.sprite.spritecollideany(self.player, self.level.enemies):
            self.player.take_damage(settings.ENEMY_DAMAGE)
            if self.player.invuln_time > 0.0 and not settings.SOUND_OFF:
                self.sfx_hurt.play()

        # --- Player vs boss contact damage
        if self.level.boss and self.level.boss.alive() and self.player.rect.colliderect(self.level.boss.rect):
            self.player.take_damage(settings.BOSS_DAMAGE)
            if self.player.invuln_time > 0.0 and not settings.SOUND_OFF:
                self.sfx_hurt.play()

        # --- Player vs boss bullets
        if pygame.sprite.spritecollideany(self.player, self.boss_bullets):
            # remove all bullets that hit
            for b in list(self.boss_bullets):
                if b.rect.colliderect(self.player.rect):
                    b.kill()
            self.player.take_damage(settings.BOSS_DAMAGE)
            if self.player.invuln_time > 0.0 and not settings.SOUND_OFF:
                self.sfx_hurt.play()

        # --- Game over
        if self.player.is_dead():
            self.state = "GAME_OVER"

        # --- Level complete: require boss dead, then touch exit flag
        boss_dead = (self.level.boss is None) or (not self.level.boss.alive())
        if boss_dead and self.level.exit_rect and self.player.rect.colliderect(self.level.exit_rect):
            self.state = "LEVEL_COMPLETE"

        # --- Camera follow (simple smooth lerp)
        target_x = self.player.rect.centerx - settings.WIDTH * 0.5
        target_y = self.player.rect.centery - settings.HEIGHT * 0.6
        target_x = clamp(target_x, 0, max(0, self.level.pixel_width - settings.WIDTH))
        target_y = clamp(target_y, 0, max(0, self.level.pixel_height - settings.HEIGHT))

        self.camera_x += (target_x - self.camera_x) * settings.CAMERA_LERP
        self.camera_y += (target_y - self.camera_y) * settings.CAMERA_LERP

    # ------------------ Draw ------------------
    def draw(self) -> None:
        self.screen.fill((20, 22, 30))

        if self.state == "START":
            self.draw_center_text("RUN & GUN PROTOTYPE", y=170, big=True)
            self.draw_center_text("Press ENTER to start", y=260)
            self.draw_center_text("A/D move, W/Space jump, J shoot", y=310)

            # --- present scaled frame ---
            scaled = pygame.transform.scale(
                self.screen,
                (settings.WIDTH * settings.SCALE, settings.HEIGHT * settings.SCALE)
            )
            self.window.blit(scaled, (0, 0))
            pygame.display.flip()
            return

        # World
        self.level.draw(self.screen, self.camera_x, self.camera_y)

        # Entities
        # (Draw order: pickups -> enemies -> boss -> bullets -> player -> UI)
        for p in self.level.pickups:
            self.screen.blit(p.image, (p.rect.x - self.camera_x, p.rect.y - self.camera_y))

        for e in self.level.enemies:
            self.screen.blit(e.image, (e.rect.x - self.camera_x, e.rect.y - self.camera_y))

        if self.level.boss and self.level.boss.alive():
            self.screen.blit(
                self.level.boss.image,
                (self.level.boss.rect.x - self.camera_x, self.level.boss.rect.y - self.camera_y)
            )

        for b in self.bullets:
            self.screen.blit(b.image, (b.rect.x - self.camera_x, b.rect.y - self.camera_y))

        for b in self.boss_bullets:
            self.screen.blit(b.image, (b.rect.x - self.camera_x, b.rect.y - self.camera_y))

        # Player (blink if invulnerable)
        if self.player.invuln_time <= 0 or int(self.player.invuln_time * 20) % 2 == 0:
            self.screen.blit(
                self.player.image,
                (self.player.rect.x - self.camera_x, self.player.rect.y - self.camera_y)
            )

        # UI overlay
        self.draw_ui()

        if self.state == "GAME_OVER":
            self.draw_overlay()
            self.draw_center_text("GAME OVER", y=220, big=True)
            self.draw_center_text("Press R to restart", y=290)
        elif self.state == "LEVEL_COMPLETE":
            self.draw_overlay()
            self.draw_center_text("LEVEL COMPLETE!", y=220, big=True)
            self.draw_center_text("Press ENTER to replay (add more levels!)", y=290)

        # --- present scaled frame ---
        scaled = pygame.transform.scale(
            self.screen,
            (settings.WIDTH * settings.SCALE, settings.HEIGHT * settings.SCALE)
        )
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()

    def draw_ui(self) -> None:
        # Health bar
        x, y, w, h = 20, 20, 220, 18
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, w, h))
        hp_ratio = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, (80, 220, 120), (x, y, int(w * hp_ratio), h))
        txt = self.font.render(f"HP: {self.player.health}/{self.player.max_health}", True, (230, 230, 230))
        self.screen.blit(txt, (x, y + 22))

        # Boss health (when alive)
        if self.level.boss and self.level.boss.alive(): 
            bx, by, bw, bh = settings.WIDTH - 280, 20, 260, 14
            pygame.draw.rect(self.screen, (50, 50, 50), (bx, by, bw, bh))
            ratio = self.level.boss.health / self.level.boss.max_health
            pygame.draw.rect(self.screen, (220, 90, 160), (bx, by, int(bw * ratio), bh))
            t = self.font.render("BOSS", True, (230, 230, 230))
            self.screen.blit(t, (bx, by + 18))

    def draw_center_text(self, text: str, y: int, big: bool = False) -> None:
        f = self.big_font if big else self.font
        surf = f.render(text, True, (240, 240, 240))
        rect = surf.get_rect(center=(settings.WIDTH//2, y))
        self.screen.blit(surf, rect)

    def draw_overlay(self) -> None:
        overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
