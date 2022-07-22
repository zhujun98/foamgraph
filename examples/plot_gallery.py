from collections import deque

import zmq

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFrame, QGridLayout

from foamgraph import (
    AbstractScene, FColor, mkQApp, PlotWidgetF, TimedPlotWidgetF
)

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
        try:
            data = data["line"]
        except KeyError:
            return

        self._plot.setData(data['x'], data['y'])


class ScatterPlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Scatter plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot = self.plotScatter()

    def updateF(self, data):
        """Override."""
        try:
            data = data["scatter"]
        except KeyError:
            return

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
        try:
            data = data["bar"]
        except KeyError:
            return

        self._plot.setData(data['x'], data['y'])


class ErrorbarPlot(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Error-bar plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot = self.plotErrorbar(beam=1)

    def updateF(self, data):
        """Override."""
        try:
            data = data["errorbar"]
        except KeyError:
            return

        self._plot.setData(data['x'], data['y'], data['y_min'], data['y_max'])


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
            name='Line C', pen=FColor.mkPen('o', width=2))

        self.addLegend()

    def updateF(self, data):
        """Override."""
        try:
            data = data["multi-line"]
        except KeyError:
            return

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
        self._plot2 = self.plotBar(
            name="Count", y2=True, brush=FColor.mkBrush('i', alpha=150))
        self.addLegend()

    def updateF(self, data):
        """Override."""
        try:
            data = data["double-y"]
        except KeyError:
            return

        self._plot.setData(data['x'], data['y'])
        self._plot2.setData(data['x'], data['y2'])


class TimedScatterPlot(TimedPlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Timed scatter plot')
        self.setLabel('bottom', "x (arb. u.)")
        self.setLabel('left', "y (arb. u.)")

        self._plot = self.plotScatter()

    def refresh(self):
        """Override."""
        ...


class PlotGalleryScene(AbstractScene):
    _title = "Plot gallery"

    _TOTAL_W, _TOTAL_H = 1920, 1080

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


class Consumer:
    def __init__(self, queue: deque):
        self._ctx = zmq.Context()
        self._socket = self._ctx.socket(zmq.SUB)
        self._socket.connect("tcp://localhost:5555")
        self._socket.setsockopt(zmq.SUBSCRIBE, b"")

        self._deque = queue

        from threading import Thread
        self._thread = Thread(target=self._consume, daemon=True)

    def _consume(self):
        import pickle
        while True:
            data = pickle.loads(self._socket.recv())
            queue.append(data)

    def start(self):
        self._thread.start()


if __name__ == "__main__":
    queue = deque(maxlen=5)

    scene = PlotGalleryScene(queue)

    consumer = Consumer(queue)
    consumer.start()

    app.exec_()
