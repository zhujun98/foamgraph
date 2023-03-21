import pytest

import numpy as np

from foamgraph.graphics_item import CandlestickPlotItem

from foamgraph.test import processEvents


def test_input_data_parsing(view):
    x = y_start = y_end = y_min = y_max = np.arange(10)

    # x and y are lists
    item = CandlestickPlotItem(
        x.tolist(), y_start.tolist(), y_end.tolist(),
        y_min=y_min.tolist(), y_max=y_max.tolist(), label="candlestick")
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
        CandlestickPlotItem(right, right)

    with pytest.raises(ValueError, match="different lengths"):
        CandlestickPlotItem(right, right, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, wrong, right, right, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, wrong, right, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, right, wrong, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, right, right, wrong)


@pytest.fixture
def item(view):
    item = view.addCandlestickPlot(label="candelstick")
    view.addLegend()
    return item


def test_plot(item):
    x = np.arange(10).astype(float)
    y_start = np.arange(10).astype(float)
    y_stop = y_start + np.random.random() - 0.5
    y_min = y_start - 1.
    y_max = y_start + 1.

    item.setData(x, y_start, y_stop, y_min, y_max)
    processEvents()

    item.clearData()
    processEvents()
