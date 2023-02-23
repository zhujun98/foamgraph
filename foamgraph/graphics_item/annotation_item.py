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

        self._offset = QPointF(-10, 20)

        self._font = None
        # self.setFont(self._font)

        self._color = None
        self.setColor(FColor.mkColor('b'))

    def setOffset(self, x: float, y: float) -> None:
        """Set the offset of the text items with respect to the annotated points."""
        self._offset = QPointF(x, y)

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
        vb = self.getViewBox()
        try:
            # FIXME
            offset = vb.mapSceneToView(self._offset) - vb.mapSceneToView(QPointF(0, 0))
        except TypeError:
            return
        for i in range(n_pts):
            self._items[i].setPos(x[i] + offset.x(), y[i] - offset.y())
            self._items[i].setPlainText(str(values[i]))

        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.update()

    def boundingRect(self) -> QRectF:
        """Override."""
        return QRectF()

    def paint(self, p, *args) -> None:
        """Override."""
        for item in self._items:
            item.paint(p, *args)
