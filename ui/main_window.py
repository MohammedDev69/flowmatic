# ui/main_window.py
"""
MainWindow: Root application window.
Orchestrates all panels, the workflow engine, hotkey manager, and file I/O.
"""

import os
import uuid
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QEvent
from PySide6.QtGui import QIcon

from core.workflow import Workflow
from core.engine import WorkflowEngine, ExecutionLog
from core.registry import ActionRegistry
from utils.file_manager import FileManager
from utils.hotkey_manager import HotkeyManager
from utils.app_settings import AppSettings

from ui.theme import THEME, build_stylesheet
from ui.toolbar import TopToolbar
from ui.palette_panel import PalettePanel
from ui.workflow_canvas import WorkflowCanvas
from ui.properties_panel import PropertiesPanel
from ui.log_panel import LogPanel
from ui.workflow_list import WorkflowListPanel
from ui.block_widget import BlockWidget
from ui.hotkey_dialog import HotkeyDialog
from ui.settings_dialog import SettingsDialog
from ui.icons import make_app_icon


class MainWindow(QMainWindow):
    """
    Primary application window for FlowMatic.

    Layout:
    ┌─────────────────────────────────────────────────────────────┐
    │                        TopToolbar                           │
    ├──────────────┬──────────────────────────────┬──────────────┤
    │ WorkflowList │                              │  Properties  │
    │              │      WorkflowCanvas          │  Panel       │
    │ PalettePanel │      (drag & drop)           │              │
    │              │                              │              │
    ├──────────────┴──────────────────────────────┴──────────────┤
    │                      LogPanel                              │
    └────────────────────────────────────────────────────────────┘
    """

    hotkey_triggered = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowMatic — Visual Automation")
        self.resize(1280, 820)
        self.setMinimumSize(900, 600)

        # Apply global stylesheet
        self.setStyleSheet(build_stylesheet())

        # ── Core services ──────────────────────────────────────────────────
        self._engine = WorkflowEngine(self)
        self._file_manager = FileManager()
        self._hotkey_manager = HotkeyManager()
        self._registry = ActionRegistry()
        self._settings = AppSettings()
        self._force_quit = False

        # ── State ──────────────────────────────────────────────────────────
        self._workflows: List[Workflow] = []
        self._active_workflow: Optional[Workflow] = None
        self._selected_action_id: Optional[str] = None
        self._save_path: Optional[str] = None
        self._is_dirty = False  # Unsaved changes

        self.setWindowIcon(make_app_icon())

        self._build_ui()
        self._connect_signals()
        self._setup_tray()

        # Create a default workflow on startup
        self._create_workflow("My First Workflow")

        # Reopen the last workflow file (replaces the default workflow)
        last_file = self._settings.get("last_file")
        if self._settings.get("reopen_last_file") and last_file and os.path.isfile(last_file):
            if self._load_from_path(last_file):
                self._log_panel.append_text(
                    f"Reopened last file: {last_file}", THEME['accent_blue']
                )

        self._update_status("Ready")
        QTimer.singleShot(400, self._check_hotkey_support)

        if self._settings.get("start_in_tray") and self._tray:
            QTimer.singleShot(0, self._hide_to_tray)

    # ── Public API (used by the entry point) ───────────────────────────────

    def install_hotkey_filter(self, app) -> bool:
        """Install the platform hotkey backend on the QApplication."""
        return self._hotkey_manager.install_on_app(app)

    def should_start_in_tray(self) -> bool:
        """True when the app should start hidden in the system tray."""
        return bool(self._settings.get("start_in_tray") and self._tray)

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the complete window layout."""
        # Central widget
        central = QWidget()
        central.setStyleSheet(f"background: {THEME['bg_base']};")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────────────
        self._toolbar = TopToolbar()
        root_layout.addWidget(self._toolbar)

        # ── Main content splitter (left | center | right) ────────────────────
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(1)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setStyleSheet(f"QSplitter::handle {{ background: {THEME['border']}; }}")

        # ── LEFT: workflow list + action palette ─────────────────────────────
        left_panel = QWidget()
        left_panel.setStyleSheet(f"background: {THEME['bg_panel']};")
        left_panel.setMinimumWidth(220)
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._workflow_list = WorkflowListPanel()
        self._workflow_list.setFixedHeight(180)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {THEME['border']};")
        sep.setFixedHeight(1)

        self._palette = PalettePanel()

        left_layout.addWidget(self._workflow_list)
        left_layout.addWidget(sep)
        left_layout.addWidget(self._palette, 1)

        # ── CENTER: workflow canvas ──────────────────────────────────────────
        center_container = QWidget()
        center_container.setStyleSheet(f"background: {THEME['bg_base']};")
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Canvas header
        canvas_header = QWidget()
        canvas_header.setFixedHeight(44)
        canvas_header.setStyleSheet(f"background: {THEME['bg_panel']}; border-bottom: 1px solid {THEME['border']};")
        ch_layout = QHBoxLayout(canvas_header)
        ch_layout.setContentsMargins(16, 0, 16, 0)

        self._canvas_title = _StyledLabel("Workflow Canvas", bold=True)
        self._canvas_hint = _StyledLabel("Drag blocks from the left to build your automation", muted=True)

        ch_layout.addWidget(self._canvas_title)
        ch_layout.addStretch()
        ch_layout.addWidget(self._canvas_hint)

        self._canvas = WorkflowCanvas()

        center_layout.addWidget(canvas_header)
        center_layout.addWidget(self._canvas, 1)

        # ── RIGHT: properties panel ──────────────────────────────────────────
        self._properties = PropertiesPanel()

        # ── Assemble main splitter ────────────────────────────────────────────
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_container)
        main_splitter.addWidget(self._properties)
        main_splitter.setSizes([240, 780, 280])

        # ── Log panel ────────────────────────────────────────────────────────
        self._log_panel = LogPanel()

        # ── Vertical splitter (main | log) ────────────────────────────────────
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(1)
        v_splitter.setStyleSheet(f"QSplitter::handle {{ background: {THEME['border']}; }}")
        v_splitter.addWidget(main_splitter)
        v_splitter.addWidget(self._log_panel)
        v_splitter.setSizes([600, 160])

        root_layout.addWidget(v_splitter, 1)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {THEME['bg_deep']};
                color: {THEME['text_muted']};
                border-top: 1px solid {THEME['border']};
                font-size: 11px;
                padding: 0 12px;
            }}
        """)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _connect_signals(self):
        """Connect all signals between components."""
        # ── Toolbar ──────────────────────────────────────────────────────────
        self._toolbar.run_clicked.connect(self._run_workflow)
        self._toolbar.stop_clicked.connect(self._stop_workflow)
        self._toolbar.save_clicked.connect(self._save_file)
        self._toolbar.load_clicked.connect(self._load_file)
        self._toolbar.settings_clicked.connect(self._show_settings)

        # ── Workflow list ─────────────────────────────────────────────────────
        self._workflow_list.workflow_selected.connect(self._on_workflow_selected)
        self._workflow_list.workflow_created.connect(self._on_workflow_created)
        self._workflow_list.workflow_deleted.connect(self._on_workflow_deleted)
        self._workflow_list.workflow_renamed.connect(self._on_workflow_renamed)
        self._workflow_list.hotkey_requested.connect(self._on_hotkey_requested)
        self._workflow_list.workflow_duplicated.connect(self._on_workflow_duplicated)
        self.hotkey_triggered.connect(self._on_hotkey_triggered)

        # ── Canvas ────────────────────────────────────────────────────────────
        self._canvas.block_clicked.connect(self._on_block_clicked)
        self._canvas.block_deleted.connect(self._on_block_deleted)
        self._canvas.block_moved.connect(self._on_block_moved)
        self._canvas.drop_from_palette.connect(self._on_drop_from_palette)
        self._canvas.selection_cleared.connect(self._on_selection_cleared)

        # ── Properties ───────────────────────────────────────────────────────
        self._properties.params_changed.connect(self._on_params_changed)

        # ── Engine ───────────────────────────────────────────────────────────
        self._engine.log_emitted.connect(self._log_panel.append_log)
        self._engine.action_started.connect(self._on_action_started)
        self._engine.action_finished.connect(self._on_action_finished)
        self._engine.workflow_started.connect(self._on_engine_started)
        self._engine.workflow_finished.connect(self._on_engine_finished)
        self._engine.progress_updated.connect(self._toolbar.set_progress)
        self._engine.notify_requested.connect(self._show_tray_notification)

    # ── Tray Icon ─────────────────────────────────────────────────────────────

    def _setup_tray(self):
        """Set up system tray icon for background operation."""
        self._tray = None
        if not self._settings.get("show_tray_icon"):
            return
        try:
            from PySide6.QtWidgets import QSystemTrayIcon, QMenu

            if not QSystemTrayIcon.isSystemTrayAvailable():
                return

            self._tray = QSystemTrayIcon(self)
            self._tray.setIcon(make_app_icon())
            self._tray.setToolTip("FlowMatic — Visual Automation")

            tray_menu = QMenu()
            show_act = tray_menu.addAction("Show FlowMatic")
            show_act.triggered.connect(self._show_from_tray)
            run_act = tray_menu.addAction("Run Active Workflow")
            run_act.triggered.connect(self._run_workflow)
            tray_menu.addSeparator()
            settings_act = tray_menu.addAction("Settings...")
            settings_act.triggered.connect(self._show_settings)
            tray_menu.addSeparator()
            quit_act = tray_menu.addAction("Quit FlowMatic")
            quit_act.triggered.connect(self._quit_application)

            self._tray.setContextMenu(tray_menu)
            self._tray.activated.connect(self._on_tray_activated)
            self._tray.show()
        except Exception:
            self._tray = None

    def _on_tray_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _hide_to_tray(self):
        if not self._tray:
            self.showMinimized()
            return
        self.hide()
        if self._settings.get("show_tray_notifications"):
            self._show_tray_notification(
                "FlowMatic",
                "Running in the background. Double-click the tray icon to open.",
            )

    def _quit_application(self):
        self._force_quit = True
        self.close()

    def changeEvent(self, event):
        if (
            event.type() == QEvent.WindowStateChange
            and self.isMinimized()
            and self._settings.get("minimize_to_tray_on_minimize")
            and self._tray
            and not self._force_quit
        ):
            QTimer.singleShot(0, self._hide_to_tray)
        super().changeEvent(event)

    def _show_tray_notification(self, title: str, message: str):
        """Show a system tray notification."""
        if not self._settings.get("show_tray_notifications"):
            return
        try:
            if self._tray and self._tray.isVisible():
                from PySide6.QtWidgets import QSystemTrayIcon
                self._tray.showMessage(title, message, QSystemTrayIcon.Information, 3500)
        except Exception:
            pass

    # ── Workflow Management ───────────────────────────────────────────────────

    def _create_workflow(self, name: str = "New Workflow") -> Workflow:
        wf = Workflow(name=name)
        # Assign a color from rotation
        colors = ["#4A90D9", "#2ECC71", "#E74C3C", "#F39C12", "#9B59B6", "#1ABC9C"]
        wf.color = colors[len(self._workflows) % len(colors)]
        self._workflows.append(wf)
        self._workflow_list.add_workflow(wf)
        self._select_workflow(wf.id)
        self._mark_dirty()
        return wf

    def _select_workflow(self, workflow_id: str):
        wf = self._get_workflow(workflow_id)
        if not wf:
            return

        self._active_workflow = wf
        self._workflow_list.set_active(workflow_id)
        self._toolbar.set_workflow_name(wf.name)
        self._canvas_title.setText(wf.name)

        # Rebuild canvas
        self._canvas.clear_blocks()
        for action in wf.actions:
            self._canvas.add_block(action)

        # Clear properties
        self._properties.show_action(None)
        self._selected_action_id = None

    def _get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return next((w for w in self._workflows if w.id == workflow_id), None)

    # ── Slots ─────────────────────────────────────────────────────────────────

    @Slot()
    def _on_workflow_created(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Workflow", "Workflow name:", text="New Workflow")
        if ok and name.strip():
            self._create_workflow(name.strip())

    @Slot(str)
    def _on_workflow_selected(self, workflow_id: str):
        self._select_workflow(workflow_id)

    @Slot(str)
    def _on_workflow_deleted(self, workflow_id: str):
        wf = self._get_workflow(workflow_id)
        if wf:
            self._unregister_workflow_hotkeys(wf)
        self._workflows = [w for w in self._workflows if w.id != workflow_id]
        self._workflow_list.remove_workflow(workflow_id)
        if self._active_workflow and self._active_workflow.id == workflow_id:
            self._active_workflow = None
            self._canvas.clear_blocks()
            self._toolbar.set_workflow_name("No workflow selected")
            if self._workflows:
                self._select_workflow(self._workflows[0].id)
        self._mark_dirty()

    @Slot(str, str)
    def _on_workflow_renamed(self, workflow_id: str, new_name: str):
        wf = self._get_workflow(workflow_id)
        if wf:
            wf.name = new_name
            self._workflow_list.refresh_workflow(workflow_id)
            if self._active_workflow and self._active_workflow.id == workflow_id:
                self._toolbar.set_workflow_name(new_name)
                self._canvas_title.setText(new_name)
            self._mark_dirty()

    @Slot(str)
    def _on_workflow_duplicated(self, workflow_id: str):
        wf = self._get_workflow(workflow_id)
        if not wf:
            return
        # Serialize → deserialize, then give the copy fresh identities
        data = wf.to_dict()
        copy_wf = Workflow.from_dict(data, self._registry)
        copy_wf.id = str(uuid.uuid4())
        copy_wf.name = f"{wf.name} (copy)"
        copy_wf.hotkeys = []  # Never steal the original's hotkeys
        for action in copy_wf.actions:
            action.id = str(uuid.uuid4())

        colors = ["#4A90D9", "#2ECC71", "#E74C3C", "#F39C12", "#9B59B6", "#1ABC9C"]
        copy_wf.color = colors[len(self._workflows) % len(colors)]

        self._workflows.append(copy_wf)
        self._workflow_list.add_workflow(copy_wf)
        self._select_workflow(copy_wf.id)
        self._mark_dirty()
        self._log_panel.append_text(
            f"Duplicated '{wf.name}' → '{copy_wf.name}'",
            THEME['accent_blue'],
        )

    @Slot(str)
    def _on_hotkey_requested(self, workflow_id: str):
        wf = self._get_workflow(workflow_id)
        if not wf:
            return
        if not self._hotkey_manager.is_available():
            QMessageBox.warning(
                self,
                "Hotkeys Unavailable",
                "Global hotkeys are not available on this system.\n\n"
                "Linux: pip install keyboard and often sudo python main.py\n\n"
                f"Details: {self._hotkey_manager.get_last_error() or 'not supported'}",
            )
            return

        new_hotkeys, ok = HotkeyDialog.ask_hotkeys(wf.hotkeys, self)
        if ok:
            self._unregister_workflow_hotkeys(wf)
            wf.hotkeys = new_hotkeys
            failed = self._register_workflow_hotkeys(wf)
            self._workflow_list.refresh_workflow(workflow_id)
            self._mark_dirty()
            if wf.hotkeys and failed:
                QMessageBox.warning(
                    self,
                    "Hotkey Registration",
                    "Some shortcuts could not be registered:\n"
                    + "\n".join(f"  - {h}" for h in failed)
                    + "\n\n"
                    + self._hotkey_manager.get_game_hotkey_hint(),
                )
            elif wf.hotkeys:
                self._log_panel.append_text(
                    f"Hotkeys for '{wf.name}': {', '.join(wf.hotkeys)}",
                    THEME['accent_blue'],
                )

    def _trigger_workflow_hotkey(self, workflow_id: str):
        """Called from keyboard library thread — emit Qt signal for main thread."""
        self.hotkey_triggered.emit(workflow_id)

    @Slot(str)
    def _on_hotkey_triggered(self, workflow_id: str):
        self._run_specific_workflow(workflow_id)

    def _register_workflow_hotkeys(self, workflow: Workflow) -> List[str]:
        """Register all hotkeys for a workflow. Returns list of keys that failed."""
        if not workflow.hotkeys or not self._hotkey_manager.is_available():
            return list(workflow.hotkeys)

        failed = []
        callback = lambda wid=workflow.id: self._trigger_workflow_hotkey(wid)
        for hk in workflow.hotkeys:
            if not self._hotkey_manager.register(hk, callback):
                failed.append(hk)
        return failed

    def _unregister_workflow_hotkeys(self, workflow: Workflow):
        self._hotkey_manager.unregister_many(workflow.hotkeys)

    def _reregister_all_hotkeys(self):
        self._hotkey_manager.unregister_all()
        for wf in self._workflows:
            self._register_workflow_hotkeys(wf)

    def _check_hotkey_support(self):
        if self._hotkey_manager.is_available():
            self._reregister_all_hotkeys()
            bound = self._hotkey_manager.list_bindings()
            backend = self._hotkey_manager.get_backend()
            if bound:
                self._log_panel.append_text(
                    f"Hotkeys active ({backend}): {', '.join(bound)}",
                    THEME['accent_green'],
                )
            else:
                self._log_panel.append_text(
                    f"Hotkey engine ready ({backend}). Assign shortcuts via Set Hotkeys.",
                    THEME['accent_green'],
                )
            return
        self._log_panel.append_text(
            "Global hotkeys disabled on this platform.",
            THEME['accent_orange'],
        )

    def _run_specific_workflow(self, workflow_id: str):
        wf = self._get_workflow(workflow_id)
        if wf and not self._engine.is_running:
            self._select_workflow(workflow_id)
            self._run_workflow()

    # ── Block Events ──────────────────────────────────────────────────────────

    @Slot(str)
    def _on_block_clicked(self, action_id: str):
        self._selected_action_id = action_id
        if self._active_workflow:
            action = self._active_workflow.get_action(action_id)
            if action:
                self._properties.show_action(action)

    @Slot(str)
    def _on_block_deleted(self, action_id: str):
        if self._active_workflow:
            self._active_workflow.remove_action(action_id)
            self._canvas.remove_block(action_id)
            if self._selected_action_id == action_id:
                self._selected_action_id = None
                self._properties.show_action(None)
            self._workflow_list.refresh_workflow(self._active_workflow.id)
            self._mark_dirty()

    @Slot(str, int)
    def _on_block_moved(self, action_id: str, new_index: int):
        if not self._active_workflow:
            return
        old_index = next(
            (i for i, a in enumerate(self._active_workflow.actions) if a.id == action_id), -1
        )
        if old_index == -1:
            return

        self._active_workflow.move_action(old_index, new_index)

        # Rebuild canvas widgets in new order
        self._canvas.clear_blocks()
        for action in self._active_workflow.actions:
            self._canvas.add_block(action)

        # Re-select
        if self._selected_action_id:
            self._canvas.select_block(self._selected_action_id)

        self._mark_dirty()

    @Slot(str, int)
    def _on_drop_from_palette(self, action_type: str, index: int):
        if not self._active_workflow:
            return
        action = self._registry.create(action_type)
        if not action:
            return
        self._active_workflow.add_action(action, index)
        self._canvas.add_block(action, index)
        self._workflow_list.refresh_workflow(self._active_workflow.id)
        self._mark_dirty()

        # Auto-select the new block
        self._canvas.select_block(action.id)
        self._selected_action_id = action.id
        self._properties.show_action(action)

    @Slot()
    def _on_selection_cleared(self):
        self._selected_action_id = None
        self._properties.show_action(None)

    @Slot(str)
    def _on_params_changed(self, action_id: str):
        self._canvas.refresh_block(action_id)
        if self._active_workflow:
            self._workflow_list.refresh_workflow(self._active_workflow.id)
        self._mark_dirty()

    # ── Engine Control ────────────────────────────────────────────────────────

    @Slot()
    def _run_workflow(self):
        if not self._active_workflow:
            QMessageBox.information(self, "No Workflow", "Please select or create a workflow first.")
            return
        if not self._active_workflow.actions:
            QMessageBox.information(self, "Empty Workflow", "Add some action blocks to the workflow first.")
            return
        if self._engine.is_running:
            return

        self._canvas.reset_all_states()
        self._log_panel.clear()
        self._toolbar.set_running(True)
        self._engine.run_workflow(self._active_workflow)

    @Slot()
    def _stop_workflow(self):
        self._engine.stop()

    @Slot(str)
    def _on_engine_started(self, name: str):
        self._update_status(f"Running: {name}…")

    @Slot(bool, str)
    def _on_engine_finished(self, success: bool, message: str):
        self._toolbar.set_running(False)
        status = f"OK: {message}" if success else f"Error: {message}"
        self._update_status(status)
        self._show_tray_notification("FlowMatic", message)

        # Reset running states after a short delay
        QTimer.singleShot(3000, self._canvas.reset_all_states)

    @Slot(str)
    def _on_action_started(self, action_id: str):
        self._canvas.set_block_state(action_id, BlockWidget.STATE_RUNNING)
        self._canvas.select_block(action_id)

    @Slot(str, bool)
    def _on_action_finished(self, action_id: str, success: bool):
        state = BlockWidget.STATE_SUCCESS if success else BlockWidget.STATE_ERROR
        self._canvas.set_block_state(action_id, state)

    # ── File I/O ──────────────────────────────────────────────────────────────

    @Slot()
    def _save_file(self):
        if not self._save_path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Workflows", "workflows.json", "JSON Files (*.json)"
            )
            if not path:
                return
            self._save_path = path

        if self._file_manager.save_workflows(self._workflows, self._save_path):
            self._is_dirty = False
            self._settings.set("last_file", self._save_path)
            self._settings.save()
            self._update_status(f"Saved to {os.path.basename(self._save_path)}")
            self._log_panel.append_text(f"Saved to {self._save_path}", THEME['accent_green'])
        else:
            QMessageBox.warning(self, "Save Failed", "Could not save workflows. Check permissions.")

    @Slot()
    def _load_file(self):
        if self._is_dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Load anyway?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        path, _ = QFileDialog.getOpenFileName(
            self, "Load Workflows", "", "JSON Files (*.json)"
        )
        if not path:
            return

        if not self._load_from_path(path):
            QMessageBox.warning(self, "Load Failed", "Could not load workflows from the selected file.")
            return

        self._update_status(f"Loaded {len(self._workflows)} workflow(s) from {os.path.basename(path)}")
        self._log_panel.append_text(f"Loaded from {path}", THEME['accent_blue'])

    def _load_from_path(self, path: str) -> bool:
        """Load workflows from a file, replacing current state. Returns True on success."""
        loaded = self._file_manager.load_workflows(path)
        if not loaded:
            return False

        # Clear and reload
        self._hotkey_manager.unregister_all()
        for tab in list(self._workflows):
            self._workflow_list.remove_workflow(tab.id)
        self._workflows.clear()
        self._active_workflow = None
        self._canvas.clear_blocks()

        for wf in loaded:
            self._workflows.append(wf)
            self._workflow_list.add_workflow(wf)
            self._register_workflow_hotkeys(wf)

        if self._workflows:
            self._select_workflow(self._workflows[0].id)

        self._save_path = path
        self._is_dirty = False
        self._settings.set("last_file", path)
        self._settings.save()
        return True

    # ── Settings ──────────────────────────────────────────────────────────────

    @Slot()
    def _show_settings(self):
        accepted = SettingsDialog.open_settings(
            self,
            self._settings,
            hotkey_available=self._hotkey_manager.is_available(),
            hotkey_backend=self._hotkey_manager.get_backend(),
            game_hotkey_hint=self._hotkey_manager.get_game_hotkey_hint(),
            registered_hotkeys=self._hotkey_manager.list_bindings(),
            workflow_count=len(self._workflows),
            save_path=self._save_path or "",
        )
        if accepted:
            self._apply_tray_settings()
            self._log_panel.append_text("Settings saved.", THEME['accent_blue'])

    def _apply_tray_settings(self):
        if self._settings.get("show_tray_icon"):
            if not self._tray:
                self._setup_tray()
            elif self._tray and not self._tray.isVisible():
                self._tray.show()
        else:
            if self._tray:
                self._tray.hide()
                self._tray = None
            if not self.isVisible():
                self._show_from_tray()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_status(self, message: str):
        self._status_bar.showMessage(message)

    def _mark_dirty(self):
        self._is_dirty = True
        if self._active_workflow:
            self._workflow_list.refresh_workflow(self._active_workflow.id)

    def closeEvent(self, event):
        minimize_instead = (
            not self._force_quit
            and self._settings.get("minimize_to_tray_on_close")
            and self._tray
            and self._tray.isVisible()
        )

        if minimize_instead:
            event.ignore()
            self._hide_to_tray()
            return

        if self._is_dirty:
            reply = QMessageBox.question(
                self, "Quit FlowMatic",
                "You have unsaved changes. Save before quitting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                self._save_file()
            elif reply == QMessageBox.Discard:
                pass
            else:
                event.ignore()
                return

        self._hotkey_manager.unregister_all()
        if self._tray:
            self._tray.hide()
        event.accept()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()


def _StyledLabel(text: str, bold: bool = False, muted: bool = False) -> "QLabel":
    """Quick helper to create a styled QLabel."""
    from PySide6.QtWidgets import QLabel
    lbl = QLabel(text)
    style_parts = [f"color: {THEME['text_muted'] if muted else THEME['text_primary']};"]
    style_parts.append("font-size: 13px;")
    if bold:
        style_parts.append("font-weight: 700;")
    lbl.setStyleSheet(" ".join(style_parts))
    return lbl
