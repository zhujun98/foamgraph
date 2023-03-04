from ..backend.QtCore import QRectF
from ..backend.QtWidgets import QGraphicsObject

from .line_item import InfiniteHorizontalLineItem, InfiniteVerticalLineItem


class CrossCursorItem(QGraphicsObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._v_line = InfiniteVerticalLineItem(parent=self)
        self._v_line.setDraggable(False)
        self._h_line = InfiniteHorizontalLineItem(parent=self)
        self._h_line.setDraggable(False)

    def setPos(self, x: float, y: float) -> None:
        """Override."""
        self._v_line.setValue(x)
        self._h_line.setValue(y)

    def boundingRect(self) -> None:
        """Override."""
        return QRectF()

    def paint(self, p, *args) -> None:
        """Override."""
        ...
