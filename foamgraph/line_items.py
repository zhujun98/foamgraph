"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Union

from .backend.QtGui import QPainterPath, QPen, QPolygonF, QTransform
from .backend.QtCore import pyqtSignal, QPointF, QRectF, Qt

from . import pyqtgraph_be as pg
from .pyqtgraph_be.GraphicsScene import HoverEvent, MouseDragEvent
from .pyqtgraph_be import Point
from .aesthetics import FColor


class InfiniteLineItem(pg.GraphicsObject):
    """A line of infinite length."""

    position_change_finished_sgn = pyqtSignal(object)
    position_changed_sgn = pyqtSignal(object)

    def __init__(self, pos: Union[tuple, list, Point, QPointF], *,
                 angle: float = 0., draggable=True, parent=None):
        """Initialization.

        :param pos: (x, y) position of the line.
        :param angle: Rotation angle of the line. 0 for a horizontal line
            and 90 for a vertical one.
        :param draggable: Whether the line is draggable.
        """
        self._boundingRect = None

        super().__init__(parent=parent)

        self._moving = False
        self._cursor_offset = 0
        self._mouse_hovering = False

        self._pos = None
        self.setPos(pos)

        self._angle = None
        self.__setAngle(angle)

        self.setAcceptHoverEvents(draggable)

        self._pen = None
        self.setPen(FColor.mkPen('k'))
        self._hover_pen = None
        self.setHoverPen(FColor.mkPen('w'))

        # Cache variables for managing bounds
        self._endPoints = [0, 1]
        self._lastViewSize = None
        
    def setPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI."""
        self._pen = pen
        self.update()

    def setHoverPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI when mouse is hovering."""
        self._hover_pen = pen
        self.update()

    def setAngle(self, angle: float) -> None:
        self._angle = angle  # TODO: normalize
        self.resetTransform()
        self.setRotation(self._angle)
        self.update()

    __setAngle = setAngle

    def pos(self) -> Point:
        return self._pos

    def setPos(self, pos: Union[tuple, list, Point, QPointF]) -> None:
        self._pos = Point(pos)
        self._boundingRect = None
        super().setPos(self._pos)
        self.position_changed_sgn.emit(self)

    def _computeBoundingRect(self):
        vr = self.viewRect()  # bounds of containing ViewBox mapped to local coords.
        if vr is None:
            self._boundingRect = QRectF()
            return
        
        # add a 4-pixel radius around the line for mouse interaction.

        # get pixel length orthogonal to the line
        px = self.pixelLength(direction=Point(1,0), ortho=True)
        if px is None:
            px = 0
        w = 5 * px
        br = QRectF(vr)
        br.setBottom(-w)
        br.setTop(w)

        length = br.width()
        left = br.left()
        right = br.left() + length
        br.setLeft(left)
        br.setRight(right)
        br = br.normalized()
        
        vs = self.getViewBox().size()
        
        if self._boundingRect != br or self._lastViewSize != vs:
            self._boundingRect = br
            self._lastViewSize = vs
            self.prepareGeometryChange()
        
        self._endPoints = (left, right)
        self._lastViewRect = vr

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._boundingRect is None:
            self._computeBoundingRect()
        return self._boundingRect

    def paint(self, p, *args) -> None:
        """Override."""
        p.setRenderHint(p.RenderHint.Antialiasing)
        
        left, right = self._endPoints
        if self.acceptHoverEvents() and self._mouse_hovering:
            pen = self._hover_pen
        else:
            pen = self._pen
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        p.setPen(pen)
        p.drawLine(Point(left, 0), Point(right, 0))

    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        if axis == 0:
            return None   # x axis should never be auto-scaled
        return 0, 0

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
            self.position_change_finished_sgn.emit(self)

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


class InfiniteHorizontalLineItem(InfiniteLineItem):
    """A convenient class for creating a horizontal infinite line."""
    def __init__(self, pos: float = 0., **kwargs):
        """Initialization.

        :param pos: Position of the line.
        """
        if 'angle' in kwargs:
            raise ValueError("Cannot set the angle of a horizontal line")
        super().__init__((0., pos), angle=0., **kwargs)

    def setAngle(self, angle: float) -> None:
        raise RuntimeError("Cannot change the angle of a horizontal line")

    def value(self) -> float:
        return self._pos[1]

    def setValue(self, v: float) -> None:
        super().setPos((0., v))


class InfiniteVerticalLineItem(InfiniteLineItem):
    """A convenient class for creating a vertical infinite line."""
    def __init__(self, pos: float = 0., **kwargs):
        """Initialization.

        :param pos: Position of the line.
        """
        if 'angle' in kwargs:
            raise ValueError("Cannot set the angle of a vertical line")
        super().__init__((pos, 0.), angle=90., **kwargs)

    def setAngle(self, angle: float) -> None:
        raise RuntimeError("Cannot change the angle of a vertical line")

    def value(self) -> float:
        return self._pos[0]

    def setValue(self, v: float) -> None:
        super().setPos((v, 0.))
