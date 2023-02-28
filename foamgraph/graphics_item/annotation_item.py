"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

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
        self._rect = QRectF()

        self._offset_x = 0
        self._offset_y = 20

        self._font = None
        # self.setFont(self._font)

        self._color = None
        self.setColor(FColor.mkColor('b'))

    def setOffsetX(self, x: float) -> None:
        """Set x offset of text items with respect to annotated points."""
        self._offset_x = x

    def setOffsetY(self, y: float) -> None:
        """Set y offset of text items with respect to annotated points."""
        self._offset_y = y

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

    def setData(self, x, y, annotations) -> None:
        """Set the positions and texts of the annotation.

        :param x: x coordinates of the annotated points.
        :param y: y coordinates of the annotated points.
        :param annotations: displayed texts of the annotations.
        """
        num_annotations = len(annotations)
        if not len(x) == len(y) == num_annotations:
            raise ValueError("data have different lengths!")

        self._updateTextItems(num_annotations)

        offset_x, offset_y = self._mapOffsetToView()
        for i in range(len(self._items)):
            self._items[i].setPos(x[i] + offset_x, y[i] + offset_y)
            self._items[i].setPlainText(str(annotations[i]))

        self._updateRect(x, y, offset_x, offset_y)
        self.prepareGeometryChange()
        self.informViewBoundsChanged()

    def _addItem(self):
        item = QGraphicsTextItem(parent=self)
        item.setDefaultTextColor(self._color)
        item.setFlag(item.GraphicsItemFlag.ItemIgnoresTransformations)
        item.show()
        self._items.append(item)

    def _updateTextItems(self, num_annotations):
        for i in range(len(self._items), num_annotations):
            self._addItem()

    def _mapOffsetToView(self):
        rect = self.canvas().mapSceneToView(
            QRectF(0, 0, self._offset_x, self._offset_y)).boundingRect()
        return (rect.width() if self._offset_x > 0 else -rect.width(),
                rect.height() if self._offset_y > 0 else -rect.height())

    def _computePaddings(self, x, y):
        padding_x = self._items[np.argmax(x)].boundingRect().width()
        padding_y = self._items[np.argmax(y)].boundingRect().height()
        rect = self.canvas().mapSceneToView(
            QRectF(0, 0, padding_x, padding_y)).boundingRect()
        return rect.width(), rect.height()

    def _updateRect(self, x, y, offset_x, offset_y):
        padding_x, padding_y = self._computePaddings(x, y)
        x_min, x_max = np.min(x), np.max(x)
        y_min, y_max = np.min(y), np.max(y)
        self._rect.setRect(x_min + offset_x,
                           y_min + offset_y,
                           x_max - x_min + padding_x,
                           y_max - y_min + padding_y)

    def boundingRect(self) -> QRectF:
        """Override."""
        return self._rect

    def paint(self, p, *args) -> None:
        """Override."""
        ...
