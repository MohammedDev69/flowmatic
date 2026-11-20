# utils/hotkey_manager.py
"""
HotkeyManager: Global workflow shortcuts.

Windows: RegisterHotKey (works in many fullscreen games).
Other OS: keyboard library low-level hooks.
"""

import sys
from typing import Callable, List, Any, Optional

from utils.hotkey_format import normalize_hotkey


class HotkeyManager:
    """
    Manages global hotkey registrations.

    Windows uses Win32 RegisterHotKey (recommended for games).
    Linux often needs root for the keyboard library.
    """

    def __init__(self):
        self._handlers: dict[str, Any] = {}
        self._last_error = ""
        self._backend = "none"
        self._win_backend: Optional[Any] = None
        self._native_filter: Optional[Any] = None
        self._keyboard_available = False

        if sys.platform == "win32":
            from utils.win_hotkey import WinHotkeyBackend
            self._win_backend = WinHotkeyBackend()
            self._backend = "win32"
        else:
            self._try_import_keyboard()

    def _try_import_keyboard(self):
        try:
            import keyboard  # noqa: F401
            self._keyboard_available = True
            self._backend = "keyboard"
            self._last_error = ""
        except Exception as exc:
            self._keyboard_available = False
            self._backend = "none"
            self._last_error = str(exc)

    def install_on_app(self, app) -> bool:
        """Install native event filter (Windows). Call once after QApplication exists."""
        if sys.platform != "win32" or not self._win_backend:
            return False
        from utils.win_hotkey import create_native_filter
        self._native_filter = create_native_filter(self._win_backend)
        app.installNativeEventFilter(self._native_filter)
        return True

    def register(self, hotkey: str, callback: Callable) -> bool:
        normalized = normalize_hotkey(hotkey)
        if not normalized:
            return False

        if self._backend == "win32" and self._win_backend:
            return self._win_backend.register(hotkey, callback)

        if not self._keyboard_available:
            return False

        try:
            import keyboard
            self.unregister(normalized)
            handler = keyboard.add_hotkey(normalized, callback, suppress=False)
            self._handlers[normalized] = handler
            self._last_error = ""
            return True
        except Exception as exc:
            self._last_error = str(exc)
            print(f"[HotkeyManager] Failed to register '{normalized}': {exc}")
            return False

    def unregister(self, hotkey: str) -> bool:
        normalized = normalize_hotkey(hotkey)
        if not normalized:
            return False

        if self._backend == "win32" and self._win_backend:
            return self._win_backend.unregister(hotkey)

        if normalized not in self._handlers:
            return False
        try:
            import keyboard
            handler = self._handlers.pop(normalized)
            keyboard.remove_hotkey(handler)
            return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    def register_many(self, hotkeys: List[str], callback: Callable) -> List[str]:
        registered = []
        for hotkey in hotkeys:
            if self.register(hotkey, callback):
                registered.append(normalize_hotkey(hotkey))
        return registered

    def unregister_many(self, hotkeys: List[str]):
        for hotkey in hotkeys:
            self.unregister(hotkey)

    def unregister_all(self):
        if self._backend == "win32" and self._win_backend:
            self._win_backend.unregister_all()
        else:
            for hotkey in list(self._handlers.keys()):
                self.unregister(hotkey)

    def is_available(self) -> bool:
        return self._backend in ("win32", "keyboard")

    def get_backend(self) -> str:
        return self._backend

    def get_last_error(self) -> str:
        if self._backend == "win32" and self._win_backend:
            return self._win_backend.get_last_error() or self._last_error
        return self._last_error

    def list_bindings(self) -> List[str]:
        if self._backend == "win32" and self._win_backend:
            return self._win_backend.list_bindings()
        return list(self._handlers.keys())

    def get_game_hotkey_hint(self) -> str:
        if sys.platform != "win32":
            return "On Linux, run FlowMatic with sudo for global hotkeys in games."
        from utils.win_hotkey import is_windows_admin
        lines = [
            "FlowMatic uses Windows RegisterHotKey (works in most games, including Generals).",
            "Use Ctrl+Shift+F9 style shortcuts (not a single key alone).",
        ]
        if not is_windows_admin():
            lines.append(
                "If the game runs as Administrator, start FlowMatic as Administrator too "
                "(right-click main.py → Run as administrator)."
            )
        else:
            lines.append("FlowMatic is running as Administrator — OK for admin games.")
        lines.append(
            "If a shortcut still fails in exclusive fullscreen, switch the game to "
            "borderless windowed mode."
        )
        return "\n".join(lines)
