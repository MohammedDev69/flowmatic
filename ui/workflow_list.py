# ui/workflow_list.py
"""
WorkflowList: Component showing all workflows as tabs/cards.
Supports creating, renaming, deleting, and selecting workflows.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QInputDialog, QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from typing import List, Optional
from core.workflow import Workflow
from ui.theme import THEME
from ui.icons import IconLabel, set_button_icon
from utils.hotkey_format import format_hotkeys_display


class WorkflowTab(QWidget):
    """A single workflow entry in the workflow list."""

    clicked = Signal(str)          # workflow_id
    rename_requested = Signal(str)
    delete_requested = Signal(str)
    hotkey_requested = Signal(str)
    duplicate_requested = Signal(str)

    def __init__(self, workflow: Workflow, parent=None):
        super().__init__(parent)
        self.workflow = workflow
        self._active = False
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(8)

        self._dot = IconLabel("dot", self.workflow.color, 10)
        self._dot.setFixedWidth(14)

        # Name + hotkey
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(1)

        self._name_label = QLabel(self.workflow.name)
        self._name_label.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 12px; font-weight: 600;")

        self._hotkey_label = QLabel(format_hotkeys_display(self.workflow.hotkeys))
        self._hotkey_label.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")

        info_layout.addWidget(self._name_label)
        info_layout.addWidget(self._hotkey_label)

        n = len(self.workflow.actions)
        self._count_badge = QLabel(f"{n} block{'s' if n != 1 else ''}")
        self._count_badge.setAlignment(Qt.AlignCenter)
        self._count_badge.setStyleSheet(f"""
            background: {THEME['bg_card']};
            color: {THEME['text_secondary']};
            border: 1px solid {THEME['border']};
            border-radius: 8px;
            font-size: 9px;
            font-weight: 600;
            padding: 2px 7px;
        """)

        self._menu_btn = QPushButton()
        self._menu_btn.setFixedSize(26, 26)
        self._menu_btn.setCursor(Qt.PointingHandCursor)
        set_button_icon(self._menu_btn, "menu", THEME['text_muted'], 14)
        self._menu_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {THEME['bg_hover']};
            }}
        """)
        self._menu_btn.setVisible(False)
        self._menu_btn.clicked.connect(self._show_menu)

        layout.addWidget(self._dot)
        layout.addWidget(info, 1)
        layout.addWidget(self._count_badge)
        layout.addWidget(self._menu_btn)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def refresh(self):
        self._name_label.setText(self.workflow.name)
        self._hotkey_label.setText(format_hotkeys_display(self.workflow.hotkeys))
        n = len(self.workflow.actions)
        self._count_badge.setText(f"{n} block{'s' if n != 1 else ''}")
        self._dot.set_color(self.workflow.color)

    def _apply_style(self):
        bg = THEME['bg_selected'] if self._active else "transparent"
        border = f"border-left: 2px solid {self.workflow.color};" if self._active else ""
        self.setStyleSheet(f"""
            WorkflowTab {{
                background: {bg};
                {border}
                border-radius: 6px;
            }}
            WorkflowTab:hover {{
                background: {THEME['bg_hover']};
            }}
        """)

    def _show_menu(self):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        rename = menu.addAction("Rename")
        hotkey = menu.addAction("Set Hotkeys")
        duplicate = menu.addAction("Duplicate")
        menu.addSeparator()
        delete = menu.addAction("Delete Workflow")

        act = menu.exec(self._menu_btn.mapToGlobal(self._menu_btn.rect().bottomLeft()))
        if act == rename:
            self.rename_requested.emit(self.workflow.id)
        elif act == hotkey:
            self.hotkey_requested.emit(self.workflow.id)
        elif act == duplicate:
            self.duplicate_requested.emit(self.workflow.id)
        elif act == delete:
            self.delete_requested.emit(self.workflow.id)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.workflow.id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._menu_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._menu_btn.setVisible(False)
        super().leaveEvent(event)


class WorkflowListPanel(QWidget):
    """
    Left sidebar section showing all loaded workflows.
    Embedded above or below the palette depending on layout.
    """

    workflow_selected = Signal(str)   # workflow_id
    workflow_created = Signal()
    workflow_deleted = Signal(str)
    workflow_renamed = Signal(str, str)  # workflow_id, new_name
    hotkey_requested = Signal(str)
    workflow_duplicated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {THEME['bg_panel']};")
        self._tabs: List[WorkflowTab] = []
        self._active_id: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background: {THEME['bg_panel']}; border-bottom: 1px solid {THEME['border']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 10, 0)

        title = QLabel("Workflows")
        title.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 13px; font-weight: 700;")

        new_btn = QPushButton()
        new_btn.setFixedSize(28, 28)
        set_button_icon(new_btn, "plus", THEME['accent_blue'], 14)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setToolTip("Create new workflow")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['bg_card']};
                color: {THEME['accent_blue']};
                border: 1px solid {THEME['border']};
                border-radius: 13px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {THEME['accent_blue']};
                color: white;
            }}
        """)
        new_btn.clicked.connect(self.workflow_created)

        header_layout.addWidget(title, 1)
        header_layout.addWidget(new_btn)
        layout.addWidget(header)

        # Scroll area for workflow tabs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {THEME['bg_panel']}; border: none;")

        self._list_container = QWidget()
        self._list_container.setStyleSheet(f"background: {THEME['bg_panel']};")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(2)
        self._list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll)

    def add_workflow(self, workflow: Workflow):
        tab = WorkflowTab(workflow)
        tab.clicked.connect(self._on_tab_clicked)
        tab.delete_requested.connect(self._on_delete)
        tab.rename_requested.connect(self._on_rename)
        tab.hotkey_requested.connect(self.hotkey_requested)
        tab.duplicate_requested.connect(self.workflow_duplicated)
        self._tabs.append(tab)
        self._list_layout.addWidget(tab)

    def remove_workflow(self, workflow_id: str):
        for tab in self._tabs[:]:
            if tab.workflow.id == workflow_id:
                self._tabs.remove(tab)
                self._list_layout.removeWidget(tab)
                tab.deleteLater()
                break

    def set_active(self, workflow_id: Optional[str]):
        self._active_id = workflow_id
        for tab in self._tabs:
            tab.set_active(tab.workflow.id == workflow_id)

    def refresh_workflow(self, workflow_id: str):
        for tab in self._tabs:
            if tab.workflow.id == workflow_id:
                tab.refresh()
                break

    def _on_tab_clicked(self, workflow_id: str):
        self.set_active(workflow_id)
        self.workflow_selected.emit(workflow_id)

    def _on_delete(self, workflow_id: str):
        reply = QMessageBox.question(
            self, "Delete Workflow",
            "Are you sure you want to delete this workflow?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.workflow_deleted.emit(workflow_id)

    def _on_rename(self, workflow_id: str):
        tab = next((t for t in self._tabs if t.workflow.id == workflow_id), None)
        if not tab:
            return
        name, ok = QInputDialog.getText(self, "Rename Workflow", "New name:", text=tab.workflow.name)
        if ok and name.strip():
            self.workflow_renamed.emit(workflow_id, name.strip())
