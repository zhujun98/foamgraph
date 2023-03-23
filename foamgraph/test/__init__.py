import time

from foamgraph import mkQApp
from foamgraph.backend.QtCore import QEventLoop, QTimer

app = mkQApp()


def processEvents(timeout=0.05):
    for _ in range(2):
        app.processEvents(
            QEventLoop.ProcessEventsFlag.WaitForMoreEvents)
        time.sleep(0.01)
    time.sleep(timeout)
