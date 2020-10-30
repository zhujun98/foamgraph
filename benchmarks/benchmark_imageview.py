"""
Distributed under the terms of the MIT License.

The full license is in the file LICENSE, distributed with this software.

Copyright (C) Jun Zhu. All rights reserved.
"""
import argparse
from collections import deque
import time

import numpy as np

from PyQt5.QtCore import QTimer

from foamgraph import ImageViewF, mkQApp

app = mkQApp()


class BenchmarkImageViewSpeed:
    def __init__(self):
        self._dt = deque(maxlen=60)

        self._timer = QTimer()
        self._timer.timeout.connect(self.update)

        self._data = np.random.normal(size=(50, 1024, 1280))
        self._prev_t = None
        self._count = 0

        self._view = ImageViewF()
        self._view.show()

    def start(self):
        self._prev_t = time.time()
        self._timer.start(0)

    def close(self):
        self._timer.stop()
        self._view.close()

    def update(self):
        self._view.setImage(self._data[self._count % 10])
        self._count += 1

        now = time.time()
        self._dt.append(now - self._prev_t)
        self._prev_t = now
        fps = len(self._dt) / sum(self._dt)

        self._view.setTitle(f"{fps:.2f} fps")

        app.processEvents()  # force complete redraw for every plot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--single_shot', action='store_true')

    args = parser.parse_args()

    bench = BenchmarkImageViewSpeed()
    bench.start()

    timer = QTimer()
    if args.single_shot:
        timer.timeout.connect(bench.close)
    timer.start(1000)

    app.exec_()
