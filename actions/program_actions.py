# actions/program_actions.py
"""
Actions for launching and terminating programs/processes.
"""

import subprocess
import os
import shlex
import time
from typing import List
import psutil

from .base_action import BaseAction, ActionResult


def _split_arguments(arguments: str) -> List[str]:
    """
    Split an arguments string into a list, respecting quoted values.

    Uses Windows-style parsing on Windows (backslashes stay literal, quotes
    group values) so paths like `"C:\\Program Files\\app.exe" --flag` survive.
    """
    arguments = (arguments or "").strip()
    if not arguments:
        return []
    if os.name == "nt":
        raw = shlex.split(arguments, posix=False)
        return [tok.strip('"') for tok in raw]
    return shlex.split(arguments)


class OpenProgramAction(BaseAction):
    """Opens an executable program or file."""

    ACTION_TYPE = "open_program"
    ACTION_LABEL = "Open Program"
    ACTION_ICON_KEY = "play"
    ACTION_COLOR = "#2ECC71"
    ACTION_DESCRIPTION = "Launch an application or open a file."

    def _init_params(self):
        self._params = {
            "path": "",           # Path to executable or file
            "arguments": "",      # Optional command-line arguments
            "working_dir": "",    # Optional working directory
            "wait": False,        # Whether to wait for the process to exit
        }

    def execute(self) -> ActionResult:
        path = self.interpolate(self.get_param("path", ""))
        arguments = self.interpolate(self.get_param("arguments", ""))
        working_dir = self.interpolate(self.get_param("working_dir", "")) or None
        wait = self.get_param("wait", False)

        if not path:
            return ActionResult(False, "No program path specified.")

        if not os.path.exists(path):
            return ActionResult(False, f"File not found: {path}")

        try:
            cmd = [path]
            cmd.extend(_split_arguments(arguments))

            proc = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if wait:
                # Poll instead of blocking proc.wait() so Stop stays responsive.
                while proc.poll() is None:
                    if self.is_stop_requested():
                        return ActionResult(
                            False,
                            f"Launched {os.path.basename(path)} (PID {proc.pid}); "
                            f"wait interrupted by stop request.",
                            proc.pid,
                            cancelled=True,
                        )
                    time.sleep(0.1)

            return ActionResult(True, f"Launched: {os.path.basename(path)} (PID {proc.pid})", proc.pid)

        except PermissionError:
            return ActionResult(False, f"Permission denied: {path}")
        except Exception as e:
            return ActionResult(False, f"Failed to launch: {e}")

    def get_summary(self) -> str:
        path = self.get_param("path", "")
        if path:
            return f"Open: {os.path.basename(path)}"
        return "Open Program (not configured)"


class CloseProgramAction(BaseAction):
    """Terminates a running process by name or PID."""

    ACTION_TYPE = "close_program"
    ACTION_LABEL = "Close Program"
    ACTION_ICON_KEY = "close"
    ACTION_COLOR = "#E74C3C"
    ACTION_DESCRIPTION = "Terminate a running application by process name."

    def _init_params(self):
        self._params = {
            "process_name": "",   # e.g. "notepad.exe" or "chrome"
            "force": False,       # Kill forcefully (SIGKILL) vs gracefully (SIGTERM)
        }

    def execute(self) -> ActionResult:
        process_name = self.get_param("process_name", "").strip()
        force = self.get_param("force", False)

        if not process_name:
            return ActionResult(False, "No process name specified.")

        # Normalize: strip .exe suffix for cross-platform matching
        name_lower = process_name.lower()
        killed = []

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = proc.info["name"].lower()
                if pname == name_lower or pname == name_lower + ".exe" or pname.replace(".exe", "") == name_lower:
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    killed.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            return ActionResult(True, f"Closed {process_name} (PIDs: {killed})", killed)
        else:
            return ActionResult(False, f"No running process found matching: {process_name}")

    def get_summary(self) -> str:
        name = self.get_param("process_name", "")
        if name:
            return f"Close: {name}"
        return "Close Program (not configured)"
