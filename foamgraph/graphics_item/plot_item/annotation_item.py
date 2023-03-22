"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from ...backend.QtGui import QColor, QFont, QPainter
from ...backend.QtCore import QRectF, Qt
from ...backend.QtWidgets import QGraphicsTextItem
from ...aesthetics import FColor
from .plot_item import PlotItem


class AnnotationItem(PlotItem):
    """Add annotation to a plot."""

    def __init__(self, x=None, y=None, annotations=None, *, label=None):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None
        self._annotations = None

        self._items = []

        self._offset_x = 0
        self._offset_y = 20

        self._font = None
        # self.setFont(self._font)

        self._color = None
        self.setColor(FColor.mkColor('b'))

        self.setData(x, y, annotations)

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

    def _parseInputData(self, x, **kwargs):
        """Override."""
        x = self._parse_input(x)

        size = len(x)
        y = self._parse_input(kwargs['y'], size=size)
        annotations = self._parse_input(kwargs['annotations'], size=size)

        # do not set data unless they pass the sanity check!
        self._x, self._y, self._annotations = x, y, annotations

    def setData(self, x, y, annotations) -> None:
        """Override.

        :param x: x coordinates of the annotated points.
        :param y: y coordinates of the annotated points.
        :param annotations: displayed texts of the annotations.
        """
        self._parseInputData(x, y=y, annotations=annotations)
        self._updateTextItems(annotations)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [], [])

    def data(self):
        """Override."""
        return self._x, self._y

    def _updateTextItems(self, annotations):
        for i in range(len(self._items), len(self._x)):
            self._addItem()

    def _addItem(self):
        item = QGraphicsTextItem(parent=self)
        item.setDefaultTextColor(self._color)
        item.setFlag(item.GraphicsItemFlag.ItemIgnoresTransformations)
        item.show()
        self._items.append(item)

    def _mapOffsetToView(self):
        if self.canvas() is None:
            return self._offset_x, self._offset_y

        rect = self.canvas().mapSceneToView(
            QRectF(0, 0, self._offset_x, self._offset_y)).boundingRect()
        return (rect.width() if self._offset_x > 0 else -rect.width(),
                rect.height() if self._offset_y > 0 else -rect.height())

    def _computePaddings(self):
        padding_x = self._items[np.argmax(self._x)].boundingRect().width()
        padding_y = self._items[np.argmax(self._y)].boundingRect().height()

        if self.canvas() is None:
            return padding_x, padding_y

        rect = self.canvas().mapSceneToView(
            QRectF(0, 0, padding_x, padding_y)).boundingRect()
        return rect.width(), rect.height()

    def _prepareGraph(self) -> None:
        self._graph = QRectF()
        if len(self._x) == 0:
            return

        x, y = self.transformedData()

        # TODO: maybe cache the value
        offset_x, offset_y = self._mapOffsetToView()
        for i in range(len(self._items)):
            self._items[i].setPos(x[i] + offset_x, y[i] + offset_y)
            self._items[i].setPlainText(str(self._annotations[i]))

        # TODO: maybe cache the value
        padding_x, padding_y = self._computePaddings()

        x_min, x_max = np.nanmin(x), np.nanmax(x)
        y_min, y_max = np.nanmin(y), np.nanmax(y)
        self._graph.setRect(x_min,
                            y_min,
                            x_max - x_min + padding_x,
                            y_max - y_min + padding_y)

    def paint(self, p: QPainter, *args) -> None:
        """Override."""
        ...

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return self._graph
