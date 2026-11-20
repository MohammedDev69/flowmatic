# core/engine.py
"""
WorkflowEngine: Executes a workflow's actions sequentially in a background thread.

Emits Qt signals for each step so the UI can update in real time.
Supports pause/stop, error handling, and condition-based skipping.
"""

import time
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, QThread

from core.workflow import Workflow
from actions.base_action import ActionResult
from actions.control_actions import ConditionAction, LoopAction


class ExecutionLog:
    """A single log entry from the execution engine."""

    LEVEL_INFO = "INFO"
    LEVEL_SUCCESS = "SUCCESS"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    LEVEL_SKIP = "SKIP"

    def __init__(self, message: str, level: str = "INFO", action_id: str = ""):
        self.message = message
        self.level = level
        self.action_id = action_id
        self.timestamp = time.strftime("%H:%M:%S")

    def __repr__(self):
        return f"[{self.timestamp}] [{self.level}] {self.message}"


class EngineWorker(QObject):
    """
    Runs workflow execution in a dedicated QThread.
    Communicates with the UI via Qt signals.
    """

    # Signals
    log_emitted = Signal(object)          # ExecutionLog
    action_started = Signal(str)          # action_id
    action_finished = Signal(str, bool)   # action_id, success
    workflow_started = Signal(str)        # workflow_name
    workflow_finished = Signal(bool, str) # success, message
    progress_updated = Signal(int, int)   # current_step, total_steps
    notify_requested = Signal(str, str)   # title, message

    def __init__(self, workflow: Workflow, parent=None):
        super().__init__(parent)
        self.workflow = workflow
        self._stop_requested = False
        self._paused = False

    def request_stop(self):
        self._stop_requested = True

    def request_pause(self):
        self._paused = True

    def request_resume(self):
        self._paused = False

    def _emit_log(self, message: str, level: str = "INFO", action_id: str = ""):
        self.log_emitted.emit(ExecutionLog(message, level, action_id))

    def run(self):
        """Main execution loop. Called from the QThread."""
        wf = self.workflow
        actions = [a for a in wf.actions if a.enabled]
        total = len(actions)

        # Shared variables visible to every block in this run
        context = {
            "workflow": wf.name,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._emit_log(f">> Starting workflow: {wf.name}", "INFO")
        self.workflow_started.emit(wf.name)

        if not actions:
            self._emit_log("Workflow has no enabled actions.", "WARNING")
            self.workflow_finished.emit(True, "No actions to run.")
            return

        skip_next = 0  # Number of blocks to skip (from Condition)
        loop_frames: List[dict] = []  # Active Loop blocks (jump-back state)
        i = 0

        while True:
            # ── Loop jump-back ───────────────────────────────────
            # When the index moves past a loop body's end (including the
            # very end of the workflow), either jump back for another
            # iteration or pop the finished frame.
            jumped = False
            while loop_frames and i > loop_frames[-1]["end"]:
                frame = loop_frames.pop()
                if frame["remaining"] > 0:
                    frame["remaining"] -= 1
                    loop_frames.append(frame)
                    self._emit_log(
                        f"  >> Loop: iteration {frame['times'] - frame['remaining']} "
                        f"of {frame['times']}",
                        "INFO",
                        frame["action_id"],
                    )
                    i = frame["jump_to"]
                    jumped = True
                    break
            if jumped:
                continue

            # ── Done? ────────────────────────────────────────────
            if i >= total:
                break

            # ── Stop check ──────────────────────────────────────
            if self._stop_requested:
                self._emit_log("[!] Execution stopped by user.", "WARNING")
                self.workflow_finished.emit(False, "Stopped by user.")
                return

            # ── Pause loop ──────────────────────────────────────
            while self._paused and not self._stop_requested:
                time.sleep(0.1)

            action = actions[i]

            # Install runtime hooks (stop, shared context, notifications)
            action.set_stop_check(lambda: self._stop_requested)
            action.set_context(context)
            action.set_notify(lambda t, m: self.notify_requested.emit(t, m))

            # ── Condition skip ───────────────────────────────────
            if skip_next > 0:
                self._emit_log(
                    f"  >> Skipping block {i+1}: {action.get_summary()}",
                    "SKIP",
                    action.id,
                )
                self.action_started.emit(action.id)
                self.action_finished.emit(action.id, True)
                self.progress_updated.emit(i + 1, total)
                skip_next -= 1
                i += 1
                continue

            # ── Execute ──────────────────────────────────────────
            self._emit_log(
                f"  [{i+1}/{total}] {action.get_summary()}",
                "INFO",
                action.id,
            )
            self.action_started.emit(action.id)

            try:
                result: ActionResult = action.execute()
            except Exception as e:
                result = ActionResult(False, f"Unhandled exception: {e}")

            self.progress_updated.emit(i + 1, total)

            if result.cancelled:
                self._emit_log("      [!] Interrupted by stop request.", "WARNING", action.id)
                self.action_finished.emit(action.id, False)
                self._emit_log("[!] Execution stopped by user.", "WARNING")
                self.workflow_finished.emit(False, "Stopped by user.")
                return

            if result.success:
                self._emit_log(f"      OK: {result.message}", "SUCCESS", action.id)
                self.action_finished.emit(action.id, True)

                # Handle condition block skip logic
                if isinstance(action, ConditionAction) and result.data:
                    skip_next = result.data.get("skip_blocks", 0)

                # Handle loop blocks: schedule a jump-back over the body
                if isinstance(action, LoopAction) and result.data:
                    body = int(result.data.get("loop_blocks", 0))
                    times = int(result.data.get("loop_times", 0))
                    end = min(i + body, total - 1)
                    if body > 0 and times > 1 and end > i:
                        loop_frames.append({
                            "end": end,
                            "jump_to": i + 1,
                            "remaining": times - 1,
                            "times": times,
                            "action_id": action.id,
                        })
            else:
                self._emit_log(f"      ERR: {result.message}", "ERROR", action.id)
                self.action_finished.emit(action.id, False)

            i += 1

        self._emit_log(f"Done: Workflow '{wf.name}' completed successfully.", "SUCCESS")
        self.workflow_finished.emit(True, f"Workflow '{wf.name}' completed.")


class WorkflowEngine(QObject):
    """
    Public API for executing workflows. Manages thread lifecycle.
    """

    log_emitted = Signal(object)
    action_started = Signal(str)
    action_finished = Signal(str, bool)
    workflow_started = Signal(str)
    workflow_finished = Signal(bool, str)
    progress_updated = Signal(int, int)
    notify_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[EngineWorker] = None
        self.is_running = False

    def run_workflow(self, workflow: Workflow):
        """Start executing a workflow in a background thread."""
        if self.is_running:
            return

        self._thread = QThread()
        self._worker = EngineWorker(workflow)
        self._worker.moveToThread(self._thread)

        # Auto-cleanup: delete the worker when the thread finishes, and the
        # thread object itself afterwards (official Qt threading pattern).
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # Connect worker signals → engine signals (thread-safe)
        self._worker.log_emitted.connect(self.log_emitted)
        self._worker.action_started.connect(self.action_started)
        self._worker.action_finished.connect(self.action_finished)
        self._worker.workflow_started.connect(self.workflow_started)
        self._worker.progress_updated.connect(self.progress_updated)
        self._worker.notify_requested.connect(self.notify_requested)
        self._worker.workflow_finished.connect(self._on_finished)

        self._thread.started.connect(self._worker.run)
        self._thread.start()
        self.is_running = True

    def stop(self):
        """Request the current workflow to stop."""
        if self._worker:
            self._worker.request_stop()

    def pause(self):
        if self._worker:
            self._worker.request_pause()

    def resume(self):
        if self._worker:
            self._worker.request_resume()

    def _on_finished(self, success: bool, message: str):
        self.is_running = False
        self.workflow_finished.emit(success, message)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            # References dropped; deleteLater (wired in run_workflow) cleans up.
            self._thread = None
            self._worker = None
