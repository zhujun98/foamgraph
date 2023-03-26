"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

import numpy as np

from ...backend import sip
from ...backend.QtGui import QPainter, QPainterPath, QPolygonF
from ...backend.QtCore import QPointF, QRectF, Qt
from ...aesthetics import FColor
from .plot_item import PlotItem


class CurvePlotItem(PlotItem):
    """CurvePlotItem."""

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

    @staticmethod
    def array2Path(x, y) -> QPainterPath:
        """Convert array to QPainterPath."""
        n = x.shape[0]
        if n < 2:
            return QPainterPath()

        polyline = QPolygonF()
        polyline.fill(QPointF(), n)

        buffer = polyline.data()
        if buffer is None:
            buffer = sip.voidptr(0)
        buffer.setsize(2 * n * np.dtype(np.double).itemsize)

        arr = np.frombuffer(buffer, np.double).reshape((-1, 2))

        arr[:, 0] = x
        arr[:, 1] = y
        path = QPainterPath()
        path.addPolygon(polyline)
        return path

    def _prepareGraph(self) -> None:
        """Override."""
        x, y = self.transformedData()
        self._graph = self.array2Path(x, y)

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
