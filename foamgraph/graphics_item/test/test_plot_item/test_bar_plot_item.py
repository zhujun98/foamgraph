import pytest

import numpy as np

from foamgraph.backend.QtCore import QRectF
from foamgraph.graphics_item.plot_item import BarPlotItem

from foamgraph.test import visualize


def test_bar_plot_item(view):
    x = np.arange(10).astype(np.float32)
    y = x * 1.5

    # x and y are lists
    item = BarPlotItem(x.tolist(), y.tolist(), label='bar')
    view.addItem(item)
    view.addLegend()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)

    # x and y are numpy.arrays
    item.setData(x, y)
    visualize()

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))

    # test log mode
    view._cw._onLogXScaleToggled(True)
    visualize()
    assert item.boundingRect() == QRectF(-1.0, 0, 3.0, 14.0)
    view._cw._onLogYScaleToggled(True)
    visualize()
    assert item.boundingRect() == QRectF(-1.0, 0, 3.0, 2.0)

    # clear data
    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    visualize()
