# Miscellaneous

Mixed personal playground with:
- desktop utility apps (Tk/CustomTkinter),
- Python/Pygame games,
- browser games (Canvas + Three.js),
- Ubuntu and Docker helper scripts.

## Repository Layout

`apps/`
- `bank.py` - loan calculator with amortization table.
- `calc.py` - standard/scientific calculator with memory + history.
- `measurement.py` - unit converter (weight/length/volume).
- `qr_code.py` - QR code generator with logo/text/theme options.

`games/` (Python)
- `alien_invaders.py` - classic wave-based space shooter.
- `alien_invadersV2.py` - extended endless shooter with more systems.
- `asteroids.py` - Asteroids-style arcade game.
- `brickbreaker.py` - Pygame brick breaker with power-ups/particles.
- `game.py` - snake game variant (Pygame).
- `pong_war.py` - Pong/territory hybrid.
- `race.py` - retro-style racer.
- `snake.py` - polished snake implementation.
- `tictactoe.py` - CustomTkinter Tic-Tac-Toe.

`games/` (browser)
- `brick/index.html` + `brick/game.js` - 3D neon brick breaker (Three.js).
- `snake-game/index.html` - modern 2D snake (HTML/CSS/JS).
- `snake/snake-game.html` - 3D snake (Three.js, single-file).
- `neon_breaker/` - multi-file neon brick breaker (HTML/CSS/JS modules).

Root scripts
- `ubuntu-setup.sh` - full Ubuntu post-install automation script.
- `docker-ui.sh` - interactive Docker TUI using `gum` (preferred) or `whiptail`.

## Prerequisites

### Python
- Python 3.10+ recommended.
- `pip install pygame customtkinter qrcode pillow CTkToolTip`

Notes:
- Pygame is needed for most Python games.
- CustomTkinter and related packages are needed for `apps/` and `games/tictactoe.py`.

### Browser games
- Any modern browser.
- `games/brick` and `games/snake/snake-game.html` load Three.js from CDN.

### Shell scripts
- `ubuntu-setup.sh`: Ubuntu/Debian with `sudo`, `apt`, `snap`, `flatpak`, and internet access.
- `docker-ui.sh`: Docker CLI installed and accessible.

## Quick Start

From repository root:

```bash
cd /home/clau/dev/playground/ccc/miscellaneous
```

Run a Python app:

```bash
python3 apps/calc.py
python3 apps/bank.py
python3 apps/measurement.py
python3 apps/qr_code.py
```

Run Python games:

```bash
python3 games/alien_invaders.py
python3 games/alien_invadersV2.py
python3 games/asteroids.py
python3 games/brickbreaker.py
python3 games/game.py
python3 games/pong_war.py
python3 games/race.py
python3 games/snake.py
python3 games/tictactoe.py
```

Run browser games:

```bash
# serve current folder
python3 -m http.server 8000
# then open:
# http://localhost:8000/games/brick/index.html
# http://localhost:8000/games/snake-game/index.html
# http://localhost:8000/games/snake/snake-game.html
# http://localhost:8000/games/neon_breaker/index.html
```

Run scripts:

```bash
bash ubuntu-setup.sh
bash docker-ui.sh
```

Optional:

```bash
bash docker-ui.sh --install-gum
```

## Notes

- `games/race.py` references absolute Windows audio paths for some sounds; those files likely do not exist on Linux unless adjusted.
- `games/neon_breaker/audio/README.md` documents expected audio assets for full sound support.
