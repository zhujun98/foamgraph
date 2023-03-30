"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from foamgraph.backend.QtCore import QTimer
from foamgraph.backend.QtWidgets import QFrame, QGridLayout
from foamgraph import (
    LiveWindow, FColor, mkQApp, GraphView, TimedGraphView
)

from consumer import Consumer

app = mkQApp()


class ShadedPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Shaded plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot1 = self.addCurvePlot(pen=FColor.mkPen('Gray', width=2))

        self._plot2 = self.addShadedPlot(pen=FColor.mkPen('DodgerBlue'))

    def updateF(self, data):
        """Override."""
        data = data['line']
        self._plot1.setData(data['x'], data['y3'], data['y3_err'])
        self._plot2.setData(data['x'], data['y1'], data['y2'])


class ScatterPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Scatter plot (aspect ratio locked)')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot1 = self.addScatterPlot(label="Data1", symbol="d", size=9)
        self._plot2 = self.addScatterPlot(
            label="Data2", brush=FColor.mkBrush('Purple', alpha=50), size=7)
        self._plot3 = self.addScatterPlot(
            label="Data3", brush=None, pen=FColor.mkPen('Brown', alpha=100), symbol="s")
        self._plot4 = self.addScatterPlot(
            label="Data4", pen=FColor.mkPen('k', alpha=150), symbol="+")
        self.addLegend()
        self.setAspectLocked(True)

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
        self.addLegend()  # add legend before plots

        self._plot1 = self.addCurvePlot(
            label='Line A', pen=FColor.mkPen('k', width=1))
        self._plot2 = self.addCurvePlot(
            label='Line B', pen=FColor.mkPen('b', width=2))
        self._plot3 = self.addCurvePlot(
            label='Line C', pen=FColor.mkPen('r', width=3))

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
        self.setXYLabels("x (arb. u.)", "y (arb. u.)", y2="y2 (arg. u.)")

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

        self._plot = self.addCurvePlot(simple=True, pen=FColor.mkPen('k'))
        self._annotation = self.addAnnotation()

    def updateF(self, data):
        """Override."""
        data = data['multi-peak']
        x, y, peaks = data['x'], data['y'], data['peaks']
        self._plot.setData(x, y)
        self._annotation.setData(x[peaks], y[peaks], annotations=x[peaks])


class CandlestickPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Candlestick plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot = self.addCandlestickPlot()

    def updateF(self, data):
        """Override."""
        data = data['candlestick']
        self._plot.setData(data['x'], data['y_start'], data['y_end'],
                           data['y_min'], data['y_max'])


class StemPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Stem plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)")

        self._plot1 = self.addStemPlot(
            label="Data1", symbol="s", pen=FColor.mkPen('DodgerBlue'))
        self._plot2 = self.addStemPlot(
            label="Data2", symbol="o", brush=FColor.mkBrush('DarkOrange'))
        self.addLegend()

    def updateF(self, data):
        """Override."""
        data = data['stem']
        self._plot1.setData(data['x'], data['y1'])
        self._plot2.setData(data['x'], data['y2'])


class PlotGalleryWindow(LiveWindow):

    def __init__(self):
        super().__init__("Plot gallery")

        self._plots = [
            ShadedPlot(parent=self),
            ScatterPlot(parent=self),
            BarPlot(parent=self),
            ErrorbarPlot(parent=self),
            MultiLinePlot(parent=self),
            DoubleYPlot(parent=self),
            LinePlotWithAnnotation(parent=self),
            CandlestickPlot(parent=self),
            StemPlot(parent=self)
        ]

        self.init()

        self._timer = QTimer()
        self._timer.timeout.connect(self.updateWidgetsF)
        self._timer.start(100)

    def initUI(self):
        """Override."""
        layout = QGridLayout()
        rows, cols = 3, 3
        for i in range(rows):
            for j in range(cols):
                layout.addWidget(self._plots[cols * i + j], i, j)

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

        w, h = 1440, 1080
        self.resize(w, h)
        self.setMinimumSize(int(0.6 * w), int(0.6 * h))

    def initConnections(self):
        """Override."""
        ...


if __name__ == "__main__":
    win = PlotGalleryWindow()

    consumer = Consumer(win.queue)
    consumer.start()

    app.exec()
