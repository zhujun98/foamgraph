from collections import deque
import pickle
from threading import Thread

import zmq


class Consumer:
    def __init__(self, queue: deque):
        self._ctx = zmq.Context()
        self._socket = self._ctx.socket(zmq.SUB)
        self._socket.connect("tcp://localhost:5555")
        self._socket.setsockopt(zmq.SUBSCRIBE, b"")

        self._queue = queue

        self._thread = Thread(target=self._consume, daemon=True)

    def _consume(self):
        while True:
            data = pickle.loads(self._socket.recv())
            self._queue.append(data)

    def start(self):
        self._thread.start()
