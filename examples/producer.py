import pickle

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


if __name__ == "__main__":

    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.bind(f"tcp://*:5555")

    scatter_plot_data = ScatterPlotData(500)
    multi_line_plot_data = MultiLinePlotData(1000)
    double_y_plot_data = DoubleYPlotData(100)
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
            "errorbar": {
                "x": np.arange(30),
                "y": 100 * np.random.random(30),
                "y_min": 100 * np.random.random(30),
                "y_max": 100 * np.random.random(30)
            },
            "multi-line": multi_line_plot_data.next(),
            "double-y": double_y_plot_data.next(),
            "image": {
                "data": np.random.random((768, 1024))
            }
        }

        socket.send(pickle.dumps(data))
        counter += 1
        print(f"Data #{counter} sent")
