import pytest
from unittest.mock import patch

from . import processEvents
from foamgraph import GraphView, LiveWindow


@pytest.fixture
def window():

    class Plot1(GraphView):
        def updateF(self, data):
            ...

    class Plot2(GraphView):
        def updateF(self, data):
            ...

    class TestWindow(LiveWindow):
        def __init__(self):
            super().__init__("Test window")

            self._plot1 = Plot1(parent=self)
            self._plot2 = Plot2(parent=self)

            self._queue.append([])

        def initUI(self):
            ...

        def initConnections(self):
            ...

    win = TestWindow()
    yield win
    win.close()


def test_update(window):
    plot1 = window._plot1
    plot2 = window._plot2

    with patch.object(plot1, "updateF") as patched_update1:
        with patch.object(plot2, "updateF") as patched_update2:
            window.updateGraphicsViews()
            patched_update1.assert_called_once()
            patched_update2.assert_called_once()
