import pytest

import numpy as np

from foamgraph.aesthetics import FSymbol
from foamgraph.graphics_item import ScatterPlotItem

from foamgraph.test import visualize


def test_symbols(view):
    FSymbol.buildSymbols()
    view.addLegend()
    for sym in FSymbol._symbol_map:
        x = np.arange(10)
        y = np.arange(10)
        item = ScatterPlotItem(x, y, label=sym, symbol=sym, size=np.random.randint(15, 30))
        view.addItem(item)
        visualize(interval=0.2)
        view.removeItem(item)


@pytest.fixture
def item(view):
    item = ScatterPlotItem(label="scatter")
    view.addItem(item)
    view.addLegend()
    return item


def test_input_data_parsing(view):
    x = y = np.arange(10).astype(float)

    # x and y are lists
    item = ScatterPlotItem(x.tolist(), y.tolist(), label="scatter")
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
    visualize()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    visualize()

    view._cw._onLogYScaleToggled(True)
    visualize()

    # clear data
    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    visualize()


def test_bounding_rect_1(item):
    x = np.array([0, 1, 2, 3, 4])
    y = np.array([2, 4, 6, 8, 10])
    item.setData(x, y)
    rect = item.boundingRect()
    assert abs(rect.x()) < 0.016
    assert abs(rect.y() - 2) < 0.021
    assert abs(rect.width() - 4) < 0.031
    assert abs(rect.height() - 8) < 0.041


def test_bounding_rect_2(item):
    x = np.array([0, 1, 2, 3, 4])
    y = np.array([2, 4, 6, np.nan, 10])
    item.setData(x, y)
    rect = item.boundingRect()
    assert abs(rect.x()) < 0.016
    assert abs(rect.y() - 2) < 0.021
    assert abs(rect.width() - 4) < 0.031
    assert abs(rect.height() - 8) < 0.041


def test_bounding_rect_3(item):
    x = np.array([np.nan, 1, 2, np.nan, 4])
    y = np.array([2, 4, 6, np.nan, 10])
    item.setData(x, y)
    rect = item.boundingRect()
    assert abs(rect.x() - 1) < 0.016
    assert abs(rect.y() - 2) < 0.021
    assert abs(rect.width() - 3) < 0.031
    assert abs(rect.height() - 8) < 0.041


def test_bounding_rect_4(item):
    x = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
    y = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
    item.setData(x, y)
    rect = item.boundingRect()
    assert abs(rect.x()) < 0.016
    assert abs(rect.y()) < 0.021
    assert abs(rect.width()) < 0.031
    assert abs(rect.height()) < 0.041
