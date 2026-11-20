# ui/hotkey_dialog.py
"""
HotkeyDialog: Modal dialog for recording multiple keyboard shortcuts per workflow.
"""

from typing import List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence, QColor

from ui.theme import THEME
from utils.hotkey_format import normalize_hotkey


class HotkeyDialog(QDialog):
    """
    Record one or more global hotkeys for a workflow.
    Click Record, press a combination, repeat to add more; select + Remove to delete one.
    """

    def __init__(self, current_hotkeys: List[str] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Hotkeys")
        self.setFixedSize(420, 360)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME['bg_panel']};
                border: 1px solid {THEME['border_light']};
            }}
            QListWidget {{
                background: {THEME['bg_input']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border']};
                border-radius: 6px;
                padding: 4px;
                font-family: Consolas, monospace;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background: {THEME['bg_selected']};
                color: {THEME['text_primary']};
            }}
        """)

        self._hotkeys: List[str] = []
        for hk in current_hotkeys or []:
            normalized = normalize_hotkey(hk)
            if normalized and normalized not in self._hotkeys:
                self._hotkeys.append(normalized)

        self._recording = False
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        instr = QLabel(
            "Click Record, then press a key combination (e.g. Ctrl+Shift+F9).\n"
            "Repeat to add more shortcuts. Each one will run this workflow.\n\n"
            "For fullscreen games (Generals, etc.): use Ctrl+Shift or Ctrl+Alt "
            "with F-keys. If the game runs as Admin, run FlowMatic as Admin too."
        )
        instr.setWordWrap(True)
        instr.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 12px;")
        layout.addWidget(instr)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {THEME['accent_orange']}; font-size: 11px;")
        layout.addWidget(self._status)

        self._list = QListWidget()
        self._list.setMinimumHeight(120)
        layout.addWidget(self._list)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        self._record_btn = QPushButton("Record")
        self._record_btn.setFixedHeight(34)
        self._record_btn.setObjectName("btn_primary")
        self._record_btn.clicked.connect(self._toggle_recording)

        remove_btn = QPushButton("Remove")
        remove_btn.setFixedHeight(34)
        remove_btn.clicked.connect(self._remove_selected)

        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedHeight(34)
        clear_btn.clicked.connect(self._clear_all)

        row_layout.addWidget(self._record_btn)
        row_layout.addWidget(remove_btn)
        row_layout.addWidget(clear_btn)
        row_layout.addStretch()
        layout.addWidget(row)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(34)
        ok_btn.setObjectName("btn_primary")
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addWidget(btn_row)

    def _refresh_list(self):
        self._list.clear()
        if not self._hotkeys:
            item = QListWidgetItem("No hotkeys — add one with Record")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor(THEME['text_muted']))
            self._list.addItem(item)
        else:
            for hk in self._hotkeys:
                self._list.addItem(QListWidgetItem(hk))

    def _toggle_recording(self):
        self._recording = not self._recording
        if self._recording:
            self._status.setText("Listening… press your key combination now")
            self._record_btn.setText("Stop")
            self.grabKeyboard()
            self.setFocus()
        else:
            self._status.setText("")
            self._record_btn.setText("Record")
            self.releaseKeyboard()

    def _remove_selected(self):
        row = self._list.currentRow()
        if 0 <= row < len(self._hotkeys):
            self._hotkeys.pop(row)
            self._refresh_list()

    def _clear_all(self):
        self._recording = False
        self._hotkeys.clear()
        self._status.setText("")
        self._record_btn.setText("Record")
        self.releaseKeyboard()
        self._refresh_list()

    def keyPressEvent(self, event: QKeyEvent):
        if not self._recording:
            super().keyPressEvent(event)
            return

        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_Escape:
            self._toggle_recording()
            return

        parts = []
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            parts.append("ctrl")
        if mods & Qt.ShiftModifier:
            parts.append("shift")
        if mods & Qt.AltModifier:
            parts.append("alt")
        if mods & Qt.MetaModifier:
            parts.append("windows")

        key = event.key()
        modifier_keys = (
            Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
            Qt.Key_AltGr,
        )
        if key not in modifier_keys:
            key_text = QKeySequence(key).toString().lower().strip()
            if key_text:
                parts.append(key_text)

        if len(parts) < 2:
            self._status.setText("Use at least one modifier + a key (e.g. Ctrl+Shift+F9)")
            return

        recorded = normalize_hotkey("+".join(parts))
        if not recorded:
            return

        if recorded in self._hotkeys:
            self._status.setText(f"Already added: {recorded}")
        else:
            self._hotkeys.append(recorded)
            self._status.setText(f"Added: {recorded}")
            self._refresh_list()

        self._toggle_recording()

    def get_hotkeys(self) -> List[str]:
        return list(self._hotkeys)

    @staticmethod
    def ask_hotkeys(current: List[str] | None = None, parent=None) -> tuple:
        """Show dialog and return (hotkeys_list, accepted)."""
        dlg = HotkeyDialog(current, parent)
        accepted = dlg.exec() == QDialog.Accepted
        return dlg.get_hotkeys(), accepted

    @staticmethod
    def ask_hotkey(current: str = "", parent=None) -> tuple:
        """Backward-compatible single hotkey API."""
        current_list = [current] if current and current.strip() else []
        hotkeys, accepted = HotkeyDialog.ask_hotkeys(current_list, parent)
        return (hotkeys[0] if hotkeys else ""), accepted
