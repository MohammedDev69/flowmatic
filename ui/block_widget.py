# ui/block_widget.py
"""
BlockWidget: Visual representation of a single action block.
Supports drag-and-drop, selection highlighting, and context menus.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QToolButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QSize, QRect
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QDrag, QCursor,
    QLinearGradient, QFont, QPixmap
)

from actions.base_action import BaseAction
from ui.theme import THEME
from ui.icons import IconLabel, action_icon_key, set_button_icon


class BlockWidget(QWidget):
    """
    Visual card representing a single action in the workflow.
    
    Features:
    - Color-coded by action type
    - Shows icon, label, and current configuration summary
    - Drag handle for reordering
    - Selected/running/error visual states
    """

    clicked = Signal(str)          # action_id
    delete_requested = Signal(str) # action_id
    move_up_requested = Signal(str)
    move_down_requested = Signal(str)

    STATE_IDLE = "idle"
    STATE_RUNNING = "running"
    STATE_SUCCESS = "success"
    STATE_ERROR = "error"
    STATE_SKIP = "skip"
    STATE_DISABLED = "disabled"

    def __init__(self, action: BaseAction, parent=None):
        super().__init__(parent)
        self.action = action
        self._selected = False
        self._state = self.STATE_IDLE
        self._drag_start_pos = None

        self.setFixedHeight(68)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setAcceptDrops(False)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._build_ui()
        self._apply_state()

        # Tooltip
        self.setToolTip(f"{action.ACTION_LABEL}\n{action.ACTION_DESCRIPTION}")

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Color accent bar ──────────────────────────────────────────────
        self._accent = QWidget()
        self._accent.setFixedWidth(5)
        self._accent.setStyleSheet(
            f"background: {self.action.ACTION_COLOR}; border-radius: 0px;"
        )

        # ── Main content ──────────────────────────────────────────────────
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(12, 8, 8, 8)
        content_layout.setSpacing(10)

        icon_wrap = QWidget()
        icon_wrap.setFixedSize(40, 40)
        icon_lay = QHBoxLayout(icon_wrap)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        icon_lay.setAlignment(Qt.AlignCenter)
        self._icon_label = IconLabel(action_icon_key(self.action), self.action.ACTION_COLOR, 22)
        icon_wrap.setStyleSheet(f"""
            background: {self.action.ACTION_COLOR}18;
            border: 1px solid {self.action.ACTION_COLOR}45;
            border-radius: 20px;
        """)
        icon_lay.addWidget(self._icon_label)

        # Text block
        text_block = QWidget()
        text_layout = QVBoxLayout(text_block)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._title_label = QLabel(self.action.ACTION_LABEL)
        self._title_label.setStyleSheet(f"""
            color: {THEME['text_primary']};
            font-size: 13px;
            font-weight: 600;
        """)

        self._summary_label = QLabel(self.action.get_summary())
        self._summary_label.setStyleSheet(f"""
            color: {THEME['text_secondary']};
            font-size: 11px;
        """)

        text_layout.addWidget(self._title_label)
        text_layout.addWidget(self._summary_label)

        self._state_dot = IconLabel("dot", THEME['text_muted'], 10)

        self._delete_btn = QToolButton()
        self._delete_btn.setFixedSize(30, 30)
        self._delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._delete_btn.setToolTip("Delete block")
        self._delete_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        set_button_icon(self._delete_btn, "trash", THEME['text_muted'], 15)
        self._delete_btn.setStyleSheet(f"""
            QToolButton {{
                background: {THEME['bg_input']};
                border: 1px solid {THEME['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QToolButton:hover {{
                background: {THEME['accent_red']}22;
                border-color: {THEME['accent_red']}88;
            }}
            QToolButton:pressed {{
                background: {THEME['accent_red']}44;
            }}
        """)
        self._delete_btn.setVisible(False)
        self._delete_btn.clicked.connect(self._on_delete_clicked)

        content_layout.addWidget(icon_wrap)
        content_layout.addWidget(text_block, 1)
        content_layout.addWidget(self._state_dot)
        content_layout.addWidget(self._delete_btn)

        layout.addWidget(self._accent)
        layout.addWidget(content, 1)

    def _on_delete_clicked(self):
        self.delete_requested.emit(self.action.id)

    def _update_delete_icon(self, hovered: bool):
        color = THEME['accent_red'] if hovered else THEME['text_muted']
        set_button_icon(self._delete_btn, "trash", color, 15)

    def refresh_summary(self):
        """Update the summary text after params change."""
        self._summary_label.setText(self.action.get_summary())
        # Disabled style
        if not self.action.enabled:
            self.set_state(self.STATE_DISABLED)
        elif self._state == self.STATE_DISABLED:
            self.set_state(self.STATE_IDLE)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_state()

    def set_state(self, state: str):
        self._state = state
        self._apply_state()

    def _apply_state(self):
        """Apply visual style based on current state and selection."""
        t = THEME
        border_color = t['border']
        bg_color = t['bg_card']
        dot_color = t['text_muted']

        if self._selected:
            border_color = t['accent_blue']
            bg_color = t['bg_selected']

        if self._state == self.STATE_RUNNING:
            border_color = t['accent_orange']
            dot_color = t['accent_orange']
        elif self._state == self.STATE_SUCCESS:
            border_color = t['accent_green']
            dot_color = t['accent_green']
        elif self._state == self.STATE_ERROR:
            border_color = t['accent_red']
            dot_color = t['accent_red']
        elif self._state == self.STATE_SKIP:
            dot_color = t['text_muted']
            bg_color = t['bg_panel']
        elif self._state == self.STATE_DISABLED:
            bg_color = t['bg_panel']

        self.setStyleSheet(f"""
            BlockWidget {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)
        self._state_dot.set_color(dot_color)

    # ── Events ────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            btn_rect = QRect(
                self._delete_btn.mapTo(self, QPoint(0, 0)),
                self._delete_btn.size(),
            )
            if not btn_rect.contains(event.pos()):
                self._drag_start_pos = event.pos()
                self.clicked.emit(self.action.id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        # Initiate drag
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.action.id)
        mime.setData("application/x-flowmatic-block", self.action.id.encode())
        drag.setMimeData(mime)

        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(pixmap.width(), pixmap.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        drag.setHotSpot(event.pos())

        drag.exec(Qt.MoveAction)

    def enterEvent(self, event):
        self._delete_btn.setVisible(True)
        self._update_delete_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._delete_btn.setVisible(False)
        self._update_delete_icon(False)
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        move_up = menu.addAction("Move Up")
        move_down = menu.addAction("Move Down")
        menu.addSeparator()
        toggle = menu.addAction("Disable" if self.action.enabled else "Enable")
        menu.addSeparator()
        delete = menu.addAction("Delete Block")

        action = menu.exec(event.globalPos())
        if action == move_up:
            self.move_up_requested.emit(self.action.id)
        elif action == move_down:
            self.move_down_requested.emit(self.action.id)
        elif action == toggle:
            self.action.enabled = not self.action.enabled
            self.refresh_summary()
        elif action == delete:
            self.delete_requested.emit(self.action.id)
