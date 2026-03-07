# Miscellaneous

A mixed playground of desktop apps, Python arcade games, browser games, and utility scripts.

## Quick Start

```bash
cd /home/clau/dev/playground/ccc/miscellaneous
pip install pygame customtkinter qrcode pillow CTkToolTip
python3 apps/calc.py
python3 games/snake.py
python3 -m http.server 8000
```

Open browser games at:
- `http://localhost:8000/games/brick/index.html`
- `http://localhost:8000/games/snake-game/index.html`
- `http://localhost:8000/games/snake/snake-game.html`
- `http://localhost:8000/games/neon_breaker/index.html`

## Projects

| Project | Type | Run |
|---|---|---|
| `apps/bank.py` | Python app (CustomTkinter) | `python3 apps/bank.py` |
| `apps/calc.py` | Python app (CustomTkinter) | `python3 apps/calc.py` |
| `apps/measurement.py` | Python app (CustomTkinter) | `python3 apps/measurement.py` |
| `apps/qr_code.py` | Python app (CustomTkinter) | `python3 apps/qr_code.py` |
| `games/alien_invaders.py` | Python game (Pygame) | `python3 games/alien_invaders.py` |
| `games/alien_invadersV2.py` | Python game (Pygame) | `python3 games/alien_invadersV2.py` |
| `games/asteroids.py` | Python game (Pygame) | `python3 games/asteroids.py` |
| `games/brickbreaker.py` | Python game (Pygame) | `python3 games/brickbreaker.py` |
| `games/game.py` | Python game (Pygame Snake variant) | `python3 games/game.py` |
| `games/pong_war.py` | Python game (Pygame) | `python3 games/pong_war.py` |
| `games/race.py` | Python game (Pygame) | `python3 games/race.py` |
| `games/snake.py` | Python game (Pygame) | `python3 games/snake.py` |
| `games/tictactoe.py` | Python game (CustomTkinter) | `python3 games/tictactoe.py` |
| `games/brick/` | Browser game (Three.js) | `python3 -m http.server 8000` then open `/games/brick/index.html` |
| `games/snake-game/` | Browser game (Canvas JS) | `python3 -m http.server 8000` then open `/games/snake-game/index.html` |
| `games/snake/snake-game.html` | Browser game (Three.js) | `python3 -m http.server 8000` then open `/games/snake/snake-game.html` |
| `games/neon_breaker/` | Browser game (modular JS) | `python3 -m http.server 8000` then open `/games/neon_breaker/index.html` |

## Scripts

| Script | Purpose | Run |
|---|---|---|
| `scripts/setup/ubuntu-setup.sh` | Ubuntu post-install automation (APT/Snap/Flatpak/apps/conda) | `bash scripts/setup/ubuntu-setup.sh` |
| `scripts/docker/docker-ui.sh` | Interactive Docker manager (`gum`/`whiptail`) | `bash scripts/docker/docker-ui.sh` |

Optional:

```bash
bash scripts/docker/docker-ui.sh --install-gum
```

## Requirements

- Python 3.10+
- Python deps: `pygame`, `customtkinter`, `qrcode`, `pillow`, `CTkToolTip`
- Docker installed for `scripts/docker/docker-ui.sh`
- Ubuntu/Debian tooling for `scripts/setup/ubuntu-setup.sh`
- Modern browser for web games

## Known Issues

- `games/race.py` references absolute Windows audio paths; adjust for Linux/macOS if needed.
- `games/neon_breaker/audio/README.md` lists optional audio files required for full sound effects/music.
