import pytest

import numpy as np

from foamgraph.backend.QtCore import QRectF
from foamgraph.graphics_item import BarPlotItem

from foamgraph.test import processEvents


def test_input_data_parsing(view):
    x = np.arange(10).astype(np.float32)
    y = x * 1.5

    # x and y are lists
    item = BarPlotItem(x.tolist(), y.tolist(), label='bar')
    view.addItem(item)
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))


@pytest.fixture
def item(view):
    item = view.addBarPlot(label="bar")
    view.addLegend()
    return item


def test_log_mode(view, item):
    x = np.arange(10).astype(np.float32)
    y = x * 1.5
    item.setData(x, y)
    item.update()
    processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-1.0, 0, 3.0, 14.0)
    view._cw._onLogYScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-1.0, 0, 3.0, 2.0)

    # clear data
    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    processEvents()
