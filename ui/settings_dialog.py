# ui/settings_dialog.py
"""
Settings dialog: tray behavior, notifications, and system info.
"""

from typing import Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QCheckBox, QGroupBox, QFormLayout, QFrame,
)
from PySide6.QtCore import Qt

from ui.theme import THEME
from utils.app_settings import AppSettings, DEFAULTS


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: AppSettings,
        hotkey_available: bool = False,
        registered_hotkeys: list | None = None,
        workflow_count: int = 0,
        save_path: str = "",
        hotkey_backend: str = "",
        game_hotkey_hint: str = "",
        parent=None,
        **_,
    ):
        super().__init__(parent)
        self._settings = settings
        self._extra = {
            "hotkey_backend": hotkey_backend,
            "game_hotkey_hint": game_hotkey_hint,
        }
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME['bg_panel']};
            }}
            QGroupBox {{
                color: {THEME['text_primary']};
                font-weight: 600;
                font-size: 12px;
                border: 1px solid {THEME['border']};
                border-radius: 8px;
                margin-top: 14px;
                padding: 16px 12px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {THEME['text_secondary']};
            }}
            QCheckBox {{
                color: {THEME['text_primary']};
                spacing: 10px;
                font-size: 13px;
            }}
            QLabel {{
                color: {THEME['text_secondary']};
                font-size: 12px;
                background: transparent;
            }}
        """)

        self._checks: Dict[str, QCheckBox] = {}
        self._build_ui(
            hotkey_available,
            registered_hotkeys or [],
            workflow_count,
            save_path,
        )

    def _build_ui(self, hotkey_ok, hotkeys, wf_count, save_path):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        title = QLabel("FlowMatic Settings")
        title.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Configure background operation and notifications.")
        subtitle.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 12px;")
        layout.addWidget(subtitle)

        tray_box = QGroupBox("System Tray")
        tray_layout = QVBoxLayout(tray_box)
        tray_layout.setSpacing(10)

        for key, label in (
            ("show_tray_icon", "Show icon in system tray"),
            ("minimize_to_tray_on_close", "Closing the window keeps FlowMatic running in the tray"),
            ("minimize_to_tray_on_minimize", "Minimize button sends the app to the tray"),
            ("start_in_tray", "Start FlowMatic hidden in the tray (next launch)"),
            ("show_tray_notifications", "Show notifications when workflows finish"),
            ("reopen_last_file", "Reopen the last workflow file on startup"),
        ):
            chk = QCheckBox(label)
            chk.setChecked(bool(self._settings.get(key)))
            self._checks[key] = chk
            tray_layout.addWidget(chk)

        hint = QLabel(
            "Tip: With tray enabled, hotkeys keep working while the window is hidden."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 11px; padding-top: 4px;")
        tray_layout.addWidget(hint)
        layout.addWidget(tray_box)

        info_box = QGroupBox("System")
        info_form = QFormLayout(info_box)
        info_form.setSpacing(8)
        backend = self._extra.get("hotkey_backend", "")
        hotkey_line = (
            f"Available ({backend})" if hotkey_ok else "Not available"
        )
        info_form.addRow("Hotkeys:", QLabel(hotkey_line))
        game_hint = self._extra.get("game_hotkey_hint", "")
        if game_hint:
            hint_lbl = QLabel(game_hint)
            hint_lbl.setWordWrap(True)
            hint_lbl.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")
            info_form.addRow("", hint_lbl)
        info_form.addRow("Registered:", QLabel(
            ", ".join(hotkeys) if hotkeys else "(none)"
        ))
        info_form.addRow("Workflows:", QLabel(str(wf_count)))
        info_form.addRow("Save file:", QLabel(save_path or "Not set"))
        layout.addWidget(info_box)

        layout.addStretch()

        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(34)
        cancel.clicked.connect(self.reject)

        save = QPushButton("Save")
        save.setFixedHeight(34)
        save.setObjectName("btn_primary")
        save.clicked.connect(self._save_and_accept)

        row_lay.addWidget(cancel)
        row_lay.addWidget(save)
        layout.addWidget(row)

    def _save_and_accept(self):
        data = {key: chk.isChecked() for key, chk in self._checks.items()}
        self._settings.apply_dict(data)
        self._settings.save()
        self.accept()

    @staticmethod
    def open_settings(parent, settings: AppSettings, **kwargs) -> bool:
        dlg = SettingsDialog(settings, parent=parent, **kwargs)
        return dlg.exec() == QDialog.Accepted
