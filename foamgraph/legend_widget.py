"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import OrderedDict

from .backend.QtGui import QBrush, QColor, QPainterPath, QPen
from .backend.QtCore import QPointF, QRectF, Qt
from .backend.QtWidgets import (
    QGraphicsItem, QGraphicsLinearLayout, QGraphicsGridLayout
)

from . import pyqtgraph_be as pg
from .pyqtgraph_be.GraphicsScene import HoverEvent, MouseDragEvent
from .pyqtgraph_be import Point
from .aesthetics import FColor
from .plot_items import PlotItem


class LegendWidget(pg.GraphicsAnchorWidget):
    """Displays a legend used for describing the contents of a plot."""

    class SampleWidget(pg.GraphicsWidget):
        """Used as a graphics label in a LegendWidget."""

        def __init__(self, item: PlotItem):
            super().__init__()
            self._item = item

        def paint(self, p, *args) -> None:
            """Override."""
            self._item.drawSample(p)

    def __init__(self, offset: tuple, *,
                 orientation: str = "vertical",
                 draggable: bool = True):
        """Initialization.

        :param orientation: orientation of the legend layout. Must be either
            "horizontal" or "vertical".
        :param draggable: whether the legend widget is draggable.
        :param offset: specifies the offset position relative to the legend's parent.
            Positive values offset from the left or top; negative values
            offset from the right or bottom. If offset is None, the
            legend must be anchored manually by calling anchor() or
            positioned by calling setPos().
        """
        super().__init__()
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations)

        self._orientation = orientation
        orientation = orientation.lower()
        if orientation == "horizontal":
            self._orientation = Qt.Orientation.Horizontal
            self._layout = QGraphicsLinearLayout(self._orientation)
            self._layout.setSpacing(25)
        elif orientation == "vertical":
            self._orientation = Qt.Orientation.Vertical
            self._layout = QGraphicsGridLayout()
            self._layout.setVerticalSpacing(0)
            self._layout.setHorizontalSpacing(25)
        else:
            raise ValueError(f"Orientation must be either 'horizontal' "
                             f"or 'vertical'. Actual: {orientation}")
        self._layout.setContentsMargins(5, 5, 0, 0)
        self.setLayout(self._layout)

        self._items = OrderedDict()
        self._offset = Point(offset)

        self._pen = None
        self.setPen(FColor.mkPen("k"))
        self._label_text_color = None
        self.setLabelColor(FColor.mkColor("k"))
        self._brush = None
        self.setBrush(FColor.mkBrush(None))

        self._draggable = draggable

    def setPen(self, pen: QPen) -> None:
        """Set the pen used to draw a border around the legend."""
        self._pen = pen
        self.update()

    def setLabelColor(self, color: QColor) -> None:
        """Set the color of the item labels."""
        self._label_text_color = color
        for sample, label in self._items:
            label.setAttr('color', self._label_text_color)
        self.update()

    def setBrush(self, brush: QBrush) -> None:
        """Set the brush used to draw the legend background."""
        self._brush = brush
        self.update()

    def setParentItem(self, parent: QGraphicsItem) -> None:
        """Override."""
        super().setParentItem(parent)
        anchorx = 1 if self._offset[0] <= 0 else 0
        anchory = 1 if self._offset[1] <= 0 else 0
        anchor = (anchorx, anchory)
        self._anchor(itemPos=anchor, parentPos=anchor, offset=self._offset)

    def addItem(self, item: PlotItem) -> None:
        """Add a new item to the legend.

        :param item: plot item to be added.
        """
        label = pg.LabelItem(
            item.label(), color=self._label_text_color, justify='left')
        sample = self.SampleWidget(item)
        self._items[item] = (sample, label)
        item.label_changed_sgn.connect(self.onItemLabelChanged)
        item.visibleChanged.connect(self.onItemVisibleChanged)
        if self._orientation == Qt.Orientation.Horizontal:
            self._layout.addItem(sample)
            self._layout.addItem(label)
        else:
            row = self._layout.rowCount()
            self._layout.addItem(sample, row, 0)
            self._layout.addItem(label, row, 1)

        self._updateSize()

    def removeItem(self, item: PlotItem) -> None:
        """Remove a given item from the legend.

        :param item: PlotItem instance.
        """
        if item not in self._items:
            raise KeyError(f"Item {item} not found")

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
        if self._orientation == Qt.Orientation.Horizontal:
            for row in range(self._layout.count()):
                row_height = 0
                col_width = 0
                item = self._layout.itemAt(row)
                if item.isVisible():
                    col_width += item.geometry().width() + 3
                    row_height = max(row_height, item.geometry().height())
                height = max(height, row_height)
                width += col_width
        else:
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
        self.setGeometry(0, 0, width, height)

    def onItemLabelChanged(self, label: str) -> None:
        item = self.sender()
        self._items[item][1].setText(label)

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

    def hoverEvent(self, ev: HoverEvent) -> None:
        ev.acceptDrags(Qt.MouseButton.LeftButton)

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        if not self._draggable:
            return

        if ev.button() == Qt.MouseButton.LeftButton:
            ev.accept()
            self.autoAnchor(self.pos() + ev.pos() - ev.lastPos())
