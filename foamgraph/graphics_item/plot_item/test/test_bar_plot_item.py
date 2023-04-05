import pytest

import numpy as np

from foamgraph.backend.QtCore import QRectF
from foamgraph.graphics_item import BarPlotItem
from foamgraph import FColor

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


def test_plot(item):
    item.setData([1], [2])
    processEvents()

    item.clearData()
    assert item.boundingRect() == QRectF()
    processEvents()


def test_log_mode(view, item):
    x = np.arange(10).astype(np.float64)
    y = x * 1.5
    item.setData(x, y)
    processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-2.0, 0, 4.0, 14.0)
    view._cw._onLogYScaleToggled(True)
    processEvents()
    assert item.boundingRect() == QRectF(-2.0, -1.0, 4.0, 3.0)


@pytest.mark.parametrize("orientation", ['v', 'h'])
def test_stacking(view, orientation):
    view.setBarPlotStackOrientation(orientation)

    items = []
    for i, c in zip(range(3), ['r', 'g', 'b']):
        items.append(view.addBarPlot(label=f"Bar{i}", brush=FColor.mkBrush(c)))
    view.addLegend()

    x = np.arange(10).astype(np.float64)
    for item in items:
        item.setData(x, np.random.random(10))
    processEvents()

    view.removeItem(items[1])
    processEvents()

    view.removeItem(items[0])
    processEvents()


def test_switch_stacking(view):
    x = np.arange(10).astype(np.float64)
    items = []
    for i, c in zip(range(3), ['r', 'g', 'b']):
        items.append(view.addBarPlot(label=f"Bar{i}", brush=FColor.mkBrush(c)))
        items[-1].setData(x, np.random.random(10))
    view.addLegend()
    processEvents()

    view.setBarPlotStackOrientation('h')
    processEvents()


def test_bounding_rect(view):
    item1 = view.addBarPlot()

    x = np.array([0, 1, 2, 3, 4])
    y = np.array([-4, -2, 0, 2, 4])

    item1.setData(x, y)
    rect = item1.boundingRect()
    assert rect == QRectF(-1.0, -4.0, 6.0, 8.0)
