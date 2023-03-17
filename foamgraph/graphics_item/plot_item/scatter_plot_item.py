"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

import numpy as np

from ...backend.QtGui import QPainter, QPixmap, QTransform
from ...backend.QtCore import QRectF, Qt
from ...aesthetics import FColor, FSymbol
from .plot_item import PlotItem


class ScatterPlotItem(PlotItem):
    """ScatterPlotItem."""

    def __init__(self, x=None, y=None, *, symbol='o', size=8,
                 pen=None, brush=None, label=None):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        if pen is None and brush is None:
            self._pen = FColor.mkPen()
            self._brush = FColor.mkBrush('b')
        else:
            self._pen = FColor.mkPen() if pen is None else pen
            self._brush = FColor.mkBrush() if brush is None else brush

        self._size = size

        self._symbol_path = FSymbol.mkSymbol(symbol)
        self._fragment = None
        self._buildFragment()

        self._graph = None

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

    def _computePaddings(self) -> tuple[float, float]:
        w, h = self._fragment.width(), self._fragment.height()
        canvas = self.canvas()
        if canvas is None:
            return 0, 0
        rect = canvas.mapSceneToView(QRectF(0, 0, w, h)).boundingRect()
        return rect.width(), rect.height()

    def _prepareGraph(self) -> None:
        """Override."""
        self._graph = QRectF()
        if len(self._x) == 0:
            return

        x, y = self.transformedData()
        x_min, x_max = np.nanmin(x), np.nanmax(x)
        y_min, y_max = np.nanmin(y), np.nanmax(y)
        if np.isnan(x_min) or np.isnan(x_max):
            x_min, x_max = 0, 0
        if np.isnan(y_min) or np.isnan(y_max):
            y_min, y_max = 0, 0

        padding_x, padding_y = self._computePaddings()

        self._graph.setRect(x_min - padding_x,
                            y_min - padding_y,
                            x_max - x_min + 2 * padding_x,
                            y_max - y_min + 2 * padding_y)

    @staticmethod
    def transformCoordinates(matrix: QTransform, x: np.array, y: np.array,
                             dx: float = 0, dy: float = 0) -> tuple:
        # TODO: do it inplace?
        x = matrix.m11() * x + matrix.m21() * y + matrix.m31() + dx
        y = matrix.m12() * x + matrix.m22() * y + matrix.m32() + dy
        return x, y

    def paint(self, p, *args) -> None:
        """Override."""
        p.resetTransform()

        x, y = self.transformedData()
        w, h = self._fragment.width(), self._fragment.height()
        x, y = self.transformCoordinates(
            self.deviceTransform(), x, y, -w / 2., -h / 2.)
        src_rect = QRectF(self._fragment.rect())
        for px, py in zip(x, y):
            p.drawPixmap(QRectF(px, py, w, h), self._fragment, src_rect)

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return self._graph

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Override."""
        if p is not None:
            p.translate(10, 10)
            self._drawSymbol(p)
        return True

    def _drawSymbol(self, p: QPainter) -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self._size, self._size)
        p.setPen(self._pen)
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
