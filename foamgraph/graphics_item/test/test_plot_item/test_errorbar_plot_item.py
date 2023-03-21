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


def test_log_mode(view, item):
    x = y = np.arange(10)
    item.setData(x, y, y_min=y-1, y_max=y+1)
    item.setBeam(1)
    processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-0.5, -1.0, 2.0, 11.0)
    view._cw._onLogYScaleToggled(True)
    processEvents()
    assert item.boundingRect().topLeft() == QPointF(-0.5, 0.0)
    assert 1.5, item.boundingRect().bottomRight().x()
    assert 1.0 < item.boundingRect().bottomRight().y() < 1.1

    # clear data
    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    processEvents()
