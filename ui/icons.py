# ui/icons.py
"""
Vector icons drawn with QPainter — no emoji dependencies.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QIcon
from PySide6.QtWidgets import QWidget, QAbstractButton, QVBoxLayout
from PySide6.QtCore import QSize


def _pen(color: str, width: float = 1.8) -> QPen:
    return QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)


def paint_icon(painter: QPainter, key: str, rect: QRectF, color: str):
    """Draw an icon into rect using the given accent color."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)

    cx, cy = rect.center().x(), rect.center().y()
    s = min(rect.width(), rect.height())
    pad = s * 0.18

    if key == "play":
        p = QPen(Qt.NoPen)
        painter.setPen(p)
        painter.setBrush(QBrush(QColor(color)))
        tri = [
            QPointF(rect.left() + pad, rect.top() + pad),
            QPointF(rect.left() + pad, rect.bottom() - pad),
            QPointF(rect.right() - pad * 0.6, cy),
        ]
        painter.drawPolygon(tri)

    elif key == "stop":
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        inner = rect.adjusted(pad, pad, -pad, -pad)
        painter.drawRoundedRect(inner, 2, 2)

    elif key == "close":
        painter.setPen(_pen(color, 2.2))
        m = pad * 0.6
        painter.drawLine(rect.left() + m, rect.top() + m, rect.right() - m, rect.bottom() - m)
        painter.drawLine(rect.right() - m, rect.top() + m, rect.left() + m, rect.bottom() - m)

    elif key == "eye":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - s * 0.34, cy - s * 0.2, s * 0.68, s * 0.4))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QRectF(cx - s * 0.1, cy - s * 0.1, s * 0.2, s * 0.2))

    elif key == "window_hide":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        body = rect.adjusted(pad, pad * 1.4, -pad, -pad)
        painter.drawRoundedRect(body, 2, 2)
        bar = QRectF(body.left(), body.top() - pad * 0.5, body.width(), pad * 0.9)
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar, 1.5, 1.5)

    elif key == "clock":
        painter.setPen(_pen(color, 1.6))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect.adjusted(pad, pad, -pad, -pad))
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - s * 0.22))
        painter.drawLine(QPointF(cx, cy), QPointF(cx + s * 0.18, cy + s * 0.06))

    elif key == "diamond":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        d = [
            QPointF(cx, rect.top() + pad),
            QPointF(rect.right() - pad, cy),
            QPointF(cx, rect.bottom() - pad),
            QPointF(rect.left() + pad, cy),
        ]
        painter.drawPolygon(d)

    elif key == "save":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        tray = QRectF(cx - s * 0.28, cy + s * 0.08, s * 0.56, s * 0.22)
        painter.drawRoundedRect(tray, 2, 2)
        painter.drawLine(QPointF(cx, rect.top() + pad), QPointF(cx, cy + s * 0.04))
        painter.drawLine(QPointF(cx - s * 0.14, rect.top() + pad + s * 0.1), QPointF(cx, rect.top() + pad))
        painter.drawLine(QPointF(cx + s * 0.14, rect.top() + pad + s * 0.1), QPointF(cx, rect.top() + pad))

    elif key == "load":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        tray = QRectF(cx - s * 0.28, rect.top() + pad, s * 0.56, s * 0.22)
        painter.drawRoundedRect(tray, 2, 2)
        painter.drawLine(QPointF(cx, rect.bottom() - pad), QPointF(cx, rect.top() + pad + s * 0.18))
        painter.drawLine(QPointF(cx - s * 0.14, rect.top() + pad + s * 0.32), QPointF(cx, rect.top() + pad + s * 0.18))
        painter.drawLine(QPointF(cx + s * 0.14, rect.top() + pad + s * 0.32), QPointF(cx, rect.top() + pad + s * 0.18))

    elif key == "settings":
        painter.setPen(_pen(color, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - s * 0.12, cy - s * 0.12, s * 0.24, s * 0.24))
        for i in range(8):
            angle = i * 45
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(angle)
            painter.drawLine(QPointF(s * 0.2, 0), QPointF(s * 0.36, 0))
            painter.restore()

    elif key == "flowmatic":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        r = s * 0.36
        for i in range(6):
            angle = 60 * i - 30
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(angle)
            painter.drawLine(QPointF(0, -r), QPointF(0, -r * 0.55))
            painter.restore()

    elif key == "drag_grip":
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        dot = s * 0.1
        gap = s * 0.2
        for row in range(3):
            for col in range(2):
                x = rect.left() + pad + col * gap
                y = rect.top() + pad + row * gap
                painter.drawEllipse(QRectF(x, y, dot, dot))

    elif key == "plus":
        painter.setPen(_pen(color, 2.0))
        painter.drawLine(QPointF(cx, rect.top() + pad), QPointF(cx, rect.bottom() - pad))
        painter.drawLine(QPointF(rect.left() + pad, cy), QPointF(rect.right() - pad, cy))

    elif key == "menu":
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        dot = s * 0.11
        gap = s * 0.2
        for i in range(3):
            y = rect.top() + pad + i * gap
            painter.drawEllipse(QRectF(cx - dot / 2, y, dot, dot))

    elif key == "dot":
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        d = s * 0.28
        painter.drawEllipse(QRectF(cx - d / 2, cy - d / 2, d, d))

    elif key == "record":
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        d = s * 0.42
        painter.drawEllipse(QRectF(cx - d / 2, cy - d / 2, d, d))

    elif key == "log":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(pad, pad, -pad, -pad * 1.2), 2, 2)
        painter.drawLine(QPointF(rect.left() + pad * 1.2, cy), QPointF(rect.right() - pad * 1.2, cy))

    elif key == "trash":
        painter.setPen(_pen(color, 1.6))
        painter.setBrush(Qt.NoBrush)
        lid = QRectF(cx - s * 0.22, rect.top() + pad, s * 0.44, s * 0.1)
        painter.drawRoundedRect(lid, 1, 1)
        painter.drawLine(QPointF(cx - s * 0.12, rect.top() + pad), QPointF(cx + s * 0.12, rect.top() + pad))
        body = QRectF(cx - s * 0.18, rect.top() + pad + s * 0.12, s * 0.36, s * 0.48)
        painter.drawRoundedRect(body, 2, 2)
        painter.drawLine(QPointF(cx - s * 0.06, body.top() + s * 0.12), QPointF(cx - s * 0.06, body.bottom() - s * 0.08))
        painter.drawLine(QPointF(cx + s * 0.06, body.top() + s * 0.12), QPointF(cx + s * 0.06, body.bottom() - s * 0.08))

    elif key == "keyboard":
        painter.setPen(_pen(color, 1.5))
        painter.setBrush(Qt.NoBrush)
        body = rect.adjusted(pad * 0.7, pad * 1.5, -pad * 0.7, -pad * 1.5)
        painter.drawRoundedRect(body, 2, 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        dot = s * 0.07
        gap = body.width() / 5
        for col in range(4):
            x = body.left() + gap * (col + 1) - dot / 2
            y = body.top() + body.height() * 0.26
            painter.drawEllipse(QRectF(x, y, dot, dot))
        bar = QRectF(
            body.left() + body.width() * 0.2,
            body.top() + body.height() * 0.62,
            body.width() * 0.6, s * 0.06,
        )
        painter.drawRoundedRect(bar, 1, 1)

    elif key == "globe":
        painter.setPen(_pen(color, 1.6))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect.adjusted(pad, pad, -pad, -pad))
        painter.drawEllipse(QRectF(cx - s * 0.16, rect.top() + pad, s * 0.32, s - pad * 2))
        painter.drawLine(QPointF(rect.left() + pad, cy), QPointF(rect.right() - pad, cy))

    elif key == "loop":
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        box = rect.adjusted(pad * 0.8, pad * 0.8, -pad * 0.8, -pad * 0.8)
        r = box.width() / 2
        painter.drawArc(box, 210 * 16, 300 * 16)
        # Arrowhead at the arc end (150°), pointing along the tangent
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        h = s * 0.16
        ex = cx + r * -0.866   # cos 150°
        ey = cy - r * 0.5      # sin 150° (Qt y axis points down)
        tip = QPointF(ex - h * 0.5, ey + h * 0.866)
        b1 = QPointF(ex - h * 0.52, ey - h * 0.30)
        b2 = QPointF(ex + h * 0.52, ey + h * 0.30)
        painter.drawPolygon([tip, b1, b2])

    elif key == "bell":
        painter.setPen(_pen(color, 1.7))
        painter.setBrush(Qt.NoBrush)
        top = rect.top() + pad * 1.2
        dome = QRectF(cx - s * 0.20, top, s * 0.40, s * 0.34)
        painter.drawArc(dome, 0, 180 * 16)
        base_y = rect.bottom() - pad * 1.5
        painter.drawLine(QPointF(cx - s * 0.20, top + s * 0.17), QPointF(cx - s * 0.30, base_y))
        painter.drawLine(QPointF(cx + s * 0.20, top + s * 0.17), QPointF(cx + s * 0.30, base_y))
        painter.drawLine(QPointF(cx - s * 0.30, base_y), QPointF(cx + s * 0.30, base_y))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color)))
        d = s * 0.10
        painter.drawEllipse(QRectF(cx - d / 2, rect.bottom() - pad * 1.2, d, d))

    else:
        painter.setPen(_pen(color, 1.8))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(pad, pad, -pad, -pad), 3, 3)

    painter.restore()


def make_pixmap(key: str, color: str, size: int = 20) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    paint_icon(painter, key, QRectF(0, 0, size, size), color)
    painter.end()
    return pixmap


def make_icon(key: str, color: str, size: int = 20) -> QIcon:
    return QIcon(make_pixmap(key, color, size))


class IconLabel(QWidget):
    """Small widget that paints a vector icon."""

    def __init__(self, icon_key: str, color: str, size: int = 24, parent=None):
        super().__init__(parent)
        self.icon_key = icon_key
        self.color = color
        self._size = size
        self.setFixedSize(size, size)

    def set_color(self, color: str):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        paint_icon(painter, self.icon_key, QRectF(0, 0, self._size, self._size), self.color)


def icon_container(icon_key: str, color: str, size: int = 28) -> QWidget:
    """Icon inside a tinted rounded square (palette / properties)."""
    wrap = QWidget()
    wrap.setFixedSize(size, size)
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(6, 6, 6, 6)
    icon = IconLabel(icon_key, color, size - 12)
    lay.addWidget(icon, alignment=Qt.AlignCenter)
    wrap.setStyleSheet(f"""
        background: {color}22;
        border: 1px solid {color}55;
        border-radius: 6px;
    """)
    return wrap


def set_button_icon(btn: QAbstractButton, icon_key: str, color: str, icon_size: int = 16):
    btn.setIcon(make_icon(icon_key, color, icon_size))
    btn.setIconSize(QSize(icon_size, icon_size))


def make_app_icon() -> QIcon:
    """Multi-size icon for window and system tray."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        margin = max(1, size // 10)
        bg = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#1A2332")))
        painter.drawRoundedRect(bg, size * 0.22, size * 0.22)
        inner = QRectF(margin + 2, margin + 2, size - 2 * margin - 4, size - 2 * margin - 4)
        paint_icon(painter, "flowmatic", inner, "#4A90D9")
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def action_icon_key(action) -> str:
    return getattr(action, "ACTION_ICON_KEY", "gear")
