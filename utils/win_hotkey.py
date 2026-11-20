# utils/win_hotkey.py
"""
Windows RegisterHotKey backend — works in fullscreen games better than keyboard hooks.

Games like C&C Generals capture raw input; low-level hooks (keyboard library) often fail.
RegisterHotKey registers shortcuts with the OS, which still delivers WM_HOTKEY in many cases.
"""

from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes
from typing import Callable, Dict, Optional, Tuple

from utils.hotkey_format import normalize_hotkey

WM_HOTKEY = 0x0312

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

ERROR_HOTKEY_ALREADY_REGISTERED = 1409

_MODIFIERS = {
    "ctrl": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "alt": MOD_ALT,
    "windows": MOD_WIN,
}

# Virtual-key codes (common keys)
_VK = {
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "space": 0x20, "tab": 0x09, "enter": 0x0D, "esc": 0x1B,
    "escape": 0x1B, "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "left": 0x25, "right": 0x27, "up": 0x26, "down": 0x28,
    "plus": 0xBB, "comma": 0xBC, "minus": 0xBD, "period": 0xBE,
}
for i in range(10):
    _VK[str(i)] = 0x30 + i
for c in "abcdefghijklmnopqrstuvwxyz":
    _VK[c] = ord(c.upper())


def is_windows_admin() -> bool:
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def hotkey_to_win32(hotkey: str) -> Tuple[int, int]:
    """
    Parse normalized hotkey into (modifiers, virtual_key).
    Raises ValueError if invalid.
    """
    normalized = normalize_hotkey(hotkey)
    if not normalized:
        raise ValueError("empty hotkey")

    parts = normalized.split("+")
    mods = MOD_NOREPEAT
    key_part: Optional[str] = None

    for part in parts:
        if part in _MODIFIERS:
            mods |= _MODIFIERS[part]
        else:
            key_part = part

    if not key_part:
        raise ValueError("missing key (use e.g. ctrl+shift+f9)")
    if mods == MOD_NOREPEAT:
        raise ValueError("at least one modifier required (ctrl, shift, alt)")

    vk = _VK.get(key_part)
    if vk is None:
        raise ValueError(f"unsupported key: {key_part}")

    return mods, vk


class WinHotkeyBackend:
    """RegisterHotKey / UnregisterHotKey on the Qt main thread."""

    _id_min = 0xA000
    _id_max = 0xBFFF

    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._next_id = self._id_min
        # hotkey_id -> (normalized_name, callback)
        self._by_id: Dict[int, Tuple[str, Callable]] = {}
        # normalized_name -> hotkey_id
        self._by_name: Dict[str, int] = {}
        self._last_error = ""

    def register(self, hotkey: str, callback: Callable) -> bool:
        normalized = normalize_hotkey(hotkey)
        if not normalized:
            return False

        self.unregister(normalized)

        try:
            mods, vk = hotkey_to_win32(normalized)
        except ValueError as exc:
            self._last_error = str(exc)
            return False

        hotkey_id = self._alloc_id()
        # NULL hwnd → WM_HOTKEY posted to this thread (Qt main loop)
        ok = self._user32.RegisterHotKey(None, hotkey_id, mods, vk)
        if not ok:
            err = ctypes.get_last_error()
            self._last_error = self._format_error(err, normalized)
            return False

        self._by_id[hotkey_id] = (normalized, callback)
        self._by_name[normalized] = hotkey_id
        self._last_error = ""
        return True

    def unregister(self, hotkey: str) -> bool:
        normalized = normalize_hotkey(hotkey)
        hotkey_id = self._by_name.pop(normalized, None)
        if hotkey_id is None:
            return False
        self._by_id.pop(hotkey_id, None)
        self._user32.UnregisterHotKey(None, hotkey_id)
        return True

    def unregister_all(self):
        for hotkey_id in list(self._by_id.keys()):
            self._user32.UnregisterHotKey(None, hotkey_id)
        self._by_id.clear()
        self._by_name.clear()

    def dispatch(self, hotkey_id: int):
        entry = self._by_id.get(int(hotkey_id))
        if entry:
            entry[1]()

    def list_bindings(self):
        return list(self._by_name.keys())

    def get_last_error(self) -> str:
        return self._last_error

    def _alloc_id(self) -> int:
        for _ in range(self._id_max - self._id_min):
            hid = self._next_id
            self._next_id += 1
            if self._next_id > self._id_max:
                self._next_id = self._id_min
            if hid not in self._by_id:
                return hid
        raise RuntimeError("no free hotkey ids")

    @staticmethod
    def _format_error(code: int, hotkey: str) -> str:
        if code == ERROR_HOTKEY_ALREADY_REGISTERED:
            return (
                f"'{hotkey}' is already used by Windows or another program. "
                "Choose a different combination."
            )
        return f"RegisterHotKey failed (error {code}) for '{hotkey}'"


def create_native_filter(backend: WinHotkeyBackend):
    """Build a QAbstractNativeEventFilter subclass instance."""
    from PySide6.QtCore import QAbstractNativeEventFilter

    class _Filter(QAbstractNativeEventFilter):
        def __init__(self):
            super().__init__()
            self._backend = backend

        def nativeEventFilter(self, eventType, message):
            if sys.platform != "win32" or eventType != b"windows_generic_MSG":
                return False
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY:
                    self._backend.dispatch(int(msg.wParam))
            except Exception:
                pass
            return False

    return _Filter()
