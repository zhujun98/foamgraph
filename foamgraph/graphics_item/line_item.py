"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod

from ..backend.QtGui import QPainterPath, QPen, QPolygonF, QTransform
from ..backend.QtCore import pyqtSignal, QPointF, QRectF, Qt

from ..aesthetics import FColor
from ..utility import normalize_angle
from ..graphics_scene import HoverEvent, MouseDragEvent
from .graphics_item import GraphicsObject


class InfiniteLineItem(GraphicsObject):
    """A line of infinite length."""

    position_changed_sgn = pyqtSignal()

    def __init__(self, pos: QPointF = QPointF(0, 0), *, parent=None):
        """Initialization.

        :param pos: (x, y) position of the line.
        """
        super().__init__(parent=parent)

        self._p1 = None
        self._p2 = None
        self._bounding_rect = None
        self._selection_radius = 0

        self._moving = False
        self._cursor_offset = 0
        self._mouse_hovering = False

        self.setPos(pos)

        self.setDraggable(True)

        self._pen = None
        self.setPen(FColor.mkPen('k'))
        self._hover_pen = None
        self.setHoverPen(FColor.mkPen('w'))

    def p1(self) -> QPointF:
        if self._p1 is None:
            self._prepareGraph()
        return self._p1

    def p2(self) -> QPointF:
        if self._p2 is None:
            self._prepareGraph()
        return self._p2

    def setDraggable(self, state: bool) -> None:
        self.setAcceptHoverEvents(state)

    def setPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI."""
        self._pen = pen
        self.update()

    def setHoverPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI when mouse is hovering."""
        self._hover_pen = pen
        self.update()

    @abstractmethod
    def _prepareGraph(self):
        raise NotImplementedError

    def updateGraph(self) -> None:
        self._bounding_rect = None
        self._p1 = None
        self._p2 = None
        self.prepareGeometryChange()

    def setPos(self, pos: QPointF) -> None:
        """Override."""
        super().setPos(pos)
        self.updateGraph()
        self.position_changed_sgn.emit()

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._bounding_rect is None:
            self._prepareGraph()
        return self._bounding_rect

    def paint(self, p, *args) -> None:
        """Override."""
        p.setRenderHint(p.RenderHint.Antialiasing)
        if self.acceptHoverEvents() and self._mouse_hovering:
            pen = self._hover_pen
        else:
            pen = self._pen
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        p.setPen(pen)
        p.drawLine(self._p1, self._p2)

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()

        if ev.entering():
            self._moving = True
            self._cursor_offset = self.pos() - self.mapToParent(ev.buttonDownPos())
        elif ev.exiting():
            self._moving = False
            self._cursor_offset = 0

        if self._moving:
            self.setPos(self._cursor_offset + self.mapToParent(ev.pos()))

    def hoverEvent(self, ev: HoverEvent) -> None:
        hovering = False
        if not ev.isExit():
            if ev.acceptDrags(Qt.MouseButton.LeftButton):
                hovering = True

        if self._mouse_hovering == hovering:
            return
        self._mouse_hovering = hovering
        self.update()


class InfiniteVLineItem(InfiniteLineItem):
    def __init__(self, x: float = 0, *, parent=None):
        super().__init__(QPointF(x, 0), parent=parent)

    def _prepareGraph(self):
        """Override."""
        vr = self.viewRect()
        if vr is None:
            self._bounding_rect = QRectF()
            self._p1 = QPointF()
            self._p2 = QPointF()
            return

        self._bounding_rect = QRectF(
            self.x() - self._selection_radius, vr.top(),
            2 * self._selection_radius, vr.height()
        )
        self._p1 = QPointF(self.x(), vr.top())
        self._p2 = QPointF(self.x(), vr.bottom())


class InfiniteHLineItem(InfiniteLineItem):
    def __init__(self, y: float = 0, *, parent=None):
        super().__init__(QPointF(0, y), parent=parent)

    def _prepareGraph(self):
        vr = self.viewRect()
        if vr is None:
            self._bounding_rect = QRectF()
            return

        self._bounding_rect = QRectF(
            vr.left(), self.y() - self._selection_radius,
            vr.width(), 2 * self._selection_radius
        )
        self._p1 = QPointF(vr.left(), self.y())
        self._p2 = QPointF(vr.right(), self.y())
