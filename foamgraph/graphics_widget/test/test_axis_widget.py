import pytest
from unittest.mock import patch

from foamgraph.backend.QtTest import QSignalSpy
from foamgraph import GraphView, mkQApp
from foamgraph.graphics_item.plot_item import PlotItem
from foamgraph.test import processEvents

app = mkQApp()


@pytest.fixture(scope="function")
def view():
    view = GraphView()
    view.addCurvePlot()
    view.addCurvePlot(y2=True)
    view.show()
    processEvents()
    yield view
    view.close()


@pytest.fixture()
def axis_left(view):
    return view._cw._axes['left']


@pytest.fixture()
def axis_bottom(view):
    return view._cw._axes['bottom']


@pytest.fixture()
def axis_right(view):
    return view._cw._axes['right']


def test_context_menu(view, axis_left, axis_bottom, axis_right):
    canvas = view._cw._canvas

    action = axis_bottom.getMenuAction("LogScale")
    assert not action.isChecked()
    with patch.object(canvas, "updateAutoRange") as patched_update:
        with patch.object(PlotItem, "setLogX") as patched_setlog:
            spy = QSignalSpy(axis_bottom.log_Scale_toggled_sgn)
            action.setChecked(True)
            assert len(spy) == 1
            patched_update.assert_called_once()
            assert patched_setlog.call_count == 2  # both y and y2

    action = axis_left.getMenuAction("LogScale")
    with patch.object(canvas, "updateAutoRange") as patched_update:
        with patch.object(PlotItem, "setLogY") as patched_setlog:
            spy = QSignalSpy(axis_left.log_Scale_toggled_sgn)
            action.setChecked(True)
            assert len(spy) == 1
            patched_update.assert_called_once()
            patched_setlog.assert_called_once()

    canvas_y2 = view._cw._canvas_y2

    action = axis_right.getMenuAction("LogScale")
    with patch.object(canvas_y2, "updateAutoRange") as patched_update:
        with patch.object(PlotItem, "setLogY") as patched_setlog:
            spy = QSignalSpy(axis_right.log_Scale_toggled_sgn)
            action.setChecked(True)
            assert len(spy) == 1
            patched_update.assert_called_once()
            patched_setlog.assert_called_once()


def test_invert(view, axis_left, axis_bottom, axis_right):
    canvas = view._cw._canvas
    canvas_y2 = view._cw._canvas_y2

    assert not canvas._x_inverted
    axis_bottom.getMenuAction("InvertAxis").trigger()
    assert canvas._x_inverted
    # FIXME:
    # assert canvas_y2._x_inverted

    assert not canvas._y_inverted
    axis_left.getMenuAction("InvertAxis").trigger()
    assert canvas._y_inverted

    assert not canvas_y2._y_inverted
    axis_right.getMenuAction("InvertAxis").trigger()
    assert canvas_y2._y_inverted


def test_mouse_double_click(view, axis_left, axis_bottom, axis_right):
    canvas = view._cw._canvas
    canvas_y2 = view._cw._canvas_y2

    with patch.object(canvas, "setTargetYRange") as patched:
        axis_left._onMouseDClickEvent()
        patched.assert_called_once()

    with patch.object(canvas, "setTargetXRange") as patched:
        axis_bottom._onMouseDClickEvent()
        patched.assert_called_once()

    with patch.object(canvas_y2, "setTargetYRange") as patched:
        axis_right._onMouseDClickEvent()
        patched.assert_called_once()
