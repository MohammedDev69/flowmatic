# ui/toolbar.py
"""
TopToolbar: Application toolbar with run, stop, save, load, and settings controls.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from ui.theme import THEME
from ui.icons import IconLabel, set_button_icon


def _vline() -> QFrame:
    line = QFrame()
    line.setFixedWidth(1)
    line.setFixedHeight(28)
    line.setStyleSheet(f"background: {THEME['border_light']}; border: none;")
    return line


class TopToolbar(QWidget):
    """Top application bar."""

    run_clicked = Signal()
    stop_clicked = Signal()
    save_clicked = Signal()
    load_clicked = Signal()
    settings_clicked = Signal()
    new_workflow_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            TopToolbar {{
                background: {THEME['bg_deep']};
                border-bottom: 1px solid {THEME['border']};
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        logo = IconLabel("flowmatic", THEME['accent_blue'], 22)

        app_name = QLabel("FlowMatic")
        app_name.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: transparent;
        """)

        version = QLabel("v1.0")
        version.setStyleSheet(f"""
            color: {THEME['text_muted']};
            font-size: 10px;
            font-weight: 600;
            background: {THEME['bg_card']};
            border: 1px solid {THEME['border']};
            border-radius: 8px;
            padding: 2px 8px;
        """)

        self._workflow_label = QLabel("No workflow selected")
        self._workflow_label.setStyleSheet(f"""
            color: {THEME['text_secondary']};
            font-size: 13px;
            font-weight: 500;
            background: transparent;
        """)
        self._workflow_label.setMinimumWidth(160)

        self._progress = QProgressBar()
        self._progress.setFixedWidth(140)
        self._progress.setFixedHeight(6)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)

        self._run_btn = QPushButton("Run")
        self._run_btn.setObjectName("btn_run")
        self._run_btn.setFixedHeight(36)
        self._run_btn.setMinimumWidth(96)
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.setToolTip("Run the current workflow (or use assigned hotkey)")
        set_button_icon(self._run_btn, "play", "#FFFFFF", 14)
        self._run_btn.setStyleSheet(f"""
            QPushButton#btn_run {{
                background-color: {THEME['accent_green']};
                color: #FFFFFF;
                border: none;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 18px 8px 12px;
                border-radius: 6px;
            }}
            QPushButton#btn_run:hover {{
                background-color: #3DDB84;
            }}
            QPushButton#btn_run:pressed {{
                background-color: #25A85A;
            }}
            QPushButton#btn_run:disabled {{
                background-color: {THEME['bg_card']};
                color: {THEME['text_muted']};
            }}
        """)
        self._run_btn.clicked.connect(self.run_clicked)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("btn_stop")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.setMinimumWidth(96)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setVisible(False)
        self._stop_btn.setToolTip("Stop the running workflow")
        set_button_icon(self._stop_btn, "stop", "#FFFFFF", 14)
        self._stop_btn.setStyleSheet(f"""
            QPushButton#btn_stop {{
                background-color: {THEME['accent_red']};
                color: #FFFFFF;
                border: none;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 18px 8px 12px;
                border-radius: 6px;
            }}
            QPushButton#btn_stop:hover {{
                background-color: #F06A5B;
            }}
            QPushButton#btn_stop:pressed {{
                background-color: #C0392B;
            }}
        """)
        self._stop_btn.clicked.connect(self.stop_clicked)

        btn_secondary = f"""
            QPushButton {{
                background: {THEME['bg_card']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border']};
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 14px;
            }}
            QPushButton:hover {{
                background: {THEME['bg_hover']};
                border-color: {THEME['border_light']};
            }}
        """

        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedHeight(34)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.setToolTip("Save all workflows to file")
        set_button_icon(self._save_btn, "save", THEME['text_secondary'], 14)
        self._save_btn.setStyleSheet(btn_secondary)
        self._save_btn.clicked.connect(self.save_clicked)

        self._load_btn = QPushButton("Load")
        self._load_btn.setFixedHeight(34)
        self._load_btn.setCursor(Qt.PointingHandCursor)
        self._load_btn.setToolTip("Load workflows from file")
        set_button_icon(self._load_btn, "load", THEME['text_secondary'], 14)
        self._load_btn.setStyleSheet(btn_secondary)
        self._load_btn.clicked.connect(self.load_clicked)

        self._settings_btn = QPushButton()
        self._settings_btn.setFixedSize(36, 34)
        self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.setToolTip("Settings")
        set_button_icon(self._settings_btn, "settings", THEME['text_secondary'], 16)
        self._settings_btn.setStyleSheet(btn_secondary)
        self._settings_btn.clicked.connect(self.settings_clicked)

        layout.addWidget(logo)
        layout.addWidget(app_name)
        layout.addWidget(version)
        layout.addWidget(_vline())
        layout.addWidget(self._workflow_label)
        layout.addWidget(self._progress)
        layout.addStretch()
        layout.addWidget(self._run_btn)
        layout.addWidget(self._stop_btn)
        layout.addWidget(_vline())
        layout.addWidget(self._save_btn)
        layout.addWidget(self._load_btn)
        layout.addWidget(_vline())
        layout.addWidget(self._settings_btn)

    def set_workflow_name(self, name: str):
        self._workflow_label.setText(name)

    def set_running(self, running: bool):
        self._run_btn.setEnabled(not running)
        self._run_btn.setVisible(not running)
        self._stop_btn.setEnabled(running)
        self._stop_btn.setVisible(running)
        self._progress.setVisible(running)
        if not running:
            self._progress.setValue(0)

    def set_progress(self, current: int, total: int):
        if total > 0:
            self._progress.setMaximum(total)
            self._progress.setValue(current)
