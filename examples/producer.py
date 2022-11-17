import argparse
import pickle
import time

import numpy as np
import zmq


class ScatterPlotData:
    def __init__(self, n: int):
        self._x = np.arange(n)
        self._y = self._x + np.abs(self._x - n / 2) * (np.random.random(n) - 0.5)

        np.random.shuffle(self._x)
        self._y = self._y[self._x]

        self._counter = 0

    def next(self):
        if self._counter == len(self._x):
            self._counter = 0
        self._counter += 1

        return {"x": self._x[:self._counter],
                "y": self._y[:self._counter]}


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


class ImageData:
    def __init__(self):
        self._h, self._w = 1024, 1024

    def next(self):
        spot_w = 200
        spot_h = 120

        yc = int(self._h / 2) - int(spot_h / 2) + np.random.randint(10)
        xc = int(self._w / 2) - int(spot_w / 2) + np.random.randint(10)

        x = np.arange(spot_w) - int(spot_w / 2)
        y = np.arange(spot_h) - int(spot_h / 2)
        xx, yy = np.meshgrid(x, y)
        spot_i = 2 * np.exp(-0.5 * (xx ** 2 / (spot_w / 8) ** 2 + yy ** 2 / (spot_h / 8) ** 2))

        data = np.random.random((self._h, self._w))
        data[yc:yc + spot_h, xc:xc + spot_w] += spot_i
        return {'data': data}


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="foamlight-example-euxfel")
    parser.add_argument("--delay", type=float, default=0.001)

    args = parser.parse_args()

    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.bind(f"tcp://*:5555")

    scatter_plot_data = ScatterPlotData(500)
    errorbar_plot_data = ErrorBarPlotData(50)
    multi_line_plot_data = MultiLinePlotData(1000)
    double_y_plot_data = DoubleYPlotData(100)
    image_data = ImageData()
    counter = 0
    while True:
        data = {
            "line": {
                "x": np.arange(200),
                "y": np.random.random(200)
            },
            "scatter": scatter_plot_data.next(),
            "bar": {
                "x": np.arange(50),
                "y": 100 * np.random.random(50)
            },
            "errorbar": errorbar_plot_data.next(),
            "multi-line": multi_line_plot_data.next(),
            "double-y": double_y_plot_data.next(),
            "image": image_data.next()
        }

        socket.send(pickle.dumps(data))

        time.sleep(args.delay)
        counter += 1
        print(f"Data #{counter} sent")
