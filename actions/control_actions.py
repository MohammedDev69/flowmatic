# actions/control_actions.py
"""
Flow control actions: Wait, Condition checks, etc.
"""

import time
import psutil
from .base_action import BaseAction, ActionResult


class WaitAction(BaseAction):
    """Pauses workflow execution for a specified duration."""

    ACTION_TYPE = "wait"
    ACTION_LABEL = "Wait"
    ACTION_ICON_KEY = "clock"
    ACTION_COLOR = "#F39C12"
    ACTION_DESCRIPTION = "Pause execution for a number of seconds."

    def _init_params(self):
        self._params = {
            "seconds": 1.0,   # Delay in seconds
        }

    # Sleep slice size: small enough for a responsive Stop button,
    # large enough to avoid busy-looping the worker thread.
    _SLICE = 0.1

    def execute(self) -> ActionResult:
        seconds = float(self.get_param("seconds", 1.0))
        if seconds < 0:
            return ActionResult(False, "Wait duration cannot be negative.")

        waited = 0.0
        while waited < seconds:
            if self.is_stop_requested():
                return ActionResult(
                    False,
                    f"Wait interrupted after {waited:.1f}s (stop requested).",
                    cancelled=True,
                )
            time.sleep(min(self._SLICE, seconds - waited))
            waited = min(waited + self._SLICE, seconds)

        return ActionResult(True, f"Waited {seconds:.1f}s")

    def get_summary(self) -> str:
        s = self.get_param("seconds", 1.0)
        return f"Wait {s}s"


class LoopAction(BaseAction):
    """
    Repeats the next N blocks M times.

    The engine reads the result data and jumps back to the block after this
    one until all iterations complete. The body counts *enabled* blocks.
    """

    ACTION_TYPE = "loop"
    ACTION_LABEL = "Loop"
    ACTION_ICON_KEY = "loop"
    ACTION_COLOR = "#8E44AD"
    ACTION_DESCRIPTION = "Repeat the next N blocks M times."

    MAX_TIMES = 100000

    def _init_params(self):
        self._params = {
            "times": 3,    # How many times to repeat the body
            "blocks": 1,   # How many following blocks form the body
        }

    def execute(self) -> ActionResult:
        try:
            times = int(self.get_param("times", 3))
            blocks = int(self.get_param("blocks", 1))
        except (TypeError, ValueError):
            return ActionResult(False, "Loop times/blocks must be whole numbers.")

        times = max(1, min(times, self.MAX_TIMES))
        blocks = max(0, blocks)

        return ActionResult(
            True,
            f"Loop next {blocks} block(s) x{times}",
            {"loop_times": times, "loop_blocks": blocks},
        )

    def get_summary(self) -> str:
        times = self.get_param("times", 3)
        blocks = self.get_param("blocks", 1)
        return f"Loop x{times} ({blocks} block(s))"


class ConditionAction(BaseAction):
    """
    Checks a condition and skips the next N blocks if the condition is False.

    Supported checks:
      - process_is_running / process_is_not_running
      - var_equals / var_not_equals / var_contains / var_is_empty
        (against the shared run context, e.g. a saved HTTP response)
    """

    ACTION_TYPE = "condition"
    ACTION_LABEL = "Condition"
    ACTION_ICON_KEY = "diamond"
    ACTION_COLOR = "#1ABC9C"
    ACTION_DESCRIPTION = "Check a condition. If false, skip the specified number of next blocks."

    CONDITION_TYPES = [
        "process_is_running",
        "process_is_not_running",
        "var_equals",
        "var_not_equals",
        "var_contains",
        "var_is_empty",
    ]

    def _init_params(self):
        self._params = {
            "condition_type": "process_is_running",
            "process_name": "",
            "var_name": "",        # for var_* conditions
            "compare_value": "",   # for var_equals / var_not_equals / var_contains
            "skip_blocks_on_false": 1,  # How many next blocks to skip if condition is False
        }

    def _evaluate_process(self, ctype: str, process_name: str) -> bool:
        running_names = {p.name().lower() for p in psutil.process_iter(["name"])}
        # Also check without .exe
        running_normalized = running_names | {n.replace(".exe", "") for n in running_names}

        is_running = (
            process_name in running_normalized
            or process_name + ".exe" in running_normalized
        )

        if ctype == "process_is_running":
            return is_running
        elif ctype == "process_is_not_running":
            return not is_running
        return False

    def _evaluate_var(self, ctype: str, var_name: str) -> bool:
        value = self.get_var(var_name) if var_name else None
        text = "" if value is None else str(value)
        compare = str(self.get_param("compare_value", ""))

        if ctype == "var_equals":
            return text == compare
        if ctype == "var_not_equals":
            return text != compare
        if ctype == "var_contains":
            return compare in text
        if ctype == "var_is_empty":
            return text.strip() == ""
        return False

    def evaluate(self) -> bool:
        """Evaluate the condition. Returns True/False."""
        ctype = self.get_param("condition_type", "process_is_running")

        if ctype.startswith("var_"):
            return self._evaluate_var(ctype, self.get_param("var_name", "").strip().lower())

        return self._evaluate_process(ctype, self.get_param("process_name", "").strip().lower())

    def execute(self) -> ActionResult:
        """
        The execution engine checks this action's result data to determine
        how many blocks to skip. Data contains: {"skip_blocks": N} if False.
        """
        result = self.evaluate()
        skip = self.get_param("skip_blocks_on_false", 1) if not result else 0

        ctype = self.get_param("condition_type", "")
        if ctype.startswith("var_"):
            target = f"var:{self.get_param('var_name', '')}"
        else:
            target = self.get_param("process_name", "")
        outcome = "TRUE" if result else f"FALSE — skipping {skip} block(s)"

        return ActionResult(
            True,
            f"Condition [{ctype}: {target}] → {outcome}",
            {"condition_result": result, "skip_blocks": skip},
        )

    def get_summary(self) -> str:
        ctype = self.get_param("condition_type", "")
        if ctype.startswith("var_"):
            name = self.get_param("var_name", "")
            ops = {
                "var_equals": "==",
                "var_not_equals": "!=",
                "var_contains": "contains",
                "var_is_empty": "is empty",
            }
            op = ops.get(ctype, "?")
            if ctype == "var_is_empty":
                return f"If {{{name}}} {op}" if name else "Condition (not configured)"
            return f"If {{{name}}} {op} '{self.get_param('compare_value', '')}'"

        pname = self.get_param("process_name", "")
        label = "Not Running?" if "not" in ctype else "Running?"
        if pname:
            return f"If {pname} {label}"
        return "Condition (not configured)"
