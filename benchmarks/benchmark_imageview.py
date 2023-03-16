"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import argparse
from collections import deque
import time

import numpy as np

from foamgraph.backend.QtCore import QTimer

from foamgraph import ImageView, mkQApp

app = mkQApp()


class BenchmarkImageViewSpeed:
    def __init__(self, dtype, *, pyqtgraph=False, grayscale=False):
        self._dt = deque(maxlen=60)

        self._timer = QTimer()
        self._timer.timeout.connect(self.update)

        self._data = np.random.normal(size=(50, 1024, 1280)).astype(dtype)
        self._prev_t = None
        self._count = 0
        self._fps = None

        if pyqtgraph:
            import pyqtgraph as pg
            self._view = pg.ImageView()
            if not grayscale:
                self._view.ui.histogram.gradient.loadPreset("plasma")
        else:
            self._view = ImageView()
            if grayscale:
                self._view.setColorMap("grey")
        self._view.show()

    def start(self):
        self._prev_t = time.time()
        self._timer.start(0)

    def close(self):
        self._timer.stop()
        self._view.close()

    def update(self):
        self._view.setImage(self._data[self._count % len(self._data)])
        self._count += 1

        now = time.time()
        self._dt.append(now - self._prev_t)
        self._prev_t = now
        self._fps = len(self._dt) / sum(self._dt)

        try:
            self._view.setTitle(f"{self._fps:.2f} fps")
        except AttributeError:
            pass

        app.processEvents()  # force complete redraw for every plot

    def callback(self):
        print(f"{self._fps:.2f} fps")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pyqtgraph', action='store_true')
    parser.add_argument('--grayscale', action='store_true')
    parser.add_argument('--dtype', type=str, default='float')
    parser.add_argument('--timeout', type=int, default=6,
                        help="Run time in seconds")
    args = parser.parse_args()

    dtype = args.dtype
    if dtype == 'double':
        dtype = np.float64
    elif dtype == 'float':
        dtype = np.float32
    elif dtype == 'uint16':
        dtype = np.uint16
    else:
        raise ValueError(f"Unknown image dtype: {dtype}")

    bench = BenchmarkImageViewSpeed(dtype,
                                    pyqtgraph=args.pyqtgraph,
                                    grayscale=args.grayscale)
    bench.start()

    timer = QTimer()
    timer.timeout.connect(bench.close)
    timer.start(args.timeout * 1000)

    timer2 = QTimer()
    timer2.timeout.connect(bench.callback)
    timer2.start(1000)

    app.exec()
