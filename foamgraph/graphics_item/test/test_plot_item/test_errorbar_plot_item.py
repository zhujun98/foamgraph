import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF, QRectF
from foamgraph.graphics_item.plot_item import ErrorbarPlotItem

from foamgraph.test import visualize


def test_errorbar_plot_item(view):
    dtype = np.float32
    x = np.arange(10).astype(dtype)
    y = np.arange(10).astype(dtype)

    # x and y are lists
    item = ErrorbarPlotItem(x.tolist(), y.tolist(), label='errorbar')
    view.addItem(item)
    view.addLegend()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    assert isinstance(item._y_min, np.ndarray)
    assert isinstance(item._y_max, np.ndarray)

    # x and y are numpy.arrays
    y_min = y - 1
    y_max = y + 1
    item.setBeam(1)
    item.setData(x, y, y_min=y_min, y_max=y_max)
    visualize()

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(2), y_min=np.arange(3), y_max=np.arange(2))

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(2), y_min=np.arange(2), y_max=np.arange(3))

    # test log mode
    view._cw._onLogXScaleToggled(True)
    visualize()
    assert item.boundingRect() == QRectF(-0.5, -1.0, 2.0, 11.0)
    view._cw._onLogYScaleToggled(True)
    visualize()
    assert item.boundingRect().topLeft() == QPointF(-0.5, 0.0)
    assert 1.5, item.boundingRect().bottomRight().x()
    assert 1.0 < item.boundingRect().bottomRight().y() < 1.1

    # clear data
    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    visualize()
