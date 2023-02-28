"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtCore import QPointF, QRectF
from ..backend.QtGui import QColor, QFont
from ..backend.QtWidgets import (
    QGraphicsItem, QGraphicsLinearLayout, QGraphicsGridLayout,
    QGraphicsTextItem
)

from ..aesthetics import FColor
from .graphics_item import GraphicsObject


class AnnotationItem(GraphicsObject):
    """Add annotation to a plot."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._items = []
        self._x_span = 0
        self._y_span = 0
        self._x_offset = 0
        self._y_offset = 0

        self._font = None
        # self.setFont(self._font)

        self._color = None
        self.setColor(FColor.mkColor('b'))

    def setOffset(self, x: float, y: float) -> None:
        """Set offset of text items with respect to annotated points."""
        self._x_offset = x
        self._y_offset = y

    def setFont(self, font: QFont) -> None:
        """Set the font of the text items."""
        self._font = font
        for item in self._items:
            item.setFont(self._font)
        self.update()

    def setColor(self, color: QColor) -> None:
        """Set the color of the text items."""
        self._color = color
        for item in self._items:
            item.setDefaultTextColor(self._color)
        self.update()

    def __addItem(self):
        item = QGraphicsTextItem(parent=self)
        item.setDefaultTextColor(self._color)
        item.setFlag(item.GraphicsItemFlag.ItemIgnoresTransformations)
        item.show()
        self._items.append(item)

    def setData(self, x, y, values) -> None:
        """Set the positions and texts of the annotation.

        :param list-like x: x coordinates of the annotated point.
        :param list-like y: y coordinates of the annotated point.
        :param list-like values: displayed texts of the annotations.
        """
        if not len(x) == len(y) == len(values):
            raise ValueError("data have different lengths!")

        n_pts = len(values)
        n_items = len(self._items)
        for i in range(n_pts - n_items):
            self.__addItem()

        # TODO: improve
        vb = self.canvas()

        for i in range(n_pts):
            # p = vb.mapFromView(QPointF(x[i], y[i]))
            # if p is None:
            #     continue
            self._items[i].setPos(x[i], y[i])
            self._items[i].setPlainText(str(values[i]))

        import numpy as np
        self._x_span = np.max(x) - np.min(x)
        self._y_span = np.max(y) - np.min(y)

        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.update()

    def boundingRect(self) -> QRectF:
        """Override."""
        return QRectF(0, 0, self._x_span, self._y_span)

    def paint(self, p, *args) -> None:
        """Override."""
        for item in self._items:
            item.paint(p, *args)
