"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod
from enum import Enum
from typing import Optional, Union

from ..backend.QtGui import QPainter, QPainterPath, QPen
from ..backend.QtCore import pyqtSignal, QPointF, QRect, QRectF, QSize, Qt
from ..backend.QtWidgets import (
    QAbstractGraphicsShapeItem, QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsTextItem
)

from ..aesthetics import FColor
from ..graphics_scene import MouseDragEvent
from .graphics_item import GraphicsObject


class ROIBase(GraphicsObject):

    class Moving(Enum):
        NONE = 0
        BODY = 1
        TOP = 2
        BOTTOM = 3
        LEFT = 4
        RIGHT = 5

    # Emitted when the user stops dragging the ROI (or one of its handles)
    # or if the ROI is changed programmatically.
    region_change_finished_sgn = pyqtSignal()

    item_type = QAbstractGraphicsShapeItem

    def __init__(self, label: str = "", *args, **kwargs):
        super().__init__(**kwargs)

        self._label = label

        self._item = self.item_type(*args, parent=self)

        self._text = QGraphicsTextItem("", parent=self)
        self._text.setFlag(
            QGraphicsTextItem.GraphicsItemFlag.ItemIgnoresTransformations)

        self._ref_cursor: QPointF = None
        self._ref_rect: QRectF = None
        self._moving = self.Moving.NONE

        self._pen = FColor.mkPen("k")
        self._hover_pen = FColor.mkPen("w")

    def label(self) -> str:
        return self._label

    def setPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI."""
        self._pen = pen
        self.update()

    def pen(self) -> QPen():
        return self._pen

    def setHoverPen(self, pen: QPen) -> None:
        """Set the QPen used to draw the ROI when the mouse is hovering."""
        self._hover_pen = pen
        self.update()

    def rect(self) -> tuple[int, int, int, int]:
        """Return the bounding region in parent's coordinate system."""
        pos = self.pos()
        rect = self._item.rect()
        return int(pos.x()), int(pos.y()), int(rect.width()), int(rect.height())

    def setPos(self, x: Union[QPointF, float], y: Optional[float] = None):
        """Override."""
        if y is None:
            y, x = x.y(), x.x()
        super().setPos(int(x), int(y))

    def setRect(self, x: float, y: float, width: float, height: float) -> None:
        self.setPos(x, y)
        self._item.setRect(0, 0, int(width), int(height))

    def moveBy(self, dx: float, dy: float) -> None:
        """Override."""
        super().moveBy(int(dx), int(dy))

    def _updateMovingState(self, pos: QPointF):
        if not self.isEnabled():
            self._moving = self.Moving.NONE
            return

        rect = self._item.rect()
        b = 0.2  # border
        if pos.x() > (1 - b) * rect.width() + rect.x() :
            self._moving = self.Moving.RIGHT
        elif pos.x() < b * rect.width() + rect.x():
            self._moving = self.Moving.LEFT
        elif pos.y() > (1 - b) * rect.height() + rect.y():
            self._moving = self.Moving.BOTTOM
        elif pos.y() < b * rect.height() + rect.y():
            self._moving = self.Moving.TOP
        else:
            self._moving = self.Moving.BODY

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return

        ev.accept()

        if ev.entering():
            pos = ev.buttonDownPos()
            self._updateMovingState(pos)

            if self._moving == self.Moving.NONE:
                return

            self._ref_cursor = pos
            self._ref_rect = self._item.rect()

        offset = ev.pos() - self._ref_cursor
        ref_rect = self._ref_rect
        if self._moving == self.Moving.BODY:
            self.moveBy(offset.x(), offset.y())
        elif self._moving == self.Moving.RIGHT:
            w = ref_rect.width() + offset.x()
            self._item.setRect(0, 0, 1 if w < 1 else w, ref_rect.height())
        elif self._moving == self.Moving.LEFT:
            self.moveBy(offset.x(), 0)
            rect = self._item.rect()
            w = rect.width() - int(offset.x())
            self._item.setRect(0, 0, 1 if w < 1 else w, rect.height())
        elif self._moving == self.Moving.BOTTOM:
            h = ref_rect.height() + offset.y()
            self._item.setRect(0, 0, ref_rect.width(), 1 if h < 1 else h)
        else:  # self._moving == self.Moving.TOP:
            self.moveBy(0, offset.y())
            rect = self._item.rect()
            h = rect.height() - int(offset.y())
            self._item.setRect(0, 0, rect.width(), 1 if h < 1 else h)

        if ev.exiting() and self._moving != self.Moving.NONE:
            self.stateChanged(finish=True)
            self._moving = self.Moving.NONE
            return

        self.stateChanged(finish=False)

    def stateChanged(self, finish: bool = True) -> None:
        """Process changes to the state of the ROI."""
        self.update()
        if finish:
            self.region_change_finished_sgn.emit()
            self.informViewBoundsChanged()

    @abstractmethod
    def region(self) -> tuple:
        """Returns the geometry parameters for querying region of interest."""
        raise NotImplementedError

    def boundingRect(self) -> QRectF:
        """Override."""
        return self._item.boundingRect()

    def paint(self, p: QPainter, *args) -> None:
        """Override."""
        if self._moving == self.Moving.NONE:
            self._item.setPen(self._pen)
            self._text.setPlainText("")
        else:
            self._item.setPen(self._hover_pen)
            self._text.setDefaultTextColor(self._hover_pen.color())
            self._text.setPlainText(str(self.rect()))


class RectROI(ROIBase):
    """Rectangular ROI widget."""

    item_type = QGraphicsRectItem

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def region(self) -> tuple:
        return self.rect()


class EllipseROI(ROIBase):

    item_type = QGraphicsEllipseItem

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def region(self) -> tuple:
        return self.rect()
