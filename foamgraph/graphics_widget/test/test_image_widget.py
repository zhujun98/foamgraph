import pytest
from unittest.mock import patch

from foamgraph import mkQApp
from foamgraph.graphics_widget import ImageWidget

app = mkQApp()


@pytest.fixture(scope="function")
def iwidget():
    widget = ImageWidget()
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
