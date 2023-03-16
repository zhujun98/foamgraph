"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from enum import IntEnum

from ..backend.QtCore import QPointF, QRectF
from ..backend.QtGui import QPen
from ..backend.QtWidgets import (
    QGraphicsLineItem, QGraphicsObject, QGraphicsTextItem
)
from ..config import config


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
        return QRectF(0, 0, 100, 100)

    def paint(self, p, *args) -> None:
        """Override."""
        ...


class FiniteLineMouseCursorItem(MouseCursorItem):
    """A mouse cursor item with a finite-line-cross as the cursor."""
    def __init__(self, length: float = 10, *, parent=None):
        super().__init__(parent=parent)

        hl = length / 2
        self._v_line = QGraphicsLineItem(0, -hl, 0, hl, parent=self)
        self._h_line = QGraphicsLineItem(-hl, 0, hl, 0, parent=self)

    # def setPos(self, pos: QPointF) -> None:
    #     """Override."""
    #     super().setPos(pos)
    #     print(pos)
    #     pos = self.mapFromParent(pos)
    #     print(pos)
    #     self._label.setPos(pos)
    #
    #     hl = self._length / 2
    #     self._v_line.setLine(pos.x(), pos.y() - hl, pos.x(), pos.y() + hl)
    #     self._h_line.setLine(pos.x() - hl, pos.y(), pos.x() + hl, pos.y())

    def setPen(self, pen: QPen) -> None:
        """Override."""
        super().setPen(pen)
        self._v_line.setPen(pen)
        self._h_line.setPen(pen)


class InfiniteLineMouseCursorItem(MouseCursorItem):
    """A mouse cursor item with an infinite-line-cross as the cursor."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        w, h = config["SCREEN_GEOMETRY"]
        self._v_line = QGraphicsLineItem(0, -h, 0, h, parent=self)
        self._h_line = QGraphicsLineItem(-w, 0, w, 0, parent=self)

    def setPen(self, pen: QPen) -> None:
        """Override."""
        super().setPen(pen)
        self._v_line.setPen(pen)
        self._h_line.setPen(pen)
