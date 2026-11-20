# ui/workflow_canvas.py
"""
WorkflowCanvas: The central drag-and-drop area where blocks are arranged.
Supports reordering blocks via drag-and-drop.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QPainter, QColor

from typing import List, Optional

from actions.base_action import BaseAction
from ui.block_widget import BlockWidget
from ui.theme import THEME


class DropIndicator(QWidget):
    """A thin horizontal line showing where a block will be dropped."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(THEME['accent_blue']))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 1, 1)


class WorkflowCanvas(QScrollArea):
    """
    Scrollable area containing all workflow block widgets in order.
    Emits signals on block interaction.
    """

    block_clicked = Signal(str)      # action_id
    block_deleted = Signal(str)      # action_id
    block_moved = Signal(str, int)   # action_id, new_index
    drop_from_palette = Signal(str, int)  # action_type, insert_index
    selection_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"background: {THEME['bg_base']}; border: none;")

        # Inner container
        self._container = QWidget()
        self._container.setStyleSheet(f"background: {THEME['bg_base']};")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(16, 12, 16, 40)
        self._layout.setSpacing(6)
        self._layout.setAlignment(Qt.AlignTop)

        # Empty state placeholder
        self._empty_label = QLabel(
            "Drop action blocks here to build your workflow\n\n"
            "Drag blocks from the Actions panel on the left"
        )
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {THEME['text_muted']};
            font-size: 14px;
            line-height: 1.8;
            padding: 60px;
        """)
        self._layout.addWidget(self._empty_label)

        self.setWidget(self._container)

        # Track block widgets
        self._blocks: List[BlockWidget] = []
        self._selected_id: Optional[str] = None
        self._drop_indicator = DropIndicator(self._container)
        self._drop_target_index = -1

    # ── Block management ──────────────────────────────────────────────────────

    def add_block(self, action: BaseAction, index: Optional[int] = None) -> BlockWidget:
        """Create and insert a BlockWidget for the given action."""
        widget = BlockWidget(action)
        widget.clicked.connect(self._on_block_clicked)
        widget.delete_requested.connect(self.block_deleted)
        widget.move_up_requested.connect(self._on_move_up)
        widget.move_down_requested.connect(self._on_move_down)

        if index is None or index >= len(self._blocks):
            self._blocks.append(widget)
            self._layout.addWidget(widget)
        else:
            self._blocks.insert(index, widget)
            # Insert at correct position in layout (skip empty label)
            self._layout.insertWidget(index, widget)

        self._update_empty_state()
        return widget

    def remove_block(self, action_id: str):
        """Remove a block widget by action ID."""
        for w in self._blocks[:]:
            if w.action.id == action_id:
                self._blocks.remove(w)
                self._layout.removeWidget(w)
                w.deleteLater()
                if self._selected_id == action_id:
                    self._selected_id = None
                break
        self._update_empty_state()

    def clear_blocks(self):
        """Remove all block widgets."""
        for w in self._blocks[:]:
            self._layout.removeWidget(w)
            w.deleteLater()
        self._blocks.clear()
        self._selected_id = None
        self._update_empty_state()

    def get_block_widget(self, action_id: str) -> Optional[BlockWidget]:
        for w in self._blocks:
            if w.action.id == action_id:
                return w
        return None

    def refresh_block(self, action_id: str):
        """Refresh a block's summary display after params changed."""
        w = self.get_block_widget(action_id)
        if w:
            w.refresh_summary()

    def select_block(self, action_id: Optional[str]):
        """Select a block by ID, deselecting all others."""
        for w in self._blocks:
            w.set_selected(w.action.id == action_id)
        self._selected_id = action_id

    def set_block_state(self, action_id: str, state: str):
        w = self.get_block_widget(action_id)
        if w:
            w.set_state(state)

    def reset_all_states(self):
        for w in self._blocks:
            w.set_state(BlockWidget.STATE_IDLE)

    def _update_empty_state(self):
        self._empty_label.setVisible(len(self._blocks) == 0)

    def _on_block_clicked(self, action_id: str):
        self.select_block(action_id)
        self.block_clicked.emit(action_id)

    def _on_move_up(self, action_id: str):
        idx = next((i for i, w in enumerate(self._blocks) if w.action.id == action_id), -1)
        if idx > 0:
            self.block_moved.emit(action_id, idx - 1)

    def _on_move_down(self, action_id: str):
        idx = next((i for i, w in enumerate(self._blocks) if w.action.id == action_id), -1)
        if 0 <= idx < len(self._blocks) - 1:
            self.block_moved.emit(action_id, idx + 1)

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if (event.mimeData().hasFormat("application/x-flowmatic-block")
                or event.mimeData().hasFormat("application/x-flowmatic-new")):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if not (event.mimeData().hasFormat("application/x-flowmatic-block")
                or event.mimeData().hasFormat("application/x-flowmatic-new")):
            event.ignore()
            return

        # Calculate drop index
        pos = self.widget().mapFrom(self, event.position().toPoint())
        self._drop_target_index = self._index_at(pos.y())
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._drop_target_index = -1

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        pos = self.widget().mapFrom(self, event.position().toPoint())
        drop_index = self._index_at(pos.y())

        if mime.hasFormat("application/x-flowmatic-new"):
            # New block from palette
            action_type = mime.data("application/x-flowmatic-new").data().decode()
            self.drop_from_palette.emit(action_type, drop_index)
            event.acceptProposedAction()

        elif mime.hasFormat("application/x-flowmatic-block"):
            # Existing block being reordered
            action_id = mime.data("application/x-flowmatic-block").data().decode()
            self.block_moved.emit(action_id, drop_index)
            event.acceptProposedAction()

        self._drop_target_index = -1

    def _index_at(self, y: int) -> int:
        """Determine which insertion index corresponds to a y coordinate."""
        for i, w in enumerate(self._blocks):
            center_y = w.y() + w.height() // 2
            if y < center_y:
                return i
        return len(self._blocks)

    def mousePressEvent(self, event):
        # Click on empty area deselects
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            hit = self.childAt(event.pos())
            if hit is self._container or hit is None:
                self.select_block(None)
                self.selection_cleared.emit()
