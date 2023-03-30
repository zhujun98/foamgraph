"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import argparse
import time
from collections import deque

import numpy as np

from foamgraph.backend.QtCore import QTimer

from foamgraph import mkQApp, GraphView

app = mkQApp()


class BenchmarkPlotItemSpeed:
    def __init__(self, plot_type, n_pts, *, pyqtgraph=False):
        self._dt = deque(maxlen=60)

        self._timer = QTimer()
        self._timer.timeout.connect(self.update)

        self._x = np.arange(n_pts).astype(float)
        self._data = 100 * np.random.normal(size=(50, n_pts)).astype(float)
        if plot_type == "errorbar":
            self._y_min = self._data - 20
            self._y_max = self._data + 20

        if pyqtgraph:
            import pyqtgraph as pg
            self._widget = pg.plot()
            if plot_type == "curve":
                self._graph = pg.PlotCurveItem()
            elif plot_type == "scatter":
                self._graph = pg.ScatterPlotItem()
            elif plot_type == "bar":
                class BarPlotItem(pg.BarGraphItem):
                    def setData(self, x, y):
                        self.setOpts(x=x, height=y)
                self._graph = BarPlotItem(
                    x=self._x, height=self._data[0], width=1.0)
            elif plot_type == "errorbar":
                class ErrorBarItem(pg.ErrorBarItem):
                    def setData(self, x, y, y_min, y_max, **kwargs):
                        super().setData(
                            x=x, y=y, bottom=y_min, top=y_max, **kwargs)

                self._graph = ErrorBarItem(x=self._x,
                                           y=self._data[0],
                                           y_min=self._y_min[0],
                                           y_max=self._y_max[0],
                                           beam=1)
            else:
                raise ValueError(f"Unsupported plot type: {plot_type}")
            self._widget.addItem(self._graph)
        else:
            self._widget = GraphView()
            self._widget.addLegend()

            if plot_type == "curve":
                self._graph = self._widget.addCurvePlot(label=plot_type)
            elif plot_type == "scatter":
                self._graph = self._widget.addScatterPlot(label=plot_type)
            elif plot_type == "bar":
                self._graph = self._widget.addBarPlot(label=plot_type, width=1.0)
            elif plot_type == "errorbar":
                self._graph = self._widget.addErrorbarPlot(
                    label=plot_type, beam=1.0)
            else:
                raise ValueError(f"Unsupported plot type: {plot_type}")
        self._plot_type = plot_type

        screen_geometry = self._widget.screen().geometry()
        wc, hc = int(screen_geometry.width() / 2), int(screen_geometry.height() / 2)
        self._widget.setGeometry(wc - 400, hc - 300, 800, 600)

        self._prev_t = None
        self._count = 0
        self._fps = 0

        self._widget.show()

    def start(self):
        self._prev_t = time.time()
        self._timer.start(0)

    def close(self):
        self._timer.stop()
        self._widget.close()

    def update(self):
        idx = self._count % len(self._data)
        if self._plot_type == "errorbar":
            self._graph.setData(x=self._x,
                                y=self._data[idx],
                                y_min=self._y_min[idx],
                                y_max=self._y_max[idx])
        else:
            self._graph.setData(x=self._x, y=self._data[idx])

        self._count += 1

        now = time.time()
        self._dt.append(now - self._prev_t)
        self._prev_t = now
        self._fps = len(self._dt) / sum(self._dt)

        self._widget.setTitle(f"{self._fps:.2f} fps")

        app.processEvents()  # force complete redraw for every plot

    def callback(self):
        print(f"{self._fps:.2f} fps")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('plot_type', type=str, default='scatter')
    parser.add_argument('pts', type=int, default=10)
    parser.add_argument('--timeout', type=int, default=6,
                        help="Run time in seconds")
    parser.add_argument('--pyqtgraph', action='store_true')

    args = parser.parse_args()

    bench = BenchmarkPlotItemSpeed(args.plot_type, args.pts,
                                   pyqtgraph=args.pyqtgraph)
    bench.start()

    timer = QTimer()
    timer.timeout.connect(bench.close)
    timer.start(args.timeout * 1000)

    timer2 = QTimer()
    timer2.timeout.connect(bench.callback)
    timer2.start(1000)

    app.exec()
