import time

from foamgraph import backend

if backend.QT_LIB == "PyQt6":
    from PyQt6 import QtTest
elif backend.QT_LIB == "PyQt5":
    from PyQt5 import QtTest

from foamgraph import mkQApp


app = mkQApp()

# For debug
_VISUALIZE = False


def _display(interval=0.5):
    if _VISUALIZE:
        app.processEvents()
        time.sleep(interval)
        return True
    return False

