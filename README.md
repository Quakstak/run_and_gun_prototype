# Run & Gun Side-Scroller Prototype (Pygame-CE)

A small **teaching-friendly** prototype for a first-year *run-and-gun* side-scrolling shooter.

## Features (prototype baseline)
- Start screen + game over screen
- One scrolling tile-based level (CSV)
- Platform collisions, jumping, shooting
- Normal enemies + a boss at the end
- Health pickup
- Basic sprite-sheet animation support (rows/frames)
- Sound effects + looping music (WAV placeholders)

## Controls
- **A/D**: Move
- **W**: Jump
- **Space**: Shoot
- **Enter**: Start / Continue
- **R**: Restart on Game Over
- **Esc**: Quit

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python -m src.main
```

## Level tiles (CSV)
Each cell is one tile (32x32).

Legend:

* `00` empty
* `01` Ground
* `02` Platform
* `03` Platform Left Edge
* `04` Platform Right Edge
* `05` Wall
* `90` player spawn
* `91` runner enemy
* `92` health pickup
* `93` boss spawn
* `94` exit
* `95` shooter enemy

Edit: `assets/levels/level1.csv`

