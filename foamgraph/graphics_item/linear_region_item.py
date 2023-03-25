"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod
from enum import Enum

from ..backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from ..backend.QtGui import QBrush, QPen

from ..aesthetics import FColor
from ..graphics_scene import MouseDragEvent
from .graphics_item import GraphicsObject


class LinearRegionItem(GraphicsObject):
    """A horizontal or vertical region inbetween two lines."""
    region_changed_sgn = pyqtSignal()
    region_dragged_sgn = pyqtSignal()

    class Moving(Enum):
        NONE = 0
        BODY = 1
        TOP = 2
        BOTTOM = 3

    def __init__(self, p1: float, p2: float, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self._p1 = p1
        self._p2 = p2
        self._bounding_rect = None

        self._draggable = True
        self._edge_fraction = 0.3
        self._moving = self.Moving.NONE
        self._cursor_offset = 0

        self._pen = FColor.mkPen(None)
        self._brush = None
        self.setBrush(FColor.mkBrush("b", alpha=80))
        self._hover_brush = None
        self.setHoverBrush(FColor.mkBrush("b", alpha=40))

    def setBrush(self, brush: QBrush) -> None:
        """Set the QBrush used to fill the region."""
        self._brush = brush
        self.update()

    def setHoverBrush(self, brush: QBrush) -> None:
        """Set the QBrush used to fill the region when mouse is hovering."""
        self._hover_brush = brush
        self.update()

    def setDraggable(self, state: bool) -> None:
        self._draggable = state

    def region(self) -> tuple[float, float]:
        return self._p1, self._p2

    def setRegion(self, p1: float, p2: float) -> None:
        self._p1 = p1
        self._p2 = p2
        self._updateRegion()

    @abstractmethod
    def _pos(self, p: QPointF) -> float:
        ...

    def paint(self, p, *args) -> None:
        """Override."""
        p.setPen(self._pen)
        if self._moving == self.Moving.NONE:
            p.setBrush(self._brush)
        else:
            p.setBrush(self._hover_brush)
        rect = self.boundingRect()
        p.drawRect(rect)

    def _updateRegion(self) -> None:
        self._bounding_rect = None
        self.region_changed_sgn.emit()
        self.prepareGeometryChange()

    def _updateMovingState(self, p: float):
        delta = self._p2 - self._p1
        if p < self._p1 + self._edge_fraction * delta:
            self._moving = self.Moving.BOTTOM
        elif p > self._p1 + (1 - self._edge_fraction) * delta:
            self._moving = self.Moving.TOP
        else:
            self._moving = self.Moving.BODY

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if not self._draggable or ev.button() != Qt.MouseButton.LeftButton:
            return

        if ev.entering():
            p = self._pos(ev.buttonDownPos())
            self._updateMovingState(p)
            self._cursor_offset = [self._p1 - p, self._p2 - p]
            self.region_dragged_sgn.emit()

        if self._moving == self.Moving.NONE:
            return

        if self._moving != self._moving.TOP:
            self._p1 = self._cursor_offset[0] + self._pos(ev.pos())
        if self._moving != self._moving.BOTTOM:
            self._p2 = self._cursor_offset[1] + self._pos(ev.pos())

        if self._p1 > self._p2:
            self._p1, self._p2 = self._p2, self._p1
            self._cursor_offset.reverse()
            if self._moving == self._moving.TOP:
                self._moving = self._moving.BOTTOM
            else:
                self._moving = self._moving.TOP

        self._updateRegion()

        if ev.exiting():
            self._moving = self.Moving.NONE

        ev.accept()


class LinearHRegionItem(LinearRegionItem):

    def _pos(self, p):
        """Override."""
        return p.x()

    def boundingRect(self) -> QRectF:
        """Override."""
        parent = self.parentItem()
        if parent is None:
            return QRectF()

        if self._bounding_rect is None:
            rect = parent.boundingRect()
            self._bounding_rect = QRectF(
                self._p1, rect.top(), self._p2 - self._p1, rect.height)
            self.prepareGeometryChange()
        return self._bounding_rect


class LinearVRegionItem(LinearRegionItem):

    def _pos(self, p):
        """Override."""
        return p.y()

    def boundingRect(self) -> QRectF:
        """Override."""
        parent = self.parentItem()
        if parent is None:
            return QRectF()

        if self._bounding_rect is None:
            rect = parent.boundingRect()
            self._bounding_rect = QRectF(
                rect.left(), self._p1, rect.width(), self._p2 - self._p1)
            self.prepareGeometryChange()
        return self._bounding_rect
