import pytest
from unittest.mock import patch

from foamgraph.graphics_item import MouseCursorItem
from foamgraph.graphics_widget import ImageWidget
from foamgraph.test import processEvents


@pytest.fixture(scope="function")
def iwidget():
    widget = ImageWidget()
    processEvents()
    return widget


def test_axes(iwidget):
    for name in ['left', 'bottom']:
        axis = iwidget._axes[name]
        assert not axis.isVisible()

    assert 'right' not in iwidget._axes


def test_clear_data(iwidget):
    with patch.object(iwidget._image_item, "setData") as patched:
        iwidget.clearData()
        patched.assert_called_once_with(None)


def test_mouse_cursor_context_menu(iwidget):
    canvas = iwidget._canvas
    assert canvas.getMenuAction("Cursor_Style_Simple").isChecked()
    assert isinstance(iwidget._mouse_cursor, MouseCursorItem)


def test_roi(iwidget):
    roi1 = iwidget.addRectROI(0, 0, 10, 10, name="ROI")
    # name in context menu will be automatically generated
    roi2 = iwidget.addEllipseROI(1, 1, 10, 10)

    action1 = iwidget._canvas.getMenuAction("ROI_ROI")
    assert not action1.isChecked()
    assert not roi1.isVisible()
    action1.setChecked(True)
    assert roi1.isVisible()

    action2 = iwidget._canvas.getMenuAction("ROI_ROI2")
    assert not action2.isChecked()
    assert not roi2.isVisible()
    action2.setChecked(True)
    assert roi2.isVisible()
