# actions/base_action.py
"""
Base class for all workflow actions.
Every action must inherit from BaseAction and implement execute().
"""

from abc import ABC, abstractmethod
import re
from typing import Any, Dict, Optional
import uuid

# {{var_name}} tokens — double braces so JSON bodies with single braces are safe
_VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class ActionResult:
    """Represents the result of executing an action."""

    def __init__(self, success: bool, message: str = "", data: Any = None,
                 cancelled: bool = False):
        self.success = success
        self.message = message
        self.data = data
        self.cancelled = cancelled  # True when interrupted by a stop request

    def __repr__(self):
        status = "CANCELLED" if self.cancelled else ("OK" if self.success else "ERR")
        return f"ActionResult({status} {self.message})"


class BaseAction(ABC):
    """
    Abstract base class for all actions.

    Subclasses define:
      - ACTION_TYPE: unique string identifier
      - ACTION_LABEL: human-readable display name
      - ACTION_ICON_KEY: icon id for ui.icons (play, close, eye, ...)
      - ACTION_COLOR: hex color for the block
      - ACTION_DESCRIPTION: tooltip description
    """

    ACTION_TYPE: str = "base"
    ACTION_LABEL: str = "Base Action"
    ACTION_ICON_KEY: str = "gear"
    ACTION_COLOR: str = "#4A90D9"
    ACTION_DESCRIPTION: str = "A base action."

    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.enabled: bool = True
        self.comment: str = ""  # Optional user comment
        self._params: Dict[str, Any] = {}
        self._stop_check = None  # Runtime callable; set by the engine (not serialized)
        self._context: Optional[Dict[str, Any]] = None   # Shared run variables
        self._notify_cb = None  # Runtime callable; routes notifications to the UI
        self._init_params()

    def _init_params(self):
        """Override to initialize default parameter values."""
        pass

    def set_stop_check(self, check):
        """
        Install a zero-argument callable that returns True when a stop was
        requested. Long-running actions should poll `is_stop_requested()`
        so the engine's Stop button stays responsive.
        """
        self._stop_check = check

    def is_stop_requested(self) -> bool:
        """True when the engine asked this action to stop (False if unset)."""
        return bool(self._stop_check and self._stop_check())

    # ── Shared variable context ────────────────────────────────────────────

    def set_context(self, context: Dict[str, Any]):
        """Install the shared per-run variable context (done by the engine)."""
        self._context = context

    def get_var(self, name: str, default: Any = None) -> Any:
        """Read a variable from the shared run context."""
        return (self._context or {}).get(name, default)

    def set_var(self, name: str, value: Any):
        """Write a variable to the shared run context (visible to later blocks)."""
        if self._context is not None:
            self._context[name] = value

    def interpolate(self, text: Any) -> str:
        """
        Replace {{var_name}} tokens with values from the shared context.
        Unknown variables are left untouched, so JSON bodies containing
        single braces stay intact.
        """
        text = "" if text is None else str(text)
        if "{{" not in text:
            return text
        ctx = self._context or {}
        return _VAR_RE.sub(
            lambda m: str(ctx[m.group(1)]) if m.group(1) in ctx else m.group(0),
            text,
        )

    # ── Notifications ──────────────────────────────────────────────────────

    def set_notify(self, callback):
        """Install a notify(title, message) callback (done by the engine)."""
        self._notify_cb = callback

    def notify(self, title: str, message: str):
        """Show a desktop notification (routed to the UI thread by the engine)."""
        if self._notify_cb:
            try:
                self._notify_cb(title, message)
            except Exception:
                pass
        else:
            print(f"[notify] {title}: {message}")

    @property
    def params(self) -> Dict[str, Any]:
        return self._params

    def set_param(self, key: str, value: Any):
        """Set a parameter value."""
        self._params[key] = value

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with an optional default."""
        return self._params.get(key, default)

    @abstractmethod
    def execute(self) -> ActionResult:
        """
        Execute the action. Must be implemented by subclasses.
        Returns an ActionResult indicating success or failure.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this action to a JSON-compatible dict."""
        return {
            "id": self.id,
            "type": self.ACTION_TYPE,
            "enabled": self.enabled,
            "comment": self.comment,
            "params": self._params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseAction":
        """Deserialize an action from a dict (used during load)."""
        instance = cls()
        instance.id = data.get("id", str(uuid.uuid4()))
        instance.enabled = data.get("enabled", True)
        instance.comment = data.get("comment", "")
        instance._params = data.get("params", {})
        return instance

    def get_summary(self) -> str:
        """Return a short human-readable summary of this action's configuration."""
        return self.ACTION_LABEL

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id[:8]}, params={self._params})"
