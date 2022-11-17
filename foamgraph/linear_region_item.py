"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from .backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from .backend.QtGui import QBrush, QPen
from .aesthetics import FColor

from . import pyqtgraph_be as pg
from .pyqtgraph_be.GraphicsScene import HoverEvent, MouseDragEvent
from .line_items import InfiniteHorizontalLineItem, InfiniteVerticalLineItem


class LinearRegionItem(pg.GraphicsObject):
    """A horizontal or vertical region inbetween two lines.

    The region can be dragged and is bounded by lines which can be dragged
    individually.
    """
    # Emitted when the user has finished dragging the region (or one of its lines)
    # and when the region is changed programmatically.
    region_change_finished_sgn = pyqtSignal(object)
    # Emitted while the user is dragging the region (or one of its lines)
    # and when the region is changed programmatically.
    region_changed_sgn = pyqtSignal(object)
    
    def __init__(self, region: tuple = (0, 1), *,
                 orientation: Qt.Orientation = Qt.Orientation.Vertical,
                 draggable=True):
        """Create a new LinearRegionItem.

        :param region: initial positions of the two boundary lines.
        :param orientation: orientation of the boundary lines of the region.
        :param draggable: whether the region can be changed by mouse dragging.
        """
        super().__init__()
        self._orientation = orientation
        self._moving = False
        self._cursor_offset = 0
        self._mouse_hovering = False
        self._bounds = None
            
        if orientation == Qt.Orientation.Horizontal:
            self._lines = [
                InfiniteHorizontalLineItem(v, draggable=draggable, parent=self)
                for v in region]
            self._lines[0].scale(1, -1)
            self._lines[1].scale(1, -1)
        elif orientation == Qt.Orientation.Vertical:
            self._lines = [
                InfiniteVerticalLineItem(v, draggable=draggable, parent=self)
                for v in region]
        else:
            raise ValueError(f"Unknown orientation value: {orientation}")

        self.setAcceptHoverEvents(draggable)

        for i, line in enumerate(self._lines):
            line.position_change_finished_sgn.connect(self.lineMoveFinished)
            line.position_changed_sgn.connect(lambda: self.lineMoved(i))

        self.setLinePen(FColor.mkPen("Gray"))

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

    def setLinePen(self, pen: QPen) -> None:
        for line in self._lines:
            line.setPen(pen)

    def setLineHoverPen(self, pen: QPen) -> None:
        for line in self._lines:
            line.setHoverPen(pen)

    def region(self) -> tuple:
        """Return the values at the edges of the region."""
        return self._lines[0].value(), self._lines[1].value()

    def setRegion(self, region: tuple):
        """Set the values for the edges of the region.
        
        :param region:
        """
        self._lines[0].setValue(region[0])
        self._lines[1].setValue(region[1])
        self.lineMoved(0)
        self.lineMoved(1)
        self.lineMoveFinished()

    def boundingRect(self):
        br = self.viewRect()  # bounds of containing ViewBox mapped to local coords.
        
        rng = self.region()
        if self._orientation == Qt.Orientation.Vertical:
            br.setLeft(rng[0])
            br.setRight(rng[1])
            length = br.height()
            br.setBottom(br.top())
            br.setTop(br.top() + length)
        else:
            br.setTop(rng[0])
            br.setBottom(rng[1])
            length = br.width()
            br.setRight(br.left())
            br.setLeft(br.left() + length)

        br = br.normalized()
        
        if self._bounds != br:
            self._bounds = br
            self.prepareGeometryChange()
        
        return br
        
    def paint(self, p, *args) -> None:
        """Override."""
        if self._mouse_hovering:
            p.setBrush(self._hover_brush)
        else:
            p.setBrush(self._brush)
        p.setPen(self._pen)
        p.drawRect(self.boundingRect())

    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        if self._orientation == Qt.Orientation.Vertical and axis == 0:
            return self.region()
        if self._orientation == Qt.Orientation.Horizontal and axis == 1:
            return self.region()
        return None

    def lineMoved(self, i):
        if self._lines[0].value() > self._lines[1].value():
            self._lines[i].setValue(self._lines[1-i].value())
        
        self.prepareGeometryChange()
        self.region_changed_sgn.emit(self)
            
    def lineMoveFinished(self):
        self.region_change_finished_sgn.emit(self)

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()

        if ev.entering():
            bdp = ev.buttonDownPos()
            self._cursor_offset = [l.pos() - bdp for l in self._lines]
            self._moving = True
            
        if not self._moving:
            return

        self._lines[0].blockSignals(True)  # only want to update once
        for i, l in enumerate(self._lines):
            l.setPos(self._cursor_offset[i] + ev.pos())
        self._lines[0].blockSignals(False)
        self.prepareGeometryChange()

        if ev.exiting():
            self._moving = False
            self.region_change_finished_sgn.emit(self)
        else:
            self.region_changed_sgn.emit(self)

    def hoverEvent(self, ev: HoverEvent) -> None:
        hovering = False
        if not ev.isExit() and ev.acceptDrags(Qt.MouseButton.LeftButton):
            hovering = True

        if self._mouse_hovering == hovering:
            return
        self._mouse_hovering = hovering
        self.update()
