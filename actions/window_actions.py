# actions/window_actions.py
"""
Actions for controlling application window visibility.
Uses pygetwindow + Win32 APIs (via utils.window_helper) for reliable control.
"""

from .base_action import BaseAction, ActionResult
from utils.window_helper import show_windows_by_title, hide_windows_by_title


class ShowWindowAction(BaseAction):
    """Restores or brings a window to the foreground."""

    ACTION_TYPE = "show_window"
    ACTION_LABEL = "Show Window"
    ACTION_ICON_KEY = "eye"
    ACTION_COLOR = "#3498DB"
    ACTION_DESCRIPTION = "Restore and bring a window to the foreground by its title."

    def _init_params(self):
        self._params = {
            "window_title": "",   # Partial or full window title
            "maximize": False,    # Whether to maximize the window
        }

    def execute(self) -> ActionResult:
        title = self.interpolate(self.get_param("window_title", "")).strip()
        maximize = self.get_param("maximize", False)

        if not title:
            return ActionResult(False, "No window title specified.")

        ok, message, data = show_windows_by_title(title, maximize=maximize)
        return ActionResult(ok, message, data)

    def get_summary(self) -> str:
        title = self.get_param("window_title", "")
        if title:
            return f"Show: {title}"
        return "Show Window (not configured)"


class HideWindowAction(BaseAction):
    """Minimizes a window to the taskbar."""

    ACTION_TYPE = "hide_window"
    ACTION_LABEL = "Hide Window"
    ACTION_ICON_KEY = "window_hide"
    ACTION_COLOR = "#9B59B6"
    ACTION_DESCRIPTION = "Minimize a window to the taskbar by its title."

    def _init_params(self):
        self._params = {
            "window_title": "",   # Partial or full window title
        }

    def execute(self) -> ActionResult:
        title = self.interpolate(self.get_param("window_title", "")).strip()

        if not title:
            return ActionResult(False, "No window title specified.")

        ok, message, data = hide_windows_by_title(title)
        return ActionResult(ok, message, data)

    def get_summary(self) -> str:
        title = self.get_param("window_title", "")
        if title:
            return f"Hide: {title}"
        return "Hide Window (not configured)"
