# ui/palette_panel.py
"""
PalettePanel: Left panel showing available action types.
Each item can be dragged onto the canvas to create a new block.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QSizePolicy, QHBoxLayout
)
from PySide6.QtCore import Qt, QMimeData, QSize
from PySide6.QtGui import QDrag, QCursor, QColor

from typing import Type, List
from actions.base_action import BaseAction
from core.registry import ActionRegistry
from ui.theme import THEME
from ui.icons import icon_container, IconLabel


class PaletteItem(QWidget):
    """
    A draggable block type tile in the action palette.
    """

    def __init__(self, action_class: Type[BaseAction], parent=None):
        super().__init__(parent)
        self.action_class = action_class
        self._drag_start = None

        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setToolTip(f"{action_class.ACTION_LABEL}\n{action_class.ACTION_DESCRIPTION}\n\nDrag to add to workflow")

        self._build_ui()
        self.setStyleSheet(f"""
            PaletteItem {{
                background: {THEME['bg_card']};
                border: 1px solid {THEME['border']};
                border-left: 3px solid {action_class.ACTION_COLOR};
                border-radius: 6px;
            }}
            PaletteItem:hover {{
                background: {THEME['bg_hover']};
                border-color: {action_class.ACTION_COLOR}80;
            }}
        """)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        icon = icon_container(
            self.action_class.ACTION_ICON_KEY,
            self.action_class.ACTION_COLOR,
            32,
        )

        # Text
        text_block = QWidget()
        text_layout = QVBoxLayout(text_block)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        title = QLabel(self.action_class.ACTION_LABEL)
        title.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 12px; font-weight: 600;")

        desc = QLabel(self.action_class.ACTION_DESCRIPTION[:38] + ("…" if len(self.action_class.ACTION_DESCRIPTION) > 38 else ""))
        desc.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")

        text_layout.addWidget(title)
        text_layout.addWidget(desc)

        drag_hint = IconLabel("drag_grip", THEME['text_muted'], 18)

        layout.addWidget(icon)
        layout.addWidget(text_block, 1)
        layout.addWidget(drag_hint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self._drag_start:
            return
        if (event.pos() - self._drag_start).manhattanLength() < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.action_class.ACTION_TYPE)
        mime.setData("application/x-flowmatic-new", self.action_class.ACTION_TYPE.encode())
        drag.setMimeData(mime)

        # Drag preview
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        drag.exec(Qt.CopyAction)


class PalettePanel(QWidget):
    """
    Left panel containing categorized action palette items.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self.setStyleSheet(f"background: {THEME['bg_panel']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background: {THEME['bg_panel']}; border-bottom: 1px solid {THEME['border']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("Actions")
        title.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)

        count_label = QLabel(f"{len(ActionRegistry.get_all())} blocks")
        count_label.setStyleSheet(f"""
            color: {THEME['text_muted']};
            font-size: 11px;
            background: {THEME['bg_card']};
            border: 1px solid {THEME['border']};
            border-radius: 10px;
            padding: 2px 8px;
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(count_label)
        layout.addWidget(header)

        # ── Scrollable list ──────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {THEME['bg_panel']}; border: none;")

        inner = QWidget()
        inner.setStyleSheet(f"background: {THEME['bg_panel']};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(10, 12, 10, 12)
        inner_layout.setSpacing(4)

        # Group by category
        categories = {
            "Programs": ["open_program", "close_program"],
            "Windows": ["show_window", "hide_window"],
            "Input": ["send_keys"],
            "Web": ["http_request"],
            "Control": ["wait", "condition", "loop"],
            "Alerts": ["notify"],
        }

        action_map = {klass.ACTION_TYPE: klass for klass in ActionRegistry.get_all()}

        for category, types in categories.items():
            # Category label
            cat_label = QLabel(category.upper())
            cat_label.setStyleSheet(f"""
                color: {THEME['text_muted']};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1.5px;
                padding: 8px 4px 4px 4px;
            """)
            inner_layout.addWidget(cat_label)

            for atype in types:
                if atype in action_map:
                    item = PaletteItem(action_map[atype])
                    inner_layout.addWidget(item)

        inner_layout.addStretch()

        # Hint at the bottom
        hint = QLabel("Drag blocks to the canvas")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            color: {THEME['text_muted']};
            font-size: 10px;
            padding: 16px 8px;
            border-top: 1px solid {THEME['border']};
        """)
        inner_layout.addWidget(hint)

        scroll.setWidget(inner)
        layout.addWidget(scroll)
