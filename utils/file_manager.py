# utils/file_manager.py
"""
FileManager: Save and load workflows as JSON files.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.workflow import Workflow
from core.registry import ActionRegistry


class FileManager:
    """Handles saving and loading workflow files."""

    FILE_VERSION = "1.0"

    def save_workflows(self, workflows: List[Workflow], filepath: str) -> bool:
        """Save a list of workflows to a JSON file."""
        try:
            payload = {
                "version": self.FILE_VERSION,
                "saved_at": datetime.now().isoformat(),
                "workflows": [wf.to_dict() for wf in workflows],
            }
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return True
        except Exception as e:
            print(f"[FileManager] Save error: {e}")
            return False

    def load_workflows(self, filepath: str) -> List[Workflow]:
        """Load workflows from a JSON file. Returns empty list on error."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)

            workflows = []
            registry = ActionRegistry()
            for wf_data in payload.get("workflows", []):
                wf = Workflow.from_dict(wf_data, registry)
                workflows.append(wf)
            return workflows
        except Exception as e:
            print(f"[FileManager] Load error: {e}")
            return []

    def save_single(self, workflow: Workflow, filepath: str) -> bool:
        return self.save_workflows([workflow], filepath)

    def load_single(self, filepath: str) -> Optional[Workflow]:
        workflows = self.load_workflows(filepath)
        return workflows[0] if workflows else None
