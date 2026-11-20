# core/registry.py
"""
ActionRegistry: Central registry mapping action type strings to action classes.
Used for serialization (to_dict) and deserialization (from_dict).
"""

from typing import Dict, Type, List, Optional, Any
from actions.base_action import BaseAction
from actions.program_actions import OpenProgramAction, CloseProgramAction
from actions.window_actions import ShowWindowAction, HideWindowAction
from actions.control_actions import WaitAction, ConditionAction, LoopAction
from actions.keyboard_actions import SendKeysAction
from actions.http_actions import HttpRequestAction
from actions.notify_actions import NotifyAction


class ActionRegistry:
    """
    Singleton registry of all available action types.
    Allows the engine and UI to discover, instantiate, and serialize actions.
    """

    _registry: Dict[str, Type[BaseAction]] = {}

    @classmethod
    def register(cls, action_class: Type[BaseAction]):
        """Register an action class by its ACTION_TYPE string."""
        cls._registry[action_class.ACTION_TYPE] = action_class

    @classmethod
    def get_all(cls) -> List[Type[BaseAction]]:
        """Return all registered action classes in display order."""
        return list(cls._registry.values())

    @classmethod
    def get_class(cls, action_type: str) -> Optional[Type[BaseAction]]:
        """Look up an action class by type string."""
        return cls._registry.get(action_type)

    @classmethod
    def create(cls, action_type: str) -> Optional[BaseAction]:
        """Instantiate a new action of the given type."""
        klass = cls.get_class(action_type)
        if klass:
            return klass()
        return None

    @classmethod
    def deserialize_action(cls, data: Dict[str, Any]) -> Optional[BaseAction]:
        """Reconstruct an action from its serialized dict."""
        action_type = data.get("type")
        klass = cls.get_class(action_type)
        if klass:
            return klass.from_dict(data)
        return None


# ── Register all built-in action types ──────────────────────────────────────
ActionRegistry.register(OpenProgramAction)
ActionRegistry.register(CloseProgramAction)
ActionRegistry.register(WaitAction)
ActionRegistry.register(ShowWindowAction)
ActionRegistry.register(HideWindowAction)
ActionRegistry.register(ConditionAction)
ActionRegistry.register(LoopAction)
ActionRegistry.register(SendKeysAction)
ActionRegistry.register(HttpRequestAction)
ActionRegistry.register(NotifyAction)
