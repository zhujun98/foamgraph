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
