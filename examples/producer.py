import pickle

import numpy as np
import zmq


if __name__ == "__main__":

    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.bind(f"tcp://*:5555")

    counter = 0
    while True:
        data = {
            "scatter": {
                "x": np.arange(200),
                "y": np.arange(200) + 50 * np.random.random(200)
            },
            "line": {
                "x": np.arange(200),
                "y": np.random.random(200)
            },
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
            "multi-line": {
                "x": np.arange(200),
                "y1": np.random.random(200),
                "y2": 2 + np.random.random(200),
                "y3": 4 + np.random.random(200)
            },
            "double-y": {
                "x": np.arange(50),
                "y": np.random.random(50),
                "y2": np.random.random(50)
            }
        }

        socket.send(pickle.dumps(data))
        counter += 1
        print(f"Data #{counter} sent")
