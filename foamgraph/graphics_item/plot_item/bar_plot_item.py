"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

from ...backend.QtGui import QPainter, QPicture
from ...backend.QtCore import QRectF, Qt
from ...aesthetics import FColor
from .plot_item import PlotItem


class BarPlotItem(PlotItem):
    """BarPlotItem"""
    def __init__(self, x=None, y=None, *,
                 width=1.0, pen=None, brush=None, label=None):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        self._width = max(min(1.0, width), 0.1)
        self._scale = 1.0
        self._shift = 0.0
        self.setShift()

        if pen is None and brush is None:
            self._pen = FColor.mkPen('b')
            self._brush = FColor.mkBrush('b', alpha=100)
        else:
            self._pen = FColor.mkPen() if pen is None else pen
            self._brush = FColor.mkBrush() if brush is None else brush

        self.setData(x, y)

    def setScale(self, scale) -> None:
        self._scale = scale
        self._graph = None

    def setShift(self, shift: Optional[float] = None) -> None:
        if shift is None:
            shift = -self._width / 2.
        self._shift = shift
        self._graph = None

    def _parseInputData(self, x, **kwargs):
        """Override."""
        x = self._parse_input(x)
        y = self._parse_input(kwargs['y'], size=len(x))

        # do not set data unless they pass the sanity check!
        self._x, self._y = x, y

    def setData(self, x, y) -> None:
        """Override."""
        self._parseInputData(x, y=y)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [])

    def data(self):
        """Override."""
        return self._x, self._y

    def _prepareGraph(self) -> None:
        """Override."""
        self._graph = QPicture()
        p = QPainter(self._graph)
        p.setPen(self._pen)
        p.setBrush(self._brush)

        x, y = self.transformedData()
        # Now it works for bar plot with equalized gaps
        # TODO: extend it
        if len(x) > 1:
            width = self._width * (x[1] - x[0])
        else:
            width = self._width

        width *= self._scale

        shift = self._shift
        for px, py in zip(x, y):
            p.drawRect(QRectF(px + shift, 0, width, py))

        p.end()

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return QRectF(self._graph.boundingRect())

    def paint(self, p: QPainter, *args) -> None:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        self._graph.play(p)

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Override."""
        if p is not None:
            p.setBrush(self._brush)
            p.setPen(self._pen)
            # Legend sample has a bounding box of (0, 0, 20, 20)
            p.drawRect(QRectF(2, 2, 18, 18))
        return True


class BarPlotItemManager:
    def __init__(self):
        self._items = []

        self._orientation = Qt.Orientation.Vertical

    def addItem(self, item: BarPlotItem) -> None:
        self._items.append(item)
        self.setStackOrientation(self._orientation)

    def removeItem(self, item: BarPlotItem) -> None:
        self._items.remove(item)
        for item in self._items:
            item.setScale(1. / len(self._items))

    def setStackOrientation(self, orientation: Qt.Orientation) -> None:
        self._orientation = orientation
        for item in self._items:
            if orientation == Qt.Orientation.Vertical:
                item.setScale(1.0)
                item.setShift()
            else:
                total_width = 0
                for item in self._items:
                    total_width += item._width
                scale = 1. / len(self._items)
                shift = - total_width * scale / 2.
                for item in self._items:
                    item.setScale(scale)
                    item.setShift(shift)
                    shift += item._width * scale
