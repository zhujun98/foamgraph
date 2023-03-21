import pytest

import numpy as np

from foamgraph.backend.QtCore import (
    QByteArray, QDataStream, QIODevice, QPointF, QRectF
)
from foamgraph.graphics_item import CurvePlotItem

from foamgraph.test import processEvents


@pytest.fixture
def item(view):
    item = CurvePlotItem(label="curve")
    view.addItem(item)
    view.addLegend()
    return item


def test_array2path(item):
    size = 5
    x = np.arange(size)
    y = 2 * np.arange(size)
    item.setData(x, y)
    p = item._graph

    # stream path
    arr = QByteArray()
    buf = QDataStream(arr, QIODevice.OpenModeFlag.ReadWrite)
    buf << p
    buf.device().reset()

    # test protocol
    assert arr.size() == 4 + size * 20 + 8
    assert buf.readInt32() == size
    for i in range(5):
        if i == 0:
            assert buf.readInt32() == 0
        else:
            assert buf.readInt32() == 1
        assert buf.readDouble() == x[i]
        assert buf.readDouble() == y[i]
    assert buf.readInt32() == 0
    assert buf.readInt32() == 0


def test_input_data_parsing(view):
    x = y = np.arange(10).astype(float)

    # x and y are lists
    item = CurvePlotItem(x.tolist(), y.tolist(), label="curve")
    view.addItem(item)
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))


@pytest.mark.parametrize("dtype", [float, np.int64, np.uint16])
def test_item(dtype, view, item):
    x = np.arange(10).astype(dtype)
    y = x * 1.5
    item.setData(x, y)
    if dtype == float:
        processEvents()

    # test log mode
    view._cw._onLogXScaleToggled(True)
    if dtype == float:
        processEvents()
    assert item.boundingRect() == QRectF(0, 0, 1.0, 13.5)

    view._cw._onLogYScaleToggled(True)
    if dtype == float:
        processEvents()

    assert item.boundingRect().topLeft() == QPointF(0, 0)
    assert item.boundingRect().bottomRight().x() == 1.0
    assert 1.2 > item.boundingRect().bottomRight().y() > 1.1

    item.clearData()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    if dtype == float:
        processEvents()


@pytest.mark.parametrize("check_finite", [True, False])
def test_bounding_rect_1(view, check_finite):
    item = CurvePlotItem(check_finite=check_finite)
    view.addItem(item)
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    item.setData(x, y)
    assert item.boundingRect() == QRectF(1., 2, 4., 8.)


@pytest.mark.parametrize("check_finite", [True, False])
def test_bounding_rect_2(view, check_finite):
    item = CurvePlotItem(check_finite=check_finite)
    view.addItem(item)
    x = [1, 2, 3, np.nan, 5]  # nan in x will be ignored
    y = [2, 4, 6, 8, 10]
    item.setData(x, y)
    assert item.boundingRect() == QRectF(1., 2, 4., 8.)


@pytest.mark.parametrize("check_finite", [True, False])
def test_bounding_rect_3(view, check_finite):
    item = CurvePlotItem(check_finite=check_finite)
    view.addItem(item)
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, np.nan, 10]
    item.setData(x, y)
    if check_finite:
        # np.nan in y will be converted to 0
        assert item.boundingRect() == QRectF(1., 0, 4., 10.)
    else:
        # np.nan in y will be ignored
        assert item.boundingRect() == QRectF(1., 2, 4., 8.)
