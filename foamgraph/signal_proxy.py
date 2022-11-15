"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import weakref

from .backend.QtCore import pyqtSignal, QObject

from foamgraph.pyqtgraph_be.ptime import time
from foamgraph.pyqtgraph_be import ThreadsafeTimer


class SignalProxy(QObject):
    """Object which collects rapid-fire signals and condenses them
    into a single signal or a rate-limited stream of signals. 
    Used, for example, to prevent a SpinBox from generating multiple 
    signals when the mouse wheel is rolled over it.
    
    Emits sigDelayed after input signals have stopped for a certain period of time.
    """

    sigDelayed = pyqtSignal(object)
    
    def __init__(self, signal, delay: float = 0.3, rateLimit=0, slot=None):
        """Initialization.

        :param signal: A bound Signal or pyqtSignal instance.
        :param delay: Time (in seconds) to wait for signals to stop before emitting (default 0.3s).
        :param rateLimit: (signals/sec) if greater than 0, this allows signals to stream out at a
            steady rate while they are being received.
        :param slot: Optional function to connect sigDelayed to.
        """
        super().__init__()

        signal.connect(self.signalReceived)
        self.signal = signal
        self.delay = delay
        self.rateLimit = rateLimit
        self.args = None
        self.timer = ThreadsafeTimer.ThreadsafeTimer()
        self.timer.timeout.connect(self.flush)
        self.block = False
        self.slot = weakref.ref(slot)
        self.lastFlushTime = None
        if slot is not None:
            self.sigDelayed.connect(slot)
        
    def setDelay(self, delay):
        self.delay = delay
        
    def signalReceived(self, *args):
        """Received signal. Cancel previous timer and store args to be forwarded later."""
        if self.block:
            return
        self.args = args
        if self.rateLimit == 0:
            self.timer.stop()
            self.timer.start((self.delay*1000)+1)
        else:
            now = time()
            if self.lastFlushTime is None:
                leakTime = 0
            else:
                lastFlush = self.lastFlushTime
                leakTime = max(0, (lastFlush + (1.0 / self.rateLimit)) - now)
                
            self.timer.stop()
            self.timer.start((min(leakTime, self.delay)*1000)+1)

    def flush(self):
        """If there is a signal queued up, send it now."""
        if self.args is None or self.block:
            return False
        args, self.args = self.args, None
        self.timer.stop()
        self.lastFlushTime = time()
        self.sigDelayed.emit(args)
        return True
