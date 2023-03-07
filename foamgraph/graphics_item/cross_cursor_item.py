"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtCore import QPointF, QRectF
from ..backend.QtGui import QPen
from ..backend.QtWidgets import QGraphicsObject, QGraphicsTextItem

from .line_item import InfiniteHLineItem, InfiniteVLineItem


class CrossCursorItem(QGraphicsObject):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)
        self._v_line = InfiniteVLineItem(0, parent=self)
        self._v_line.setDraggable(False)
        self._h_line = InfiniteHLineItem(0, parent=self)
        self._h_line.setDraggable(False)

        self._label = QGraphicsTextItem('', parent=self)
        self._label.show()

    def setPos(self, pos: QPointF) -> None:
        """Override."""
        super().setPos(pos)
        pos = self.mapFromParent(pos)
        self._v_line.setPos(pos)
        self._h_line.setPos(pos)
        self._label.setPos(pos)

    def setLabel(self, x: float, y: float) -> None:
        self._label.setPlainText(f"{x}, {y}")

    def setPen(self, pen: QPen) -> None:
        self._v_line.setPen(pen)
        self._h_line.setPen(pen)

    def boundingRect(self) -> None:
        """Override."""
        return QRectF()

    def paint(self, p, *args) -> None:
        """Override."""
        ...
