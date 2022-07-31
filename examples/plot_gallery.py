"""
Distributed under the terms of the MIT License.

The full license is in the file LICENSE, distributed with this software.

Copyright (C) Jun Zhu. All rights reserved.
"""
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFrame, QGridLayout

from foamgraph import (
    AbstractScene, FColor, mkQApp, PlotWidgetF, TimedPlotWidgetF
)

from consumer import Consumer

app = mkQApp()


class LinePlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Line plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot = self.plotCurve()

    def updateF(self, data):
        """Override."""
        data = data['line']
        self._plot.setData(data['x'], data['y'])


class ScatterPlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Scatter plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot = self.plotScatter(brush=FColor.mkBrush('p', alpha=150))

    def updateF(self, data):
        """Override."""
        data = data['scatter']
        self._plot.setData(data['x'], data['y'])


class BarPlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Bar plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot = self.plotBar(
            pen=FColor.mkPen('s'), brush=FColor.mkBrush('b'))

    def updateF(self, data):
        """Override."""
        data = data['bar']
        self._plot.setData(data['x'], data['y'])


class ErrorbarPlot(TimedPlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(1000, parent=parent)

        self.setTitle('Timed error-bar plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot1 = self.plotErrorbar(
            beam=1, pen=FColor.mkPen('o'))
        self._plot2 = self.plotCurve(pen=FColor.mkPen('o', width=2))

    def refresh(self):
        """Override."""
        data = self._data['errorbar']
        self._plot1.setData(data['x'], data['y'], data['y_min'], data['y_max'])
        self._plot2.setData(data['x'], data['y'])


class MultiLinePlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Multi-line plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot1 = self.plotCurve(
            name='Line A', pen=FColor.mkPen('k', width=2))
        self._plot2 = self.plotCurve(
            name='Line B', pen=FColor.mkPen('b', width=2))
        self._plot3 = self.plotCurve(
            name='Line C', pen=FColor.mkPen('c', width=2))

        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['multi-line']
        self._plot1.setData(data['x'], data['y1'])
        self._plot2.setData(data['x'], data['y2'])
        self._plot3.setData(data['x'], data['y3'])


class DoubleYPlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Double-y plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")
        self.setLabel('right', "y2 (arg. u.)")

        self._plot = self.plotCurve(name="Data", pen=FColor.mkPen('w'))
        self._plot1 = self.plotScatter(symbol='x', pen=FColor.mkPen('w'))
        self._plot2 = self.plotBar(
            name="Count", y2=True, brush=FColor.mkBrush('i', alpha=150))
        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['double-y']
        self._plot.setData(data['x'], data['y'])
        self._plot1.setData(data['x'], data['y'])
        self._plot2.setData(data['x'], data['y2'])


class PlotGalleryScene(AbstractScene):
    _title = "Plot gallery"

    _TOTAL_W, _TOTAL_H = 1440, 720

    def __init__(self, *args, **kwargs):
        """Initialization."""
        super().__init__(*args, **kwargs)

        self._plots = [
            LinePlot(parent=self),
            ScatterPlot(parent=self),
            BarPlot(parent=self),
            ErrorbarPlot(parent=self),
            MultiLinePlot(parent=self),
            DoubleYPlot(parent=self)
        ]

        self.initUI()
        self.initConnections()

        self.resize(self._TOTAL_W, self._TOTAL_H)
        self.setMinimumSize(int(0.6 * self._TOTAL_W), int(0.6 * self._TOTAL_H))

        self._timer = QTimer()
        self._timer.timeout.connect(self.updateWidgetsF)
        self._timer.start(100)

    def initUI(self):
        """Override."""
        layout = QGridLayout()
        rows, cols = 2, 3
        for i in range(rows):
            for j in range(cols):
                layout.addWidget(self._plots[cols * i + j], i, j)

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

    def initConnections(self):
        """Override."""
        ...


if __name__ == "__main__":
    scene = PlotGalleryScene()

    consumer = Consumer(scene.queue)
    consumer.start()

    app.exec_()
