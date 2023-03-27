import pytest

import numpy as np

from foamgraph.backend.QtCore import QRectF
from foamgraph.graphics_item import StemPlotItem

from foamgraph.test import processEvents


@pytest.fixture
def item(view):
    item = StemPlotItem(label="stem")
    view.addItem(item)
    view.addLegend()
    return item


def test_input_data_parsing(view):
    x = y = np.arange(10).astype(float)

    # x and y are lists
    item = StemPlotItem(x.tolist(), y.tolist(), label="scatter")
    view.addItem(item)
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))


def test_log_mode(view, item):
    x = np.arange(10).astype(float)
    y = x * 1.5
    item.setData(x, y)
    processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    processEvents()

    view._cw._onLogYScaleToggled(True)
    processEvents()

    # clear data
    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    processEvents()


def test_bounding_rect_1(item):
    x = np.array([0, 1, 2, 3, 4])
    y = np.array([-4, -2, 0, 2, 4])
    item.setData(x, y)
    rect = item.boundingRect()
    assert rect == QRectF(0.0, -4.0, 4.0, 8.0)


def test_bounding_rect_2(item):
    x = np.array([0, 1, 2, 3, 4])
    y = np.array([2, 4, 6, 8, 10])
    item.setData(x, y)
    rect = item.boundingRect()
    assert rect == QRectF(0.0, 0.0, 4.0, 10.0)
