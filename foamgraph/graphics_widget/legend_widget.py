"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import OrderedDict

from ..backend.QtGui import QBrush, QColor, QPen
from ..backend.QtCore import QPointF, Qt
from ..backend.QtWidgets import (
    QGraphicsLinearLayout, QGraphicsGridLayout
)

from ..aesthetics import FColor
from ..graphics_scene import MouseDragEvent
from ..graphics_item import PlotItem
from .graphics_widget import GraphicsWidget
from .label_widget import LabelWidget


class LegendWidget(GraphicsWidget):
    """Displays a legend used for describing the contents of a plot."""

    class SampleWidget(GraphicsWidget):
        """Used as a graphics label in a LegendWidget."""

        def __init__(self, item: PlotItem, **kwargs):
            super().__init__(**kwargs)
            self._item = item

        def paint(self, p, *args) -> None:
            """Override."""
            self._item.drawSample(p)

    def __init__(self, *,
                 orientation: Qt.Orientation = Qt.Orientation.Vertical,
                 **kwargs):
        """Initialization.

        :param orientation: orientation of the legend layout. Must be either
            "horizontal" or "vertical".
        """
        super().__init__(**kwargs)
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations)

        self._orientation = orientation
        if orientation == Qt.Orientation.Vertical:
            self._layout = QGraphicsGridLayout()
            self._layout.setVerticalSpacing(0)
            self._layout.setHorizontalSpacing(25)
        else:  # orientation == Qt.Orientation.Horizontal:
            self._layout = QGraphicsLinearLayout(orientation)
            self._layout.setSpacing(25)
        self._layout.setContentsMargins(5, 5, 0, 0)
        self.setLayout(self._layout)

        self._items = OrderedDict()

        self._pen = None
        self.setPen(FColor.mkPen('foreground'))
        self._label_color = None
        self.setLabelColor(FColor.mkColor('foreground'))
        self._brush = None
        self.setBrush(FColor.mkBrush(None))

        self._draggable = True
        self._moving = False
        self._cursor_offset = QPointF(0, 0)

    def setPen(self, pen: QPen) -> None:
        """Set the pen used to draw a border around the legend."""
        self._pen = pen
        self.update()

    def setLabelColor(self, color: QColor) -> None:
        """Set the color of the item labels."""
        self._label_color = color
        for sample, label in self._items.values():
            label.setColor(self._label_color)
        self.update()

    def setBrush(self, brush: QBrush) -> None:
        """Set the brush used to draw the legend background."""
        self._brush = brush
        self.update()

    def setDraggable(self, draggable: bool) -> None:
        self._draggable = draggable

    def addItem(self, item: PlotItem) -> None:
        """Add a new item to the legend.

        :param item: plot item to be added.
        """
        if not item.label() or not item.drawSample():
            return

        label = LabelWidget(item.label())
        label.setColor(self._label_color)
        sample = self.SampleWidget(item)
        self._items[item] = (sample, label)
        item.label_changed_sgn.connect(self.onItemLabelChanged)
        item.visibleChanged.connect(self.onItemVisibleChanged)
        if self._orientation == Qt.Orientation.Vertical:
            row = self._layout.rowCount()
            self._layout.addItem(sample, row, 0)
            self._layout.addItem(label, row, 1)
        else:
            self._layout.addItem(sample)
            self._layout.addItem(label)

        self._updateSize()

    def removeItem(self, item: PlotItem) -> None:
        """Remove a given item from the legend.

        :param item: PlotItem instance.
        """
        if item not in self._items:
            return

        sample, label = self._items[item]
        self._layout.removeItem(sample)
        self._layout.removeItem(label)
        del self._items[item]
        self._updateSize()

    def removeAllItems(self) -> None:
        """Remove all plot items from the legend."""
        for sample, label in self._items.values():
            self._layout.removeItem(sample)
            self._layout.removeItem(label)
        self._items.clear()
        self._updateSize()

    def _updateSize(self) -> None:
        # TODO: is there a better way?
        height = 0
        width = 0
        if self._orientation == Qt.Orientation.Vertical:
            for row in range(self._layout.rowCount()):
                row_height = 0
                col_width = 0
                for col in range(self._layout.columnCount()):
                    item = self._layout.itemAt(row, col)
                    # There could be empty rows and cols which results in
                    # returns of None items.
                    if item is not None and item.isVisible():
                        col_width += item.geometry().width() + 3
                        row_height = max(row_height, item.geometry().height())
                width = max(width, col_width)
                height += row_height
        else:
            for row in range(self._layout.count()):
                row_height = 0
                col_width = 0
                item = self._layout.itemAt(row)
                if item.isVisible():
                    col_width += item.geometry().width() + 3
                    row_height = max(row_height, item.geometry().height())
                height = max(height, row_height)
                width += col_width

        pos = self.pos()
        self.setGeometry(pos.x(), pos.y(), width, height)

    def onItemLabelChanged(self, label: str) -> None:
        item = self.sender()
        if item in self._items:
            self._items[item][1].setPlainText(label)
        else:
            self.addItem(item)

    def onItemVisibleChanged(self) -> None:
        item = self.sender()
        sample, label = self._items[item]
        state = item.isVisible()
        label.setVisible(state)
        sample.setVisible(state)
        self._updateSize()

    def paint(self, p, *args) -> None:
        """Override."""
        p.setPen(self._pen)
        p.setBrush(self._brush)
        p.drawRect(self.boundingRect())

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if not self._draggable or ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()

        if ev.entering():
            self._moving = True
            self._cursor_offset = self.pos() - self.mapToParent(ev.buttonDownPos())
        elif ev.exiting():
            self._moving = False
            self._cursor_offset = QPointF(0, 0)

        if self._moving:
            pos = self._cursor_offset + self.mapToParent(ev.pos())
            # TODO: Add constraint for the right and bottom as well as
            #       during a resize event.
            if pos.x() < 0:
                pos.setX(0)
            if pos.y() < 0:
                pos.setY(0)
            self.setPos(pos)
