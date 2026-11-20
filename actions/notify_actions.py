# actions/notify_actions.py
"""
Desktop notification action.

The engine routes notifications to the UI thread, where they appear as
system tray balloon messages (see MainWindow._show_tray_notification).
"""

from .base_action import BaseAction, ActionResult


class NotifyAction(BaseAction):
    """Shows a desktop (tray) notification mid-workflow."""

    ACTION_TYPE = "notify"
    ACTION_LABEL = "Notify"
    ACTION_ICON_KEY = "bell"
    ACTION_COLOR = "#F1C40F"
    ACTION_DESCRIPTION = "Show a desktop notification (supports {{variables}})."

    def _init_params(self):
        self._params = {
            "title": "FlowMatic",
            "message": "",
        }

    def execute(self) -> ActionResult:
        title = self.interpolate(self.get_param("title", "")).strip() or "FlowMatic"
        message = self.interpolate(self.get_param("message", "")).strip()
        if not message:
            return ActionResult(False, "No message specified.")

        self.notify(title, message)
        preview = message[:50] + ("…" if len(message) > 50 else "")
        return ActionResult(True, f"Notified: {preview}")

    def get_summary(self) -> str:
        message = self.get_param("message", "")
        if message:
            preview = message[:24] + ("…" if len(message) > 24 else "")
            return f"Notify: {preview}"
        return "Notify (not configured)"
