"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from enum import IntEnum

from ..backend.QtCore import QPointF, QRectF
from ..backend.QtGui import QGuiApplication, QPen
from ..backend.QtWidgets import (
    QGraphicsLineItem, QGraphicsObject, QGraphicsTextItem
)


class MouseCursorStyle(IntEnum):
    Simple = 0
    Cross = 1
    InfiniteCross = 2


class MouseCursorItem(QGraphicsObject):
    """A simple mouse cursor item with only the default mouse cursor."""
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._label = QGraphicsTextItem('', parent=self)
        self._label.setFlag(
            QGraphicsTextItem.GraphicsItemFlag.ItemIgnoresTransformations)

        self._pen = None

    def setLabel(self, text: str) -> None:
        self._label.setPlainText(text)

    def setPen(self, pen: QPen) -> None:
        self._pen = pen

    def boundingRect(self) -> None:
        """Override."""
        return QRectF()

    def paint(self, p, *args) -> None:
        """Override."""
        ...


class CrossMouseCursorItem(MouseCursorItem):
    """A mouse cursor item with a cross as the cursor."""
    def __init__(self, length: float = 10, *, parent=None):
        super().__init__(parent=parent)

        if length > 0:
            hh = hw = length / 2
        else:
            rect = QGuiApplication.primaryScreen().geometry()
            hw, hh = rect.width(), rect.height()

        self._v_line = QGraphicsLineItem(0, -hh, 0, hh, parent=self)
        self._h_line = QGraphicsLineItem(-hw, 0, hw, 0, parent=self)

    def setPen(self, pen: QPen) -> None:
        """Override."""
        super().setPen(pen)
        self._v_line.setPen(pen)
        self._h_line.setPen(pen)
