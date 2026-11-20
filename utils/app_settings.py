# utils/app_settings.py
"""
Persistent application settings (tray, notifications, etc.).
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from typing import Any, Dict


DEFAULTS: Dict[str, Any] = {
    "minimize_to_tray_on_close": True,
    "minimize_to_tray_on_minimize": True,
    "start_in_tray": False,
    "show_tray_notifications": True,
    "show_tray_icon": True,
    "reopen_last_file": True,
    "last_file": "",
}


def settings_file_path() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        folder = os.path.join(base, "FlowMatic")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".flowmatic")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


class AppSettings:
    """Load/save user preferences."""

    def __init__(self):
        self._data = deepcopy(DEFAULTS)
        self.load()

    def load(self) -> bool:
        path = settings_file_path()
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for key, default in DEFAULTS.items():
                    if key in raw:
                        self._data[key] = raw[key]
            return True
        except Exception:
            return False

    def save(self) -> bool:
        try:
            with open(settings_file_path(), "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            return True
        except Exception:
            return False

    def get(self, key: str) -> Any:
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key: str, value: Any):
        if key in DEFAULTS:
            self._data[key] = value

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def apply_dict(self, data: Dict[str, Any]):
        """Apply a dict of settings. Bool defaults are cast to bool; others kept as-is."""
        for key, default in DEFAULTS.items():
            if key in data:
                self._data[key] = bool(data[key]) if isinstance(default, bool) else data[key]
