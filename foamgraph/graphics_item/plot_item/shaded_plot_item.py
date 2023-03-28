"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

import numpy as np

from ...backend.QtGui import QPainter, QPainterPath, QPolygonF
from ...backend.QtCore import QPointF, QRectF, Qt
from ...aesthetics import FColor
from .plot_item import PlotItem


class ShadedPlotItem(PlotItem):
    """ShadedPlotItem.

    Visualize area between two lines.
    """

    def __init__(self, x=None, y1=None, y2=None, *,
                 pen=None, brush=None, label=None, check_finite=True):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y1 = None
        self._y2 = None

        self._pen = FColor.mkPen('g') if pen is None else pen
        self._brush = FColor.mkBrush(self._pen.color(), alpha=100) \
            if brush is None else brush

        self._check_finite = check_finite

        self._graph_shade = None

        self.setData(x, y1, y2)

    def _parseInputData(self, x, **kwargs):
        """Override."""
        x = self._parse_input(x)
        y1 = self._parse_input(kwargs['y1'], size=len(x))
        y2 = self._parse_input(kwargs['y2'], size=len(x))

        # do not set data unless they pass the sanity check!
        self._x, self._y1, self._y2 = x, y1, y2

    def setData(self, x, y1, y2) -> None:
        """Override."""
        self._parseInputData(x, y1=y1, y2=y2)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [], [])

    def data(self):
        """Override."""
        return self._x, self._y1, self._y2

    def transformedData(self) -> tuple:
        """Override."""
        if not self._check_finite:
            return super().transformedData()

        # inf/nans completely prevent the plot from being displayed starting on
        # Qt version 5.12.3
        # we do not expect to have nan in x
        return (
            self.toLogScale(self._x) if self._log_x_mode else self._x,
            self.toLogScale(self._y1) if self._log_y_mode else np.nan_to_num(self._y1),
            self.toLogScale(self._y2) if self._log_y_mode else np.nan_to_num(self._y2)
        )

    def _prepareGraph(self) -> None:
        """Override."""
        x, y1, y2 = self.transformedData()
        polygon1 = PlotItem.array2Polygon(x, y1)
        polygon2 = PlotItem.array2Polygon(x[::-1], y2[::-1])
        self._graph = QPainterPath()
        self._graph.addPolygon(polygon1)
        self._graph.addPolygon(polygon2)

        self._graph_shade = QPainterPath()
        self._graph_shade.addPolygon(polygon1)
        path = QPainterPath()
        path.addPolygon(polygon2)
        self._graph_shade.connectPath(path)

    def paint(self, p: QPainter, *args) -> None:
        """Override."""
        if self._graph is None:
            self._prepareGraph()

        p.setPen(self._pen)
        p.setBrush(FColor.mkBrush())
        p.drawPath(self._graph)

        p.setPen(FColor.mkPen())
        p.setBrush(self._brush)
        p.drawPath(self._graph_shade)

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return self._graph.boundingRect()

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Override."""
        if p is not None:
            p.setPen(self._pen)
            # Legend sample has a bounding box of (0, 0, 20, 20)
            p.drawLine(0, 11, 20, 11)
        return True
