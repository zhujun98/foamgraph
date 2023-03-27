"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

import numpy as np

from ...backend.QtGui import QPainter, QPainterPath, QPixmap, QTransform
from ...backend.QtCore import QRectF, Qt
from ...aesthetics import FColor, FSymbol
from .plot_item import PlotItem


class StemPlotItem(PlotItem):
    """ScatterPlotItem."""

    def __init__(self, x=None, y=None, *, symbol='o', size=6,
                 pen=None, brush=None, baseline_pen=None, label=None):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        if pen is None and brush is None:
            self._pen = FColor.mkPen('b')
            self._brush = FColor.mkBrush('b')
        elif pen is None:
            self._pen = FColor.mkPen(brush.color())
            self._brush = brush
        elif brush is None:
            self._pen = pen
            self._brush = None

        if baseline_pen is None:
            self._pen_baseline = FColor.mkPen('foreground')
        else:
            self._pen_baseline = baseline_pen

        self._size = size

        self._symbol_path = FSymbol.mkSymbol(symbol)
        self._fragment = None
        self._buildFragment()

        self._graph = None
        self._graph_baseline = None

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

    def _prepareGraph(self) -> None:
        """Override."""
        path = QPainterPath()
        x, y = self.transformedData()
        for px, py in zip(x, y):
            path.moveTo(px, 0)
            path.lineTo(px, py)

        self._graph = path

        path = QPainterPath()
        if len(x) > 1:
            path.moveTo(x[0], 0)
            path.lineTo(x[-1], 0)
        self._graph_baseline = path

    @staticmethod
    def transformCoordinates(matrix: QTransform, x: np.array, y: np.array,
                             dx: float = 0, dy: float = 0) -> tuple:
        # TODO: do it inplace?
        x = matrix.m11() * x + matrix.m21() * y + matrix.m31() + dx
        y = matrix.m12() * x + matrix.m22() * y + matrix.m32() + dy
        return x, y

    def paint(self, p, *args) -> None:
        """Override."""
        p.setPen(self._pen_baseline)
        p.drawPath(self._graph_baseline)

        p.setPen(self._pen)
        p.drawPath(self._graph)

        x, y = self.transformedData()
        w, h = self._fragment.width(), self._fragment.height()
        x, y = self.transformCoordinates(
            self.deviceTransform(), x, y, -w / 2., -h / 2.)
        src_rect = QRectF(self._fragment.rect())

        p.resetTransform()
        for px, py in zip(x, y):
            p.drawPixmap(QRectF(px, py, w, h), self._fragment, src_rect)

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return self._graph.boundingRect()

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Override."""
        if p is not None:
            p.translate(10, 10)
            self._drawSymbol(p)
            p.setPen(self._pen)
            p.drawLine(0, 1, 0, 0)

        return True

    def _drawSymbol(self, p: QPainter) -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self._size, self._size)
        if self._brush is None:
            p.setPen(self._pen)
            p.setBrush(FColor.mkBrush())
        else:
            p.setPen(FColor.mkPen())
            p.setBrush(self._brush)
        p.drawPath(self._symbol_path)

    def _buildFragment(self):
        size = int(self._size + max(np.ceil(self._pen.widthF()), 1))
        symbol = QPixmap(size, size)
        symbol.fill(FColor.mkColor('w', alpha=0))
        p = QPainter(symbol)
        center = 0.5 * size
        p.translate(center, center)
        self._drawSymbol(p)
        p.end()

        self._fragment = symbol
