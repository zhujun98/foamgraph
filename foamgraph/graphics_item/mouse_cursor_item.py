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

from .line_item import InfiniteHLineItem, InfiniteVLineItem


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
        self._label.show()

        self._pen = None

        self._bounding_rect = None

    def setPos(self, pos: QPointF) -> None:
        """Override."""
        super().setPos(pos)
        pos = self.mapFromParent(pos)
        self._label.setPos(pos)

    def setLabel(self, text: str) -> None:
        self._label.setPlainText(text)

    def setPen(self, pen: QPen) -> None:
        self._pen = pen

    def updateBoundingRect(self) -> None:
        ...

    def boundingRect(self) -> None:
        """Override."""
        return QRectF()

    def paint(self, p, *args) -> None:
        """Override."""
        ...


class FiniteLineMouseCursorItem(MouseCursorItem):
    """A mouse cursor item with a finite-line-cross as the cursor."""
    def __init__(self, length: float = 10, *, parent=None):
        super().__init__(parent=parent)

        self._length = length
        self._v_line = QGraphicsLineItem(0, -1, 0, 1, parent=self)
        self._h_line = QGraphicsLineItem(-1, 0, 1, 0, parent=self)

    def setPos(self, pos: QPointF) -> None:
        """Override."""
        super().setPos(pos)
        pos = self.mapFromParent(pos)
        self._label.setPos(pos)
        self._v_line.setPos(pos)
        self._h_line.setPos(pos)

    def setPen(self, pen: QPen) -> None:
        """Override."""
        super().setPen(pen)
        self._v_line.setPen(pen)
        self._h_line.setPen(pen)

    def updateBoundingRect(self) -> None:
        """Override."""
        self._bounding_rect = None
        self.prepareGeometryChange()

    def boundingRect(self) -> None:
        """Override."""
        if self._bounding_rect is None:
            pos = self._label.pos()

            rect = self.mapRectToParent(self.mapRectFromScene(
                QRectF(0, 0, self._length, self._length)))

            hw, hh = rect.width() / 2., rect.height() / 2.
            self._v_line.setLine(pos.x(), pos.y() - hh, pos.x(), pos.y() + hh)
            self._h_line.setLine(pos.x() - hw, pos.y(), pos.x() + hw, pos.y())
            # we don't need the bounding_rect for now
            self._bounding_rect = QRectF()
        return self._bounding_rect


class InfiniteLineMouseCursorItem(MouseCursorItem):
    """A mouse cursor item with an infinite-line-cross as the cursor."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._v_line = InfiniteVLineItem(0, parent=self)
        self._v_line.setDraggable(False)
        self._h_line = InfiniteHLineItem(0, parent=self)
        self._h_line.setDraggable(False)

    def setPos(self, pos: QPointF) -> None:
        """Override."""
        super().setPos(pos)
        pos = self.mapFromParent(pos)
        self._label.setPos(pos)
        self._v_line.setPos(pos)
        self._h_line.setPos(pos)

    def setPen(self, pen: QPen) -> None:
        """Override."""
        super().setPen(pen)
        self._v_line.setPen(pen)
        self._h_line.setPen(pen)
