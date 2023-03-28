import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF, QRectF
from foamgraph.graphics_item import ShadePlotItem

from foamgraph.test import processEvents


@pytest.fixture
def item(view):
    item = ShadePlotItem(label="shade")
    view.addItem(item)
    view.addLegend()
    return item


def test_input_data_parsing(view):
    x = y1 = y2 = np.arange(10).astype(float)

    # x and y are lists
    item = ShadePlotItem(x.tolist(), y1.tolist(), y2.tolist(), label="shade")
    view.addItem(item)
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y1, np.ndarray)
    assert isinstance(item._y2, np.ndarray)

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3), np.arange(3))

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(2), np.arange(3))


def test_plot(item):
    item.setData([1], [2], [3])
    processEvents()

    item.clearData()
    assert item.boundingRect() == QRectF()
    processEvents()


def test_log_mode(view, item):
    x = np.arange(10).astype(np.float32)
    y1 = x * 1.5
    y2 = x * 0.5
    item.setData(x, y1, y2)
    item.update()
    processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(0.0, 0.0, 1.0, 13.5)
    view._cw._onLogYScaleToggled(True)
    processEvents()
    # assert item.boundingRect() == QRectF(0.0, 0.0, 1.0, 2.0)


def test_bounding_rect_1(item):
    x = [1, 2, 3, 4, 5]
    y1 = [1, 4, 2, 6, 10]
    y2 = [2, 6, 3, 4, 8]
    item.setData(x, y1, y2)
    assert item.boundingRect() == QRectF(1., 1., 4., 9.)


def test_bounding_rect_2(item):
    x = [1, 2, 3, np.nan, 5]  # nan in x will be ignored
    y1 = [1, 4, 2, 6, 10]
    y2 = [2, 6, 3, 4, 8]
    item.setData(x, y1, y2)
    assert item.boundingRect() == QRectF(1., 1., 4., 9.)
