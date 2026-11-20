# core/workflow.py
"""
Workflow model: a named sequence of actions with an optional hotkey.
"""

import uuid
from typing import List, Optional, Dict, Any
from actions.base_action import BaseAction


class Workflow:
    """
    Represents a single automation workflow.

    A workflow is an ordered list of BaseAction instances,
    with a name, description, and optional global hotkey trigger.
    """

    def __init__(self, name: str = "New Workflow"):
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = ""
        self.hotkeys: List[str] = []   # e.g. ["ctrl+shift+f1", "ctrl+alt+r"]
        self.actions: List[BaseAction] = []
        self.color: str = "#4A90D9"    # Visual color for the workflow tab
        self.created_at: str = ""
        self.modified_at: str = ""

    @property
    def hotkey(self) -> str:
        """First hotkey (backward compatibility)."""
        return self.hotkeys[0] if self.hotkeys else ""

    @hotkey.setter
    def hotkey(self, value: str):
        value = (value or "").strip()
        self.hotkeys = [value] if value else []

    def add_action(self, action: BaseAction, index: Optional[int] = None):
        """Append or insert an action."""
        if index is None:
            self.actions.append(action)
        else:
            self.actions.insert(index, action)

    def remove_action(self, action_id: str) -> bool:
        """Remove an action by its ID. Returns True if found and removed."""
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                self.actions.pop(i)
                return True
        return False

    def move_action(self, from_index: int, to_index: int):
        """Move an action from one position to another."""
        if 0 <= from_index < len(self.actions) and 0 <= to_index < len(self.actions):
            action = self.actions.pop(from_index)
            self.actions.insert(to_index, action)

    def get_action(self, action_id: str) -> Optional[BaseAction]:
        """Find an action by ID."""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hotkeys": list(self.hotkeys),
            "hotkey": self.hotkey,
            "color": self.color,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "actions": [a.to_dict() for a in self.actions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry) -> "Workflow":
        """Deserialize a workflow from a dict, using registry to reconstruct actions."""
        wf = cls(name=data.get("name", "Unnamed"))
        wf.id = data.get("id", str(uuid.uuid4()))
        wf.description = data.get("description", "")
        raw_hotkeys = data.get("hotkeys")
        if isinstance(raw_hotkeys, list):
            wf.hotkeys = [str(h).strip() for h in raw_hotkeys if str(h).strip()]
        else:
            legacy = data.get("hotkey", "")
            wf.hotkeys = [legacy.strip()] if legacy and str(legacy).strip() else []
        wf.color = data.get("color", "#4A90D9")
        wf.created_at = data.get("created_at", "")
        wf.modified_at = data.get("modified_at", "")

        for action_data in data.get("actions", []):
            action = registry.deserialize_action(action_data)
            if action:
                wf.actions.append(action)

        return wf

    def __repr__(self):
        return f"Workflow(name={self.name!r}, actions={len(self.actions)}, hotkeys={self.hotkeys!r})"
