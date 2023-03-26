"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ...backend.QtGui import QPainter, QPainterPath, QPicture
from ...backend.QtCore import QPointF, QRectF, Qt
from ...aesthetics import FColor
from .plot_item import PlotItem


class CandlestickPlotItem(PlotItem):
    def __init__(self, x=None, y_start=None, y_end=None, *,
                 y_min=None, y_max=None, width=0.5, label=None) -> None:
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y_start = None
        self._y_end = None
        self._y_min = None
        self._y_max = None

        if width > 1.0 or width <= 0:
            width = 1.0
        self._width = width

        self._pen = FColor.mkPen('k')
        self._brush = FColor.mkBrush('b')

        self.setData(x, y_start, y_end, y_min, y_max)

    def setData(self, x, y_start, y_end, y_min, y_max) -> None:
        """Override."""
        self._parseInputData(
            x, y_start=y_start, y_end=y_end, y_min=y_min, y_max=y_max)

        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [], [], [], [])

    def _parseInputData(self, x, **kwargs):
        """Override."""
        x = self._parse_input(x)

        size = len(x)
        y_start = self._parse_input(kwargs['y_start'], size=size)
        y_end = self._parse_input(kwargs['y_end'], size=size)
        y_min = self._parse_input(kwargs['y_min'], size=size)
        y_max = self._parse_input(kwargs['y_max'], size=size)

        # do not set data unless they pass the sanity check!
        self._x, self._y_start, self._y_end, self._y_min, self._y_max = \
            x, y_start, y_end, y_min, y_max

    def data(self):
        """Override."""
        return self._x, self._y_start, self._y_end, self._y_min, self._y_max

    def _prepareGraph(self) -> None:
        self._graph = QPicture()
        p = QPainter(self._graph)

        x, y_start, y_end, y_min, y_max = self.transformedData()

        if len(x) > 1:
            hw = self._width * (x[1] - x[0]) / 2.
        else:
            hw = self._width / 2.

        p.setPen(self._pen)
        for px, s, e, u, l in zip(x, y_start, y_end, y_min, y_max):
            p.drawLine(QPointF(px, l), QPointF(px, u))
            if s > e:
                p.setBrush(FColor.mkBrush('r'))
            else:
                p.setBrush(FColor.mkBrush('g'))
            p.drawRect(QRectF(px - hw, s, hw * 2, e - s))

        p.end()

    def transformedData(self) -> tuple:
        """Override."""
        return (
            self.toLogScale(self._x) if self._log_x_mode else self._x,
            self.toLogScale(self._y_start) if self._log_y_mode else self._y_start,
            self.toLogScale(self._y_end) if self._log_y_mode else self._y_end,
            self.toLogScale(self._y_min) if self._log_y_mode else self._y_min,
            self.toLogScale(self._y_max) if self._log_y_mode else self._y_max
        )

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
