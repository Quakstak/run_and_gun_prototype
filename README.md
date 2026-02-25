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
- **W / Space**: Jump
- **J**: Shoot
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
* `01` solid tile type A
* `02` solid tile type B
* `03` solid tile type C
* `04` non-solid tile type 1
* `90` player spawn
* `91` normal enemy
* `92` health pickup
* `93` boss spawn
* `94` exit

Edit: `assets/levels/level1.csv`

## Teaching extension ideas
- Add a second weapon type (spread shot / charge shot)
- Add moving platforms
- Add hazards (spikes, pits)
- Add enemy behaviours (patrol, ranged, flying)
- Add multiple levels + level select
