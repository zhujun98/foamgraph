import argparse
import pickle
import time

import numpy as np
from scipy import signal
import zmq


class LinePlotData:
    def __init__(self, n: int):
        self._n_pts = n

    def next(self):
        x = np.arange(self._n_pts).astype(np.float32)
        x[0] = np.nan
        x[2] = np.nan
        y = np.random.random(self._n_pts).astype(np.float32)
        y[1] = np.nan
        y[2] = np.nan
        return {"x": x, "y": y}


class ScatterPlotData:
    def __init__(self, n: int):
        self._n_pts = n

        self._x1 = np.random.normal(0, 1, self._n_pts)
        self._y1 = np.random.normal(0, 1, self._n_pts)
        self._x1[0] = np.nan
        self._x1[2] = np.nan
        self._y1[1] = np.nan
        self._y1[2] = np.nan

        self._x2 = np.random.normal(10, 0.8, self._n_pts)
        self._y2 = np.random.normal(5, 0.8, self._n_pts)

        self._x3 = np.random.normal(8, 1.2, self._n_pts)
        self._y3 = np.random.normal(-3, 1.2, self._n_pts)

        self._x4 = np.random.normal(6, 0.5, self._n_pts)
        self._y4 = np.random.normal(1, 0.5, self._n_pts)

        self._counter = 0

    def next(self):
        if self._counter == self._n_pts:
            self._counter = 0
        self._counter += 1

        return {
            "x1": self._x1[:self._counter], "y1": self._y1[:self._counter],
            "x2": self._x2[:self._counter], "y2": self._y2[:self._counter],
            "x3": self._x3[:self._counter], "y3": self._y3[:self._counter],
            "x4": self._x4[:self._counter], "y4": self._y4[:self._counter]
        }


class ErrorBarPlotData:
    def __init__(self, n: int):
        self._x = np.arange(n)
        size = 2000
        self._data = np.random.randn(size * n).reshape(n, size)
        self._scale = np.random.random(n)

        self._counter = 0

    def next(self):
        if self._counter == len(self._x):
            self._counter = 0
        self._counter += 1

        data_slice = self._data[:, :self._counter]
        y = np.mean(data_slice, axis=1)
        err = np.std(data_slice, axis=1) * self._scale
        return {"x": self._x,
                "y": y,
                "y_min": y - err,
                "y_max": y + err}


class MultiLinePlotData:
    def __init__(self, n: int):
        self._x = np.arange(n)
        self._y1 = np.random.random(n)
        self._y2 = 2 + np.random.random(n)
        self._y3 = 4 + np.random.random(n)

        self._counter = 0

    def next(self):
        if self._counter == len(self._x):
            self._counter = 0
        self._counter += 1

        return {"x": self._x[:self._counter],
                "y1": self._y1[:self._counter],
                "y2": self._y2[:self._counter],
                "y3": self._y3[:self._counter]}


class DoubleYPlotData:
    def __init__(self, n: int):
        self._x = np.arange(n)
        self._y = np.exp(-16 * (self._x - n/2)**2 / n ** 2)
        self._count = 10 * np.ones(n)

        self._counter = 0

    def next(self):
        n = len(self._x)
        if self._counter == n:
            self._counter = 0
        self._counter += 1

        return {"x": self._x,
                "y": self._y + 0.2 * np.random.random(n),
                "y2": self._count + np.random.randint(20, size=n)}


class MultiPeakData:
    def __init__(self):
        from scipy.datasets import electrocardiogram

        self._x = np.arange(2000, 4000)
        self._y = electrocardiogram()[2000:4000]
        self._peaks, _ = signal.find_peaks(self._y, distance=150)

    def next(self):
        return {
            "x": self._x,
            "y": self._y + np.random.random(1),
            "peaks": self._peaks
        }


class StockPriceData:
    def __init__(self, n: int):
        self._x = np.arange(n)
        self._y_start = np.random.normal(0, 10., n) + 20.
        self._y_end = self._y_start + 20 * (np.random.random(n) - 0.5)
        self._y_min = np.minimum(self._y_start, self._y_end)\
                      - 10 * np.random.random(n)
        self._y_max = np.maximum(self._y_start, self._y_end)\
                      + 10 * np.random.random(n)

        self._counter = 0

    def next(self):
        if self._counter == len(self._x):
            self._counter = 0
        self._counter += 1

        return {"x": self._x[:self._counter],
                "y_start": self._y_start[:self._counter],
                "y_end": self._y_end[:self._counter],
                "y_min": self._y_min[:self._counter],
                "y_max": self._y_max[:self._counter]}


class StemPlotData:
    def __init__(self, n: int):
        self._x = np.linspace(-1, 1, 2 * n, endpoint=False)
        self._y1 = 10 * signal.gausspulse(self._x, fc=3)
        self._y2 = 5 * signal.gausspulse(self._x, fc=5)

        self._x = self._x[int(n/2):int(n/2) + n]
        self._y1 = self._y1[int(n/2):int(n/2) + n]
        self._y2 = self._y2[int(n/2):int(n/2) + n]

        self._counter = 0

    def next(self):
        if self._counter == len(self._x):
            self._counter = 0
        self._counter += 1

        return {"x": self._x[:self._counter],
                "y1": self._y1[:self._counter],
                "y2": self._y2[:self._counter]}


class ImageData:
    def __init__(self):
        self._shape = (768, 1024)

        self._counter = 0
        self._h, self._w = self._shape
        self._max_v = 255

        self._spot = self._generate_spot(200, 120)

    def _generate_spot(self, w, h):
        yc = int(self._h / 2) - int(h / 2) + np.random.randint(10)
        xc = int(self._w / 2) - int(w / 2) + np.random.randint(10)

        x = np.arange(w) - int(w / 2)
        y = np.arange(h) - int(h / 2)
        xx, yy = np.meshgrid(x, y)
        return xc, yc, 0.2 * self._max_v * np.exp(-0.5 * (xx ** 2 / (w / 8) ** 2 + yy ** 2 / (h / 8) ** 2))

    def next(self):
        v0 = self._counter % self._max_v
        self._counter += 1

        data = v0 * np.random.random((self._h, self._w))
        if v0 != 0:
            xc, yc, spot = self._spot
            data[yc:yc + spot.shape[0], xc:xc + spot.shape[1]] += spot

        return {'data': data}


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="foamlight-example-euxfel")
    parser.add_argument("--delay", type=float, default=0.001,
                        help="delay in seconds before publishing the next data")

    args = parser.parse_args()

    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.bind(f"tcp://*:5555")

    line_plot_data = LinePlotData(500)
    scatter_plot_data = ScatterPlotData(300)
    errorbar_plot_data = ErrorBarPlotData(50)
    multi_line_plot_data = MultiLinePlotData(300)
    double_y_plot_data = DoubleYPlotData(100)
    multi_peak_data = MultiPeakData()
    candlestick_plot_data = StockPriceData(100)
    stem_plot_data = StemPlotData(80)
    image_data = ImageData()
    counter = 0
    while True:
        data = {
            "line": line_plot_data.next(),
            "scatter": scatter_plot_data.next(),
            "bar": {
                "x": np.arange(50),
                "y": 100 * np.random.random(50)
            },
            "errorbar": errorbar_plot_data.next(),
            "multi-line": multi_line_plot_data.next(),
            "double-y": double_y_plot_data.next(),
            "multi-peak": multi_peak_data.next(),
            "candlestick": candlestick_plot_data.next(),
            "stem": stem_plot_data.next(),
            "image": image_data.next()
        }

        socket.send(pickle.dumps(data))

        time.sleep(args.delay)
        counter += 1
        print(f"Data #{counter} sent")
