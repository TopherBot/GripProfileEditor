#!/usr/bin/env python3
"""GripProfileEditor – tiny CLI for JSON grip‑strength profiles.

Features:
- Load a profile JSON file.
- Edit fields via a curses UI.
- Live‑reload when the file changes on disk.
- Configurable key mappings (see config.json).
"""

import json
import os
import sys
import threading
from pathlib import Path

# ----- Optional imports for Windows -----
try:
    import curses
except ImportError:
    # On Windows, curses is provided by `windows-curses`
    import curses

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def load_config(path="config.json"):
    """Load key mappings, falling back to defaults if missing."""
    default = {
        "keys": {
            "save": "ctrl+s",
            "quit": "ctrl+q",
            "next": "right",
            "prev": "left",
            "reload": "ctrl+r",
        }
    }
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def parse_key(key_str):
    """Translate a config string to a curses key constant.
    Supports a tiny subset needed for the UI.
    """
    mapping = {
        "ctrl+s": 19,  # ASCII SUB
        "ctrl+q": 17,
        "ctrl+r": 18,
        "left": curses.KEY_LEFT,
        "right": curses.KEY_RIGHT,
        "up": curses.KEY_UP,
        "down": curses.KEY_DOWN,
    }
    return mapping.get(key_str.lower(), -1)

# --------------------------------------------------
# File watcher for live‑reload
# --------------------------------------------------
class ReloadHandler(FileSystemEventHandler):
    def __init__(self, target_path, callback):
        self.target_path = Path(target_path).resolve()
        self.callback = callback

    def on_modified(self, event):
        if Path(event.src_path).resolve() == self.target_path:
            self.callback()

# --------------------------------------------------
# Main UI class
# --------------------------------------------------
class GripEditor:
    def __init__(self, stdscr, profile_path):
        self.stdscr = stdscr
        self.profile_path = Path(profile_path).resolve()
        self.config = load_config()
        self.keys = {name: parse_key(k) for name, k in self.config["keys"].items()}
        self.profile = {}
        self.fields = []  # ordered list of (key, value)
        self.idx = 0  # currently selected field
        self.message = ""
        self.load_profile()
        self.start_watcher()

    # --------------------------------------------------
    def load_profile(self):
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                self.profile = json.load(f)
            self.fields = list(self.profile.items())
            self.message = "Profile loaded."
        except Exception as e:
            self.profile = {}
            self.fields = []
            self.message = f"Error loading profile: {e}"

    def save_profile(self):
        try:
            # Re‑assemble dict preserving order
            ordered = {k: v for k, v in self.fields}
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(ordered, f, indent=2)
            self.message = "Profile saved."
        except Exception as e:
            self.message = f"Save failed: {e}"

    # --------------------------------------------------
    def start_watcher(self):
        handler = ReloadHandler(self.profile_path, self.on_external_change)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.profile_path.parent), recursive=False)
        self.observer.start()

    def on_external_change(self):
        # Called from watchdog thread – schedule UI update via flag
        self.message = "File changed externally – reloaded."
        self.load_profile()
        self.refresh()

    # --------------------------------------------------
    def refresh(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        # Title
        title = f"GripProfileEditor – {self.profile_path.name}"
        self.stdscr.addstr(0, 0, title[:w-1], curses.A_BOLD)
        # Fields
        for i, (k, v) in enumerate(self.fields):
            prefix = "> " if i == self.idx else "  "
            line = f"{prefix}{k}: {v}"
            self.stdscr.addstr(i+2, 0, line[:w-1], curses.A_REVERSE if i == self.idx else curses.A_NORMAL)
        # Footer message
        self.stdscr.addstr(h-2, 0, self.message[:w-1], curses.A_DIM)
        self.stdscr.refresh()

    # --------------------------------------------------
    def edit_current(self):
        k, v = self.fields[self.idx]
        curses.echo()
        self.stdscr.addstr(self.idx+2, 0, f"  {k}: ")
        new_val = self.stdscr.getstr(self.idx+2, len(k)+4).decode("utf-8")
        curses.noecho()
        # Attempt type conversion – keep original type if possible
        try:
            if isinstance(v, int):
                new_val = int(new_val)
            elif isinstance(v, float):
                new_val = float(new_val)
        except ValueError:
            pass  # keep as string
        self.fields[self.idx] = (k, new_val)
        self.message = f"{k} updated."

    # --------------------------------------------------
    def run(self):
        while True:
            self.refresh()
            ch = self.stdscr.getch()
            if ch == self.keys["quit"]:
                break
            elif ch == self.keys["save"]:
                self.save_profile()
            elif ch == self.keys["reload"]:
                self.load_profile()
                self.message = "Manually reloaded."
            elif ch == self.keys["next"]:
                self.idx = (self.idx + 1) % len(self.fields) if self.fields else 0
            elif ch == self.keys["prev"]:
                self.idx = (self.idx - 1) % len(self.fields) if self.fields else 0
            elif ch == ord('\n') or ch == curses.KEY_ENTER:
                self.edit_current()
            # ignore other keys – no duplicate loops!
        self.observer.stop()
        self.observer.join()

# --------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python grip_editor.py <profile.json>")
        sys.exit(1)
    profile_path = sys.argv[1]
    curses.wrapper(lambda stdscr: GripEditor(stdscr, profile_path).run())

if __name__ == "__main__":
    main()
