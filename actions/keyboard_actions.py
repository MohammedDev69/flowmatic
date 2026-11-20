# actions/keyboard_actions.py
"""
Keyboard input automation via the `keyboard` library (already a dependency).

Note: typed text and hotkey presses go to whatever window currently has
keyboard focus — pair with Show Window / Open Program blocks first.
"""

import time

from .base_action import BaseAction, ActionResult


class SendKeysAction(BaseAction):
    """Types text or presses a hotkey combination into the focused window."""

    ACTION_TYPE = "send_keys"
    ACTION_LABEL = "Send Keys"
    ACTION_ICON_KEY = "keyboard"
    ACTION_COLOR = "#E67E22"
    ACTION_DESCRIPTION = "Type text or press a hotkey combo (goes to the focused window)."

    MODES = ["type_text", "press_hotkey"]

    def _init_params(self):
        self._params = {
            "mode": "type_text",
            "text": "",
            "hotkey": "",        # e.g. "ctrl+shift+s"
            "interval": 0.02,    # seconds between characters (type mode)
            "repeat": 1,         # how many times to press the hotkey
        }

    def execute(self) -> ActionResult:
        try:
            import keyboard
        except Exception as e:
            return ActionResult(False, f"keyboard library unavailable: {e}")

        mode = self.get_param("mode", "type_text")

        try:
            if mode == "press_hotkey":
                return self._press_hotkey(keyboard)
            return self._type_text(keyboard)
        except Exception as e:
            return ActionResult(False, f"Send keys failed: {e}")

    def _press_hotkey(self, keyboard) -> ActionResult:
        combo = self.interpolate(self.get_param("hotkey", "")).strip()
        if not combo:
            return ActionResult(False, "No hotkey combination specified.")

        try:
            repeat = max(1, min(int(self.get_param("repeat", 1)), 100))
        except (TypeError, ValueError):
            repeat = 1

        for n in range(repeat):
            if self.is_stop_requested():
                return ActionResult(
                    False, f"Stopped after {n} of {repeat} press(es).", cancelled=True
                )
            keyboard.press_and_release(combo)
            if repeat > 1:
                time.sleep(0.05)

        return ActionResult(True, f"Pressed: {combo}" + (f" (x{repeat})" if repeat > 1 else ""))

    def _type_text(self, keyboard) -> ActionResult:
        text = self.interpolate(self.get_param("text", ""))
        if not text:
            return ActionResult(False, "No text specified.")

        try:
            interval = max(0.0, float(self.get_param("interval", 0.02)))
        except (TypeError, ValueError):
            interval = 0.02

        # Type in small chunks so the Stop button stays responsive
        chunk = 20
        typed = 0
        for start in range(0, len(text), chunk):
            if self.is_stop_requested():
                return ActionResult(
                    False,
                    f"Typed {typed}/{len(text)} characters before stop.",
                    cancelled=True,
                )
            keyboard.write(text[start:start + chunk], delay=interval)
            typed += len(text[start:start + chunk])

        preview = text[:30] + ("…" if len(text) > 30 else "")
        return ActionResult(True, f"Typed: {preview}")

    def get_summary(self) -> str:
        if self.get_param("mode") == "press_hotkey":
            combo = self.get_param("hotkey", "")
            return f"Press: {combo}" if combo else "Send Keys (not configured)"
        text = self.get_param("text", "")
        if text:
            preview = text[:20] + ("…" if len(text) > 20 else "")
            return f"Type: {preview}"
        return "Send Keys (not configured)"
