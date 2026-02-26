# settings.py
# Central place for constants so students can safely tweak game feel.

# Window / render
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60

# Logical render size (game draws to this)
SCALE = 4  # 2 means pixels appear 2x bigger on the window
RENDER_WIDTH  = WINDOW_WIDTH  // SCALE
RENDER_HEIGHT = WINDOW_HEIGHT // SCALE

# Tile size (CSV grid uses this)
TILE_SIZE = 16

# Physics tuning
GRAVITY = 1800.0          # pixels per second^2
PLAYER_SPEED = 260.0      # pixels per second
JUMP_SPEED = 620.0        # pixels per second

# Combat
BULLET_SPEED = 560.0 
BULLET_LIFETIME = 1.2     # seconds
PLAYER_MAX_HEALTH = 100
ENEMY_DAMAGE = 10
BOSS_DAMAGE = 15

# Camera
CAMERA_LERP = 0.15        # 0..1 smoothing (higher = snappier)

# Audio
MUSIC_VOLUME = 0.25
SFX_VOLUME = 0.45
SOUND_OFF = True
