"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtCore import QRectF
from ..backend.QtGui import QColor
from ..backend.QtWidgets import (
    QGraphicsItem, QGraphicsLinearLayout, QGraphicsGridLayout,
    QGraphicsTextItem
)

from ..aesthetics import FColor
from .graphics_item import GraphicsWidget


class AnnotationItem(GraphicsWidget):
    """Add annotation to a plot."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations)

        self._items = []

        self._color = None
        self.setColor(FColor.mkColor('b'))

    def setColor(self, color: QColor) -> None:
        """Set the color of the item labels."""
        self._color = color
        for item in self._items:
            item.setDefaultTextColor(self._color)
        self.update()

    def __addItem(self):
        item = QGraphicsTextItem(parent=self)
        item.setDefaultTextColor(self._color)
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

        for i in range(n_pts):
            self._items[i].setPos(x[i], y[i])
            self._items[i].setPlainText(str(values[i]))

        self.update()

    def boundingRect(self) -> QRectF:
        """Override."""
        return self.mapRectFromParent(self.parentItem().boundingRect())
