# Ember

Ember is a small animated desktop companion for Linux. This first milestone
contains its pixel-art character, deterministic animation model, and a
transparent, frameless PySide6 window.

## Development setup

On Ubuntu, install the venv module if it is missing:

```bash
sudo apt install python3-venv
```

```bash
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Ubuntu, install Qt's platform libraries if the window cannot start:

```bash
sudo apt install libxcb-cursor0 libxkbcommon-x11-0
```

## Run

```bash
ember
```

The overlay draws on a 380 by 250 logical canvas, displayed at 85% scale, and
targets 30 frames per second. It starts near the bottom center of the current
work area.
Left-clicking the character shows a happy expression; holding the right mouse
button previews the listening pose. These are visual previews only: microphone
capture and push-to-talk behavior belong to a later milestone. Desktop
movement, window standing, settings, and tools are also planned for later.

## Test

```bash
pytest
```
