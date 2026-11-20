# ui/log_panel.py
"""
LogPanel: Bottom panel showing real-time execution logs.
Color-coded by level with timestamps.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont

from core.engine import ExecutionLog
from ui.theme import THEME
from ui.icons import IconLabel


LEVEL_COLORS = {
    "INFO":    THEME['text_secondary'],
    "SUCCESS": THEME['accent_green'],
    "WARNING": THEME['accent_orange'],
    "ERROR":   THEME['accent_red'],
    "SKIP":    THEME['text_muted'],
}


class LogPanel(QWidget):
    """
    Execution log panel with colored output and clear button.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(200)
        self.setMinimumHeight(120)
        self.setStyleSheet(f"background: {THEME['bg_deep']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background: {THEME['bg_deep']}; border-bottom: 1px solid {THEME['border']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 10, 0)

        log_icon = IconLabel("log", THEME['accent_blue'], 16)
        title = QLabel("Execution Log")
        title.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; background: transparent;")

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedSize(48, 22)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['text_muted']};
                border: 1px solid {THEME['border']};
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                color: {THEME['text_primary']};
                border-color: {THEME['border_light']};
            }}
        """)
        self._clear_btn.clicked.connect(self.clear)

        header_layout.addWidget(log_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self._clear_btn)
        layout.addWidget(header)

        # ── Log output ───────────────────────────────────────────────────────
        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setFont(QFont("Consolas, Courier New, monospace", 11))
        self._log_view.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {THEME['bg_deep']};
                color: {THEME['text_secondary']};
                border: none;
                padding: 8px 14px;
                font-family: "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
                font-size: 11px;
            }}
        """)
        self._log_view.setMaximumBlockCount(500)
        layout.addWidget(self._log_view)

    def append_log(self, entry: ExecutionLog):
        """Append a colored log entry."""
        cursor = self._log_view.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        color = LEVEL_COLORS.get(entry.level, THEME['text_secondary'])
        fmt.setForeground(QColor(color))

        # Timestamp in muted color
        ts_fmt = QTextCharFormat()
        ts_fmt.setForeground(QColor(THEME['text_muted']))
        cursor.insertText(f"[{entry.timestamp}]  ", ts_fmt)

        cursor.insertText(entry.message + "\n", fmt)

        # Auto-scroll
        self._log_view.setTextCursor(cursor)
        self._log_view.ensureCursorVisible()

    def append_text(self, text: str, color: str = None):
        """Append plain text with optional color."""
        entry = ExecutionLog(text, "INFO")
        if color:
            entry.level = "SUCCESS" if color == THEME['accent_green'] else "INFO"
        self.append_log(entry)

    def clear(self):
        self._log_view.clear()
