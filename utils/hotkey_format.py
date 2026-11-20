# utils/hotkey_format.py
"""
Convert Qt-recorded shortcuts to the format expected by the `keyboard` library.
"""

from __future__ import annotations

from typing import List


# Qt / QKeySequence name -> keyboard library name
_KEY_ALIASES = {
    "return": "enter",
    "esc": "esc",
    "escape": "esc",
    "del": "delete",
    "ins": "insert",
    "pgup": "page up",
    "pgdown": "page down",
    "pageup": "page up",
    "pagedown": "page down",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
    "meta": "windows",
    "win": "windows",
    "super": "windows",
    "control": "ctrl",
    "ctl": "ctrl",
    "+": "plus",
    ",": "comma",
    " ": "space",
}


def normalize_hotkey(hotkey: str) -> str:
    """Normalize a hotkey string for keyboard.add_hotkey."""
    if not hotkey or not str(hotkey).strip():
        return ""

    raw = str(hotkey).strip().lower()
    parts = [p.strip() for p in raw.replace(" ", "").split("+") if p.strip()]

    normalized: List[str] = []
    for part in parts:
        part = _KEY_ALIASES.get(part, part)
        if part and part not in normalized:
            normalized.append(part)

    return "+".join(normalized)


def format_hotkeys_display(hotkeys: List[str]) -> str:
    """Human-readable summary for UI labels."""
    cleaned = [h.strip() for h in hotkeys if h and h.strip()]
    if not cleaned:
        return "No hotkey"
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]}  |  {cleaned[1]}"
    return f"{cleaned[0]}  |  {cleaned[1]}  (+{len(cleaned) - 2})"


def parse_hotkeys_field(text: str) -> List[str]:
    """Parse comma- or newline-separated hotkeys from legacy single-field input."""
    if not text:
        return []
    items = []
    for chunk in text.replace("\n", ",").split(","):
        hk = normalize_hotkey(chunk)
        if hk and hk not in items:
            items.append(hk)
    return items
