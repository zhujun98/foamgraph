"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from foamgraph.backend.QtCore import QTimer
from foamgraph.backend.QtWidgets import QFrame, QGridLayout

from foamgraph import (
    AbstractScene, FColor, mkQApp, GraphView, TimedGraphView
)

from consumer import Consumer

app = mkQApp()


class LinePlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Line plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot = self.addCurvePlot()

    def updateF(self, data):
        """Override."""
        data = data['line']
        self._plot.setData(data['x'], data['y'])


class ScatterPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Scatter plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot1 = self.addScatterPlot(label="Data1", symbol="d", size=9)
        self._plot2 = self.addScatterPlot(
            label="Data2", brush=FColor.mkBrush('Purple', alpha=150), size=7)
        self._plot3 = self.addScatterPlot(
            label="Data3", brush=None, pen=FColor.mkPen('y'), symbol="s")
        self._plot4 = self.addScatterPlot(
            label="Data4", pen=FColor.mkPen('k'), symbol="+")
        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['scatter']
        self._plot1.setData(data['x1'], data['y1'])
        self._plot2.setData(data['x2'], data['y2'])
        self._plot3.setData(data['x3'], data['y3'])
        self._plot4.setData(data['x4'], data['y4'])


class BarPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Bar plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot = self.addBarPlot(pen=FColor.mkPen('ForestGreen'),
                                  brush=FColor.mkBrush('DodgerBlue'))

    def updateF(self, data):
        """Override."""
        data = data['bar']
        self._plot.setData(data['x'], data['y'])


class ErrorbarPlot(TimedGraphView):
    def __init__(self, *, parent=None):
        super().__init__(1000, parent=parent)

        self.setTitle('Timed error-bar plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot1 = self.addErrorbarPlot(
            beam=1, pen=FColor.mkPen('Orange'))
        self._plot2 = self.addCurvePlot(
            pen=FColor.mkPen('Orange', width=2))

    def refresh(self):
        """Override."""
        data = self._data['errorbar']
        self._plot1.setData(data['x'], data['y'], data['y_min'], data['y_max'])
        self._plot2.setData(data['x'], data['y'])


class MultiLinePlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Multi-line plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot1 = self.addCurvePlot(
            label='Line A', pen=FColor.mkPen('k', width=2))
        self._plot2 = self.addCurvePlot(
            label='Line B', pen=FColor.mkPen('b', width=2))
        self._plot3 = self.addCurvePlot(
            label='Line C', pen=FColor.mkPen('r', width=2))

        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['multi-line']
        self._plot1.setData(data['x'], data['y1'])
        self._plot2.setData(data['x'], data['y2'])
        self._plot3.setData(data['x'], data['y3'])


class DoubleYPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Double-y plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot = self.addCurvePlot(pen=FColor.mkPen('Brown'))
        self._plot1 = self.addScatterPlot(
            label="Data", symbol='o', pen=FColor.mkPen('Brown'))
        self._plot2 = self.addBarPlot(
            label="Count", y2=True, brush=FColor.mkBrush('Silver', alpha=150))
        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['double-y']
        self._plot.setData(data['x'], data['y'])
        self._plot1.setData(data['x'], data['y'])
        self._plot2.setData(data['x'], data['y2'])


class LinePlotWithAnnotation(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Line plot with peak annotation')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot = self.addCurvePlot(label="Data", pen=FColor.mkPen('k'))
        self._annotation = self.addAnnotation()
        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['multi-peak']
        x, y, peaks = data['x'], data['y'], data['peaks']
        self._plot.setData(x, y)
        self._annotation.setData(x[peaks], y[peaks], annotations=x[peaks])


class PlotGalleryScene(AbstractScene):
    _title = "Plot gallery"

    _TOTAL_W, _TOTAL_H = 1440, 1080

    def __init__(self, *args, **kwargs):
        """Initialization."""
        super().__init__(*args, **kwargs)

        self._plots = [
            LinePlot(parent=self),
            ScatterPlot(parent=self),
            BarPlot(parent=self),
            ErrorbarPlot(parent=self),
            MultiLinePlot(parent=self),
            DoubleYPlot(parent=self),
            LinePlotWithAnnotation(parent=self)
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
        layout.addWidget(self._plots[-1], 2, 0)

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

    app.exec()
