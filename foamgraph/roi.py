"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from enum import Enum
from math import cos, sin
from typing import Union

import numpy as np

from .backend.QtGui import (
    QAction, QGraphicsItem, QImage, QMenu, QPainter, QPainterPath, QPen,
    QPicture, QTransform
)
from .backend.QtCore import (
    pyqtSignal, pyqtSlot, QPoint, QPointF, QRectF, Qt, QTimer
)
from . import pyqtgraph_be as pg
from .pyqtgraph_be.GraphicsScene import HoverEvent, MouseDragEvent
from .pyqtgraph_be import Point

from .aesthetics import FColor


class RoiHandle(pg.UIGraphicsItem):
    """A single interactive point attached to an ROI."""

    def __init__(self, pos: Union[tuple, QPointF, Point], *, parent=None):
        super().__init__(parent=parent)

        # bookkeeping the relative position to the attached ROI
        self._pos = Point(pos)
        self.updatePosition()

        self._size = 10
        self._edges = 4

        self._pen = FColor.mkPen("c", width=0)
        self._hover_pen = FColor.mkPen("y", width=0)

        self._mouse_hovering = False
        self._moving = False
        self._cursor_offset = None

        self._path = QPainterPath()
        self._buildPath()

        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(11)

    def hoverEvent(self, ev: HoverEvent) -> None:
        hovering = False
        if not ev.isExit():
            if ev.acceptDrags(Qt.MouseButton.LeftButton):
                hovering = True

        if self._mouse_hovering == hovering:
            return

        self._mouse_hovering = hovering
        self.update()

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()

        if ev.exiting():
            if self._moving:
                self.parentItem().stateChangeFinished()
            self._moving = False
            self._cursor_offset = 0
            self.update()
        elif ev.entering():
            self.parentItem().handleMoveStarted()
            self._moving = True
            self._cursor_offset = self.scenePos() - ev.buttonDownScenePos()

        if self._moving:
            pos = ev.scenePos() + self._cursor_offset
            self.parentItem().moveHandle(self, pos)

    def _buildPath(self):
        angle = 0
        for i in range(0, self._edges + 1):
            x = self._size * cos(angle)
            y = self._size * sin(angle)
            angle += 2 * np.pi / self._edges
            if i == 0:
                self._path.moveTo(x, y)
            else:
                self._path.lineTo(x, y)

    def paint(self, p, *args) -> None:
        """Override."""
        p.setRenderHints(p.RenderHint.Antialiasing, True)
        if self._mouse_hovering:
            p.setPen(self._hover_pen)
        else:
            p.setPen(self._pen)
        p.drawPath(self._path)

    def boundingRect(self) -> QRectF:
        """Override."""
        return self._path.boundingRect()

    def viewTransformChanged(self):
        # TODO: check whether this method is needed
        self.update()

    def updatePosition(self):
        self.setPos(self._pos * self.parentItem().size())


class ROI(pg.GraphicsObject):
    """Generic region-of-interest graphics object."""

    class DragMode(Enum):
        NONE = 0
        TRANSLATE = 1

    # Emitted when the user starts dragging the ROI (or one of its handles).
    region_change_started_sgn = pyqtSignal(object)

    # Emitted when the user stops dragging the ROI (or one of its handles)
    # or if the ROI is changed programmatically.
    region_change_finished_sgn = pyqtSignal(object)

    # Emitted any time the position of the ROI changes, including while
    # it is being dragged by the user.
    region_changed_sgn = pyqtSignal(object)

    def __init__(self, pos=Point(0, 0), size=Point(1, 1), *,
                 snap: bool = True,
                 parent=None):
        """Initialization.

        :param pos: (x, y) position of the ROI's origin. For most ROIs, this is
            the lower-left corner of its bounding rectangle.
        :param size: (width, height) of the ROI.
        :param snap: If True, the width and height of the ROI are forced
                     to be integers.
        """
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._snap = snap

        pos = Point(pos)
        size = Point(size)

        self._translatable = True

        self._mouse_hovering = False
        self._moving = False
        self._cursor_offset = None
        self._drag_mode = self.DragMode.NONE

        self._pen = FColor.mkPen("k")
        self._hover_pen = FColor.mkPen("w")

        self._handles = []

        self._pos = None
        self._size = None
        self.setPos(pos)
        self.setSize(size)

        self.setZValue(10)

    def setZValue(self, z):
        QGraphicsItem.setZValue(self, z)
        for handle in self._handles:
            handle.setZValue(z + 1)

    def setPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI."""
        self._pen = pen
        self.update()

    def setHoverPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI when the mouse is hovering."""
        self._hover_pen = pen
        self.update()

    def size(self) -> Point:
        """Return the size (w,h) of the ROI."""
        return self._size

    def pos(self) -> Point:
        """Return the position (x, y) of the ROI's origin."""
        return self._pos

    def setPos(self, pos: Union[tuple, QPointF, Point], *,
               update: bool = True,
               finish: bool = True) -> None:
        """Set the position of the ROI (in the parent's coordinate system).

        :param pos: New position of the ROI.
        :param update: ...
        :param finish: ...

        FIXME: check whether it is called repeatedly
        """
        pos = Point(pos)
        if self._snap:
            pos[0] = round(pos[0])
            pos[1] = round(pos[1])

        self._pos = pos
        super().setPos(self._pos)  # why?
        if update:
            self.stateChanged(finish=finish)

    def setSize(self, size: Union[tuple, QPointF, Point], *,
                update: bool = True,
                finish: bool = True) -> None:
        """Set the size of the ROI.

        :param size: New size of the ROI.
        :param update: ...
        :param finish: ...
        """
        size = Point(size)
        if self._snap:
            size[0] = round(size[0])
            size[1] = round(size[1])

        self._size = size
        if update:
            self.stateChanged(finish=finish)

    def scale(self, scale: float, update: bool = True, finish: bool = True) -> None:
        """Resize the ROI by scaling relative to *center*."""
        self.setSize(self._size * scale, update=update, finish=finish)

    def translate(self, offset: Point, update=True, finish=True) -> None:
        """Translate the ROI by a given offset."""
        self.setPos(self._pos + offset, update=update, finish=finish)

    def handleMoveStarted(self) -> None:
        # called by RoiHandle
        self.region_change_started_sgn.emit(self)

    def addHandle(self, pos: Union[tuple, QPointF, Point]) -> None:
        """Add a new handle to the ROI.

        Dragging a scale handle allows changing the height and/or width of the ROI.

        :param pos: The normalized position of the handle relative to the ROI.
            (0, 0) indicates the upper-left corner and (1, 1) indicates the
            lower-right corner.
        """
        handle = RoiHandle(pos, parent=self)
        handle.setZValue(self.zValue() + 1)
        self._handles.append(handle)

        self.stateChanged()

    @abc.abstractmethod
    def _addHandles(self) -> None:
        ...

    def _clearHandles(self) -> None:
        """Remove the ROI handle."""
        for handle in self._handles:
            self.scene().removeItem(handle)
        self._handles.clear()
        self.stateChanged()

    def setSelected(self, state: bool) -> None:
        QGraphicsItem.setSelected(self, state)
        if state:
            for handle in self._handles:
                handle.show()
        else:
            for handle in self._handles:
                handle.hide()

    def hoverEvent(self, ev: HoverEvent) -> None:
        hover = False
        if not ev.isExit():
            if self._translatable and ev.acceptDrags(Qt.MouseButton.LeftButton):
                hover = True

        if self._mouse_hovering == hover:
            return

        self._mouse_hovering = hover
        # update because color changed
        self.update()

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        drag_mode = self.DragMode
        if ev.entering():
            if ev.button() == Qt.MouseButton.LeftButton:
                # self.setSelected(True)

                if self._translatable:
                    self._drag_mode = drag_mode.TRANSLATE
                else:
                    self._drag_mode = drag_mode.NONE

                if self._drag_mode != drag_mode.NONE:
                    self.moveStarted()
                    self._cursor_offset = self.pos() - self.mapToParent(ev.buttonDownPos())
                    ev.accept()
                else:
                    ev.ignore()
            else:
                self._drag_mode = drag_mode.NONE
                ev.ignore()

        if ev.exiting() and self._drag_mode != drag_mode.NONE:
            self.moveFinished()
            return

        if self._drag_mode == drag_mode.TRANSLATE:
            self.translate(
                self.mapToParent(ev.pos()) + self._cursor_offset - self.pos(),
                finish=False)

    def moveStarted(self) -> None:
        self._moving = True
        self.region_change_started_sgn.emit(self)

    def moveFinished(self) -> None:
        if self._moving:
            self.stateChangeFinished()
        self._moving = False

    def moveHandle(self, handle: RoiHandle, pos: Point) -> None:
        """Move the given handle to the given position.

        :param handle: The ROI handle.
        :param pos: New position of the handle in its scene's coordinate system.
        """
        p0 = self.mapToParent(handle.pos()) - self._pos
        p1 = self.mapToParent(self.mapFromScene(pos)) - self._pos

        self.setSize(Point(self._size * (p1 / p0)), finish=False)

    def stateChanged(self, finish: bool = True) -> None:
        """Process changes to the state of the ROI."""
        self.prepareGeometryChange()

        for handle in self._handles:
            handle.updatePosition()

        self.update()
        self.region_changed_sgn.emit(self)

        if finish:
            self.stateChangeFinished()
            self.informViewBoundsChanged()

    def stateChangeFinished(self):
        self.region_change_finished_sgn.emit(self)

    def boundingRect(self) -> QRectF:
        """Override."""
        return QRectF(0, 0, self._size[0], self._size[1]).normalized()

    def paint(self, p, *args) -> None:
        """Override."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._mouse_hovering:
            p.setPen(self._hover_pen)
        else:
            p.setPen(self._pen)

        p.drawRect(self.boundingRect())


class RectROI(ROI):
    """Rectangular ROI widget."""
    def __init__(self, idx: int, *,
                 pos: tuple = (0, 0),
                 size: tuple = (1, 1),
                 color: str = 'k', **kwargs):
        """Initialization.

        :param idx: index of the ROI.
        :param pos: (x, y) of the left-upper corner.
        :param size: (w, h) of the ROI.
        :param color: ROI display color.
        """
        # TODO: make 'color' an attribute of the parent class
        self._color = color
        super().__init__(Point(pos), Point(size), **kwargs)

        pen = FColor.mkPen(color, width=2, style=Qt.PenStyle.SolidLine)
        self.setPen(pen)

        self._index = idx

    @property
    def index(self):
        return self._index

    @property
    def color(self):
        return self._color

    def setLocked(self, locked: bool):
        if locked:
            self._translatable = False
            self._clearHandles()
        else:
            self._translatable = True
            self._addHandles()

    def _addHandles(self):
        """Override."""
        self.addHandle([1, 1])
