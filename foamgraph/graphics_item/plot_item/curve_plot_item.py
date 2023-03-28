"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

import numpy as np

from ...backend.QtGui import QPainter, QPainterPath
from ...backend.QtCore import QRectF, Qt
from ...aesthetics import FColor
from .plot_item import PlotItem


class SimpleCurvePlotItem(PlotItem):
    """SimpleCurvePlotItem."""

    def __init__(self, x=None, y=None, *,
                 pen=None, label=None, check_finite=True):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        self._pen = FColor.mkPen('g') if pen is None else pen

        self._check_finite = check_finite

        self.setData(x, y)

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

    def transformedData(self) -> tuple:
        """Override."""
        if not self._check_finite:
            return super().transformedData()

        # inf/nans completely prevent the plot from being displayed starting on
        # Qt version 5.12.3
        # we do not expect to have nan in x
        return (self.toLogScale(self._x) if self._log_x_mode else self._x,
                self.toLogScale(self._y)
                if self._log_y_mode else np.nan_to_num(self._y))

    def _prepareGraph(self) -> None:
        """Override."""
        x, y = self.transformedData()
        self._graph = QPainterPath()
        polygon = PlotItem.array2Polygon(x, y)
        self._graph.addPolygon(polygon)

    def paint(self, p: QPainter, *args) -> None:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        p.setPen(self._pen)
        p.drawPath(self._graph)

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


class CurvePlotItem(SimpleCurvePlotItem):
    """CurvePlotItem.

    :class:`CurvePlotItem` is a "class"`SimpleCurvePlotItem`. The former
    should be able to use as a drop-in replacement of the latter.
    """

    def __init__(self, x=None, y=None, y_err=None, *, brush=None, **kwargs):
        """Initialization."""
        super().__init__(None, None, **kwargs)

        self._brush = FColor.mkBrush(self._pen.color(), alpha=100) \
            if brush is None else brush

        self._y_err = None
        self._graph_shade = None

        self.setData(x, y, y_err)

    def _parseInputData(self, x, **kwargs):
        """Override."""
        x = self._parse_input(x)
        y = self._parse_input(kwargs['y'], size=len(x))
        y_err = self._parse_input(kwargs['y_err'])
        if y_err.size != 0 and len(y_err) != len(y):
            raise ValueError("'y' and 'y_err' data have different lengths!")

        # do not set data unless they pass the sanity check!
        self._x, self._y, self._y_err = x, y, y_err

    def setData(self, x, y, y_err=None) -> None:
        """Override."""
        self._parseInputData(x, y=y, y_err=y_err)
        self.updateGraph()

    def data(self):
        """Override."""
        return self._x, self._y, self._y_err

    def _prepareGraph(self) -> None:
        """Override."""
        x, y = self.transformedData()
        self._graph = QPainterPath()
        polygon = PlotItem.array2Polygon(x, y)
        self._graph.addPolygon(polygon)

        if not self._y_err.size == 0:
            self._graph_shade = QPainterPath()
            polygon1 = PlotItem.array2Polygon(x, y + self._y_err)
            self._graph_shade.addPolygon(polygon1)
            path = QPainterPath()
            polygon2 = PlotItem.array2Polygon(x[::-1], (y - self._y_err)[::-1])
            path.addPolygon(polygon2)
            self._graph_shade.connectPath(path)
        else:
            self._graph_shade = None

    def paint(self, p: QPainter, *args) -> None:
        """Override."""
        if self._graph is None:
            self._prepareGraph()

        p.setPen(self._pen)
        p.setBrush(FColor.mkBrush())
        p.drawPath(self._graph)

        if self._graph_shade is not None:
            p.setPen(FColor.mkPen())
            p.setBrush(self._brush)
            p.drawPath(self._graph_shade)

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        if self._graph_shade is None:
            return self._graph.boundingRect()
        return self._graph_shade.boundingRect()
