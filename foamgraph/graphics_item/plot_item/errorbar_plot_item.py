"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

from ...backend.QtCore import QRectF
from ...backend.QtGui import QPainter, QPainterPath
from ...aesthetics import FColor
from .plot_item import PlotItem


class ErrorbarPlotItem(PlotItem):
    """ErrorbarPlotItem."""

    def __init__(self, x=None, y=None, *, y_min=None, y_max=None, beam=None,
                 line=False, pen=None, label=None):
        """Initialization.

        Note: y is not used for now.
        """
        super().__init__(label=label)

        self._x = None
        self._y = None
        self._y_min = None
        self._y_max = None

        self._beam = 0.0 if beam is None else beam
        self._line = line
        self._pen = FColor.mkPen('m') if pen is None else pen

        self.setData(x, y, y_min=y_min, y_max=y_max)

    def _parseInputData(self, x, **kwargs):
        """Override."""
        x = self._parse_input(x)

        size = len(x)
        y = self._parse_input(kwargs['y'], size=size)
        y_min = self._parse_input(kwargs['y_min'], size=size, default=y)
        y_max = self._parse_input(kwargs['y_max'], size=size, default=y)

        # do not set data unless they pass the sanity check!
        self._x, self._y, self._y_min, self._y_max = x, y, y_min, y_max

    def setData(self, x, y, y_min=None, y_max=None, beam=None) -> None:
        """Override."""
        self._parseInputData(x, y=y, y_min=y_min, y_max=y_max)

        if beam is not None:
            # keep the default beam if not specified
            self._beam = beam

        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [])

    def data(self):
        """Override."""
        return self._x, self._y, self._y_min, self._y_max

    def setBeam(self, width: float) -> None:
        self._beam = width

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Override."""
        if p is not None:
            p.setPen(self._pen)
            # Legend sample has a bounding box of (0, 0, 20, 20)
            p.drawLine(2, 2, 8, 2)  # lower horizontal line
            p.drawLine(5, 2, 5, 18)  # vertical line
            p.drawLine(2, 18, 8, 18)  # upper horizontal line
        return True

    def transformedData(self) -> tuple:
        """Override."""
        y_min = self.toLogScale(self._y_min) if self._log_y_mode else self._y_min
        y_max = self.toLogScale(self._y_max) if self._log_y_mode else self._y_max
        return super().transformedData() + (y_min, y_max)

    def _prepareGraph(self) -> None:
        p = QPainterPath()

        x, y, y_min, y_max = self.transformedData()
        beam = self._beam
        for px, u, l in zip(x, y_min, y_max):
            # plot the lower horizontal lines
            p.moveTo(px - beam / 2., l)
            p.lineTo(px + beam / 2., l)

            # plot the vertical line
            p.moveTo(px, l)
            p.lineTo(px, u)

            # plot the upper horizontal line
            p.moveTo(px - beam / 2., u)
            p.lineTo(px + beam / 2., u)

        if self._line and len(x) > 2:
            p.moveTo(x[-1], y[-1])
            for px, py in zip(reversed(x[:-1]), reversed(y[:-1])):
                p.lineTo(px, py)

        self._graph = p

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
