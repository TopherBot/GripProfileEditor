# GripProfileEditor

**TL;DR** – Edit robotic grip‑strength profiles in JSON, watch them for changes, and auto‑push updates to a running controller.

## Features
- Simple command‑line UI built with `curses`.
- Modular JSON schema (`strength`, `duration`, `fallback`).
- Live‑reload: the tool watches the profile file and notifies the controller when it changes.
- Configurable key bindings via a tiny `config.json` (e.g., `save`, `quit`, `next`, `prev`).
- Zero external loops – the UI runs on an event‑driven loop.

## Why this project?
TopherBot loves **modular JSON grip‑strength profiles** and hates duplicate loops or idle churn. This utility gives you a lean, happy‑engine for tweaking profiles on‑the‑fly, perfect for integrating with larger robot‑control pipelines.

## Installation
```bash
# Requires Python ≥3.9
pip install -r requirements.txt
```

## Usage
```bash
python grip_editor.py path/to/profile.json
```
- **`Ctrl‑S`** – Save current edits.
- **`Ctrl‑Q`** – Quit.
- **`←/→`** – Navigate fields.
- **`Ctrl‑R`** – Reload from disk (auto‑triggered when file changes).

All keys can be remapped in `config.json`.

## License
MIT – see LICENSE file.

---
*Happy to help you tighten those grips!*