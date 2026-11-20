# ui/properties_panel.py
"""
PropertiesPanel: Right panel showing editable properties for the selected block.
Dynamically builds form fields based on the selected action's params.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox, QPushButton,
    QScrollArea, QFrame, QFileDialog, QTextEdit, QSizePolicy,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from typing import Optional, Dict, Any
from actions.base_action import BaseAction
from actions.control_actions import ConditionAction
from actions.keyboard_actions import SendKeysAction
from actions.http_actions import HttpRequestAction
from ui.theme import THEME
from ui.icons import icon_container, action_icon_key
from utils.window_helper import list_open_window_titles


class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            color: {THEME['text_muted']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 10px 0 4px 0;
        """)


class FieldLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {THEME['text_secondary']};
            font-size: 12px;
            font-weight: 500;
        """)


class PropertiesPanel(QWidget):
    """
    Shows and edits the properties of the currently selected action block.
    """

    params_changed = Signal(str)  # action_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(320)
        self.setStyleSheet(f"background: {THEME['bg_panel']};")

        self._current_action: Optional[BaseAction] = None
        self._field_map: Dict[str, Any] = {}  # param_key -> widget

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        self._header = QWidget()
        self._header.setFixedHeight(52)
        self._header.setStyleSheet(f"background: {THEME['bg_panel']}; border-bottom: 1px solid {THEME['border']};")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self._header_title = QLabel("Properties")
        self._header_title.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 14px;
            font-weight: 700;
        """)
        header_layout.addWidget(self._header_title)
        layout.addWidget(self._header)

        # ── Scroll area for form ─────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {THEME['bg_panel']}; border: none;")

        self._form_container = QWidget()
        self._form_container.setStyleSheet(f"background: {THEME['bg_panel']};")
        self._form_layout = QVBoxLayout(self._form_container)
        self._form_layout.setContentsMargins(14, 12, 14, 20)
        self._form_layout.setSpacing(6)
        self._form_layout.setAlignment(Qt.AlignTop)

        # Empty state
        self._empty_label = QLabel("Select a block\nto edit its properties")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {THEME['text_muted']};
            font-size: 13px;
            padding: 40px 20px;
            line-height: 1.8;
        """)
        self._form_layout.addWidget(self._empty_label)

        scroll.setWidget(self._form_container)
        layout.addWidget(scroll)

    def show_action(self, action: Optional[BaseAction]):
        """Populate the panel with the given action's properties."""
        self._current_action = action
        self._field_map.clear()

        # Clear current form
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if action is None:
            self._header_title.setText("Properties")
            self._empty_label = QLabel("Select a block\nto edit its properties")
            self._empty_label.setAlignment(Qt.AlignCenter)
            self._empty_label.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 13px; padding: 40px 20px;")
            self._form_layout.addWidget(self._empty_label)
            return

        # ── Block type badge ─────────────────────────────────────────────────
        badge = QWidget()
        badge.setFixedHeight(48)
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setSpacing(10)

        icon = icon_container(action_icon_key(action), action.ACTION_COLOR, 40)

        name_lbl = QLabel(action.ACTION_LABEL)
        name_lbl.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 13px;
            font-weight: 700;
        """)

        badge_layout.addWidget(icon)
        badge_layout.addWidget(name_lbl, 1)
        self._form_layout.addWidget(badge)

        # ── Divider ──────────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {THEME['border']}; margin: 4px 0;")
        div.setFixedHeight(1)
        self._form_layout.addWidget(div)

        # ── Dynamic fields based on action type ──────────────────────────────
        self._build_fields(action)

        # ── Common: Comment field ────────────────────────────────────────────
        self._form_layout.addWidget(SectionHeader("Notes"))
        comment_edit = QTextEdit()
        comment_edit.setPlainText(action.comment)
        comment_edit.setFixedHeight(60)
        comment_edit.setPlaceholderText("Optional note...")
        comment_edit.setStyleSheet(f"""
            background: {THEME['bg_input']};
            color: {THEME['text_secondary']};
            border: 1px solid {THEME['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 11px;
        """)
        comment_edit.textChanged.connect(
            lambda: self._on_comment_changed(action, comment_edit)
        )
        self._form_layout.addWidget(comment_edit)

        # ── Enabled toggle ───────────────────────────────────────────────────
        enabled_row = QWidget()
        enabled_layout = QHBoxLayout(enabled_row)
        enabled_layout.setContentsMargins(0, 4, 0, 0)
        enabled_chk = QCheckBox("Block enabled")
        enabled_chk.setChecked(action.enabled)
        enabled_chk.stateChanged.connect(
            lambda state: self._on_enabled_changed(action, state)
        )
        enabled_layout.addWidget(enabled_chk)
        self._form_layout.addWidget(enabled_row)

        self._form_layout.addStretch()

        self._header_title.setText("Properties")

    def _build_fields(self, action: BaseAction):
        """Build form fields dynamically from the action type."""
        params = action.params
        atype = action.ACTION_TYPE

        if atype == "open_program":
            self._form_layout.addWidget(SectionHeader("Program"))
            self._add_file_field("path", "Executable", params.get("path", ""), action,
                                  filter="Executables (*.exe *.sh *.app);;All Files (*)")
            self._add_text_field("arguments", "Arguments", params.get("arguments", ""),
                                  action, placeholder="-flag value")
            self._add_text_field("working_dir", "Working Directory",
                                  params.get("working_dir", ""), action, placeholder="(optional)")
            self._add_check_field("wait", "Wait for process to exit", params.get("wait", False), action)

        elif atype == "close_program":
            self._form_layout.addWidget(SectionHeader("Target Process"))
            self._add_text_field("process_name", "Process Name",
                                  params.get("process_name", ""), action,
                                  placeholder="e.g. notepad.exe")
            self._add_check_field("force", "Force kill (SIGKILL)", params.get("force", False), action)

        elif atype == "wait":
            self._form_layout.addWidget(SectionHeader("Timing"))
            self._add_double_field("seconds", "Duration (seconds)", params.get("seconds", 1.0), action,
                                    minimum=0.0, maximum=3600.0, step=0.5)

        elif atype == "show_window":
            self._form_layout.addWidget(SectionHeader("Window"))
            self._add_window_title_field("window_title", "Window Title",
                                         params.get("window_title", ""), action)
            self._add_check_field("maximize", "Maximize after showing", params.get("maximize", False), action)

        elif atype == "hide_window":
            self._form_layout.addWidget(SectionHeader("Window"))
            self._add_window_title_field("window_title", "Window Title",
                                         params.get("window_title", ""), action)

        elif atype == "condition":
            self._form_layout.addWidget(SectionHeader("Condition"))
            combo_items = ConditionAction.CONDITION_TYPES
            self._add_combo_field("condition_type", "Check Type", combo_items,
                                   params.get("condition_type", combo_items[0]), action)
            self._form_layout.addWidget(SectionHeader("Process Check"))
            self._add_text_field("process_name", "Process Name",
                                  params.get("process_name", ""), action,
                                  placeholder="e.g. chrome.exe")
            self._form_layout.addWidget(SectionHeader("Variable Check"))
            self._add_text_field("var_name", "Variable Name",
                                  params.get("var_name", ""), action,
                                  placeholder="e.g. http_response")
            self._add_text_field("compare_value", "Compare Value",
                                  params.get("compare_value", ""), action,
                                  placeholder="Used by ==, != and contains")
            self._add_int_field("skip_blocks_on_false", "Skip N blocks if False",
                                 params.get("skip_blocks_on_false", 1), action,
                                 minimum=0, maximum=100)

        elif atype == "loop":
            self._form_layout.addWidget(SectionHeader("Loop"))
            self._add_int_field("times", "Repeat times", params.get("times", 3), action,
                                minimum=1, maximum=10000)
            self._add_int_field("blocks", "Blocks in loop body", params.get("blocks", 1), action,
                                minimum=1, maximum=100)

        elif atype == "send_keys":
            self._form_layout.addWidget(SectionHeader("Keyboard"))
            self._add_combo_field("mode", "Mode", SendKeysAction.MODES,
                                  params.get("mode", "type_text"), action)
            self._add_text_field("text", "Text to type", params.get("text", ""), action,
                                 placeholder="Supports {{variables}}")
            self._add_text_field("hotkey", "Hotkey combo", params.get("hotkey", ""), action,
                                 placeholder="e.g. ctrl+shift+s")
            self._add_double_field("interval", "Delay between keys (s)",
                                   params.get("interval", 0.02), action,
                                   minimum=0.0, maximum=1.0, step=0.01)
            self._add_int_field("repeat", "Hotkey repeats", params.get("repeat", 1), action,
                                minimum=1, maximum=100)

        elif atype == "http_request":
            self._form_layout.addWidget(SectionHeader("HTTP Request"))
            self._add_combo_field("method", "Method", HttpRequestAction.METHODS,
                                  params.get("method", "GET"), action)
            self._add_text_field("url", "URL", params.get("url", ""), action,
                                 placeholder="https://api.example.com — {{variables}} OK")
            self._add_multiline_field("headers", "Headers (Key: Value per line)",
                                      params.get("headers", ""), action)
            self._add_multiline_field("body", "Body", params.get("body", ""), action,
                                      placeholder="Supports {{variables}}")
            self._add_double_field("timeout", "Timeout (s)", params.get("timeout", 10.0),
                                   action, minimum=1.0, maximum=300.0, step=1.0)
            self._add_text_field("save_to_var", "Save response to variable",
                                 params.get("save_to_var", "http_response"), action)

        elif atype == "notify":
            self._form_layout.addWidget(SectionHeader("Notification"))
            self._add_text_field("title", "Title", params.get("title", "FlowMatic"), action)
            self._add_multiline_field("message", "Message", params.get("message", ""), action,
                                      placeholder="Supports {{variables}}")

    # ── Field builder helpers ─────────────────────────────────────────────────

    def _add_text_field(self, key, label, value, action, placeholder=""):
        self._form_layout.addWidget(FieldLabel(label))
        edit = QLineEdit(str(value))
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(lambda v: self._on_param_changed(action, key, v))
        self._form_layout.addWidget(edit)
        self._field_map[key] = edit

    def _add_multiline_field(self, key, label, value, action, placeholder="", height=72):
        self._form_layout.addWidget(FieldLabel(label))
        edit = QPlainTextEdit(str(value or ""))
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(height)
        edit.textChanged.connect(lambda: self._on_param_changed(action, key, edit.toPlainText()))
        self._form_layout.addWidget(edit)
        self._field_map[key] = edit

    def _add_window_title_field(self, key, label, value, action):
        """Editable combo with a refresh list of currently open window titles."""
        self._form_layout.addWidget(FieldLabel(label))
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.lineEdit().setPlaceholderText("Partial title OK — pick or type")
        titles = list_open_window_titles()
        if titles:
            combo.addItems(titles)
        current = str(value).strip()
        if current:
            if combo.findText(current) < 0:
                combo.insertItem(0, current)
            combo.setCurrentText(current)
        combo.currentTextChanged.connect(lambda v: self._on_param_changed(action, key, v.strip()))

        refresh = QPushButton("Refresh")
        refresh.setFixedWidth(72)
        refresh.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['bg_card']};
                color: {THEME['text_secondary']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                font-size: 11px;
                padding: 5px 8px;
            }}
            QPushButton:hover {{
                background: {THEME['bg_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        refresh.clicked.connect(lambda: self._refresh_window_titles(combo))

        row_layout.addWidget(combo, 1)
        row_layout.addWidget(refresh)
        self._form_layout.addWidget(row)
        self._field_map[key] = combo

    def _refresh_window_titles(self, combo: QComboBox):
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        titles = list_open_window_titles()
        if titles:
            combo.addItems(titles)
        if current:
            if combo.findText(current) < 0:
                combo.insertItem(0, current)
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _add_file_field(self, key, label, value, action, filter="All Files (*)"):
        self._form_layout.addWidget(FieldLabel(label))
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        edit = QLineEdit(str(value))
        edit.setPlaceholderText("Path to executable...")
        edit.textChanged.connect(lambda v: self._on_param_changed(action, key, v))

        browse = QPushButton("Browse")
        browse.setFixedWidth(64)
        browse.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['bg_card']};
                color: {THEME['text_secondary']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                font-size: 11px;
                padding: 5px 8px;
            }}
            QPushButton:hover {{
                background: {THEME['bg_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        browse.clicked.connect(lambda: self._browse_file(edit, filter))

        row_layout.addWidget(edit, 1)
        row_layout.addWidget(browse)
        self._form_layout.addWidget(row)
        self._field_map[key] = edit

    def _browse_file(self, edit: QLineEdit, filter: str):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", filter)
        if path:
            edit.setText(path)

    def _add_double_field(self, key, label, value, action, minimum=0.0, maximum=9999.0, step=1.0):
        self._form_layout.addWidget(FieldLabel(label))
        spin = QDoubleSpinBox()
        spin.setMinimum(minimum)
        spin.setMaximum(maximum)
        spin.setSingleStep(step)
        spin.setDecimals(1)
        spin.setValue(float(value))
        spin.valueChanged.connect(lambda v: self._on_param_changed(action, key, v))
        self._form_layout.addWidget(spin)
        self._field_map[key] = spin

    def _add_int_field(self, key, label, value, action, minimum=0, maximum=999):
        self._form_layout.addWidget(FieldLabel(label))
        spin = QSpinBox()
        spin.setMinimum(minimum)
        spin.setMaximum(maximum)
        spin.setValue(int(value))
        spin.valueChanged.connect(lambda v: self._on_param_changed(action, key, v))
        self._form_layout.addWidget(spin)
        self._field_map[key] = spin

    def _add_check_field(self, key, label, value, action):
        chk = QCheckBox(label)
        chk.setChecked(bool(value))
        chk.stateChanged.connect(lambda s: self._on_param_changed(action, key, bool(s)))
        self._form_layout.addWidget(chk)
        self._field_map[key] = chk

    def _add_combo_field(self, key, label, items, value, action):
        self._form_layout.addWidget(FieldLabel(label))
        combo = QComboBox()
        combo.addItems(items)
        if value in items:
            combo.setCurrentIndex(items.index(value))
        combo.currentTextChanged.connect(lambda v: self._on_param_changed(action, key, v))
        self._form_layout.addWidget(combo)
        self._field_map[key] = combo

    def _on_param_changed(self, action: BaseAction, key: str, value):
        action.set_param(key, value)
        self.params_changed.emit(action.id)

    def _on_comment_changed(self, action: BaseAction, widget: QTextEdit):
        action.comment = widget.toPlainText()

    def _on_enabled_changed(self, action: BaseAction, state: int):
        action.enabled = bool(state)
        self.params_changed.emit(action.id)
