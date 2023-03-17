import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF, QRectF
from foamgraph.graphics_item import CandlestickPlotItem

from foamgraph.test import visualize


def test_input_data_parsing(view):
    dtype = np.float32
    x = np.arange(10).astype(dtype)
    y = np.arange(10).astype(dtype)

    # x and y are lists
    item = CandlestickPlotItem(x.tolist(), y.tolist(), label="candlestick")
    view.addItem(item)
    view.addLegend()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y_start, np.ndarray)
    assert isinstance(item._y_end, np.ndarray)
    assert isinstance(item._y_min, np.ndarray)
    assert isinstance(item._y_max, np.ndarray)

    # test different lengths
    right, wrong = np.arange(2), np.arange(3)
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, wrong, right, right, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, wrong, right, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, right, wrong, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, right, right, wrong)
