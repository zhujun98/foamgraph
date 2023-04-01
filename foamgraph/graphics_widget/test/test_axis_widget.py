import pytest
from unittest.mock import patch

from foamgraph import mkQApp
from foamgraph import GraphView
from foamgraph.test import processEvents

app = mkQApp()


@pytest.fixture(scope="function")
def view():
    view = GraphView()
    view.show()
    processEvents()
    return view


@pytest.fixture(scope="function")
def axis_left(view):
    return view._cw._axes['left']


@pytest.fixture(scope="function")
def axis_bottom(view):
    return view._cw._axes['bottom']


def test_mouse_double_click(view, axis_left, axis_bottom):
    with patch.object(view._cw._canvas, "setTargetYRange") as patched:
        axis_left._onMouseDClickEvent()
        patched.assert_called_once()

    with patch.object(view._cw._canvas, "setTargetXRange") as patched:
        axis_bottom._onMouseDClickEvent()
        patched.assert_called_once()
