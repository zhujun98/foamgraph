import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF, QRectF
from foamgraph.graphics_item import ErrorbarPlotItem

from foamgraph.test import processEvents


def test_input_data_parsing(view):
    x = y = np.arange(10)

    # x and y are lists
    item = ErrorbarPlotItem(x.tolist(), y.tolist(), label="errorbar")
    view.addItem(item)
    view.addLegend()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    assert isinstance(item._y_min, np.ndarray)
    assert isinstance(item._y_max, np.ndarray)

    # test different lengths
    right, wrong = np.arange(2), np.arange(3)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, wrong)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, y_min=wrong, y_max=right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, y_min=right, y_max=wrong)


@pytest.fixture
def item(view):
    item = view.addErrorbarPlot(label="errorbar")
    view.addLegend()
    return item


def test_plot(item):
    item.setData([1], [2], [3], [4])
    processEvents()

    item.clearData()
    assert item.boundingRect() == QRectF()
    processEvents()


def test_log_mode(view, item):
    x = y = np.arange(11).astype(np.float64)
    item.setData(x, y, y_min=y/10, y_max=y*10)
    item.setBeam(1)
    processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-1.5, 0., 3., 100.)
    view._cw._onLogYScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-1.5, -2., 3., 4.)
