import pytest

import numpy as np

from foamgraph.backend.QtCore import (
    QByteArray, QDataStream, QIODevice, QPointF, QRectF
)
from foamgraph import mkQApp, GraphView
from foamgraph.graphics_item.plot_item import (
    AnnotationItem, CurvePlotItem, BarPlotItem, ScatterPlotItem, ErrorbarPlotItem
)
from foamgraph.aesthetics import FSymbol

from foamgraph.test import _display

app = mkQApp()


@pytest.fixture(scope="function")
def view():
    graph_view = GraphView()
    if _display():
        graph_view.show()
    return graph_view


class TestCurvePlotItem:
    def test_array2path(self, view):
        size = 5
        x = np.arange(size)
        y = 2 * np.arange(size)
        item = CurvePlotItem(x, y)
        view.addItem(item)
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

    def test_curve_plot_item_(self, view):
        item = CurvePlotItem(check_finite=False)
        view.addItem(item)
        # nan and infinite values prevent generating plots
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, np.nan, 5]
        item.setData(x, y)
        # FIXME
        # assert QRectF() == item.boundingRect()
        view.removeItem(item)

        item2 = CurvePlotItem(check_finite=True)
        view.addItem(item2)
        item2.setData(x, y)
        assert QRectF(1., 0., 4., 5.) == item2.boundingRect()

    @pytest.mark.parametrize("dtype", [float, np.int64, np.uint16])
    def test_item(self, dtype, view):
        x = np.arange(10).astype(dtype)
        y = x * 1.5

        # x and y are lists
        item = CurvePlotItem(x.tolist(), y.tolist(), label='line')
        view.addItem(item)
        view.addLegend()
        assert isinstance(item._x, np.ndarray)
        assert isinstance(item._y, np.ndarray)

        # x and y are numpy.arrays
        # item.setData(x, y)
        if dtype == float:
            _display()

        # test different lengths
        with pytest.raises(ValueError, match="different lengths"):
            item.setData(np.arange(2).astype(dtype), np.arange(3).astype(dtype))

        # test log mode
        view._cw._onLogXScaleToggled(True)
        if dtype == float:
            _display()
        assert item.boundingRect() == QRectF(0, 0, 1.0, 13.5)
        view._cw._onLogYScaleToggled(True)
        if dtype == float:
            _display()
        assert item.boundingRect().topLeft() == QPointF(0, 0)
        assert item.boundingRect().bottomRight().x() == 1.0
        assert 1.2 > item.boundingRect().bottomRight().y() > 1.1

        # clear data
        item.setData([], [])
        assert isinstance(item._x, np.ndarray)
        assert isinstance(item._y, np.ndarray)
        if dtype == float:
            _display()


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
    _display()

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))

    # test log mode
    view._cw._onLogXScaleToggled(True)
    _display()
    assert item.boundingRect() == QRectF(-1.0, 0, 3.0, 14.0)
    view._cw._onLogYScaleToggled(True)
    _display()
    assert item.boundingRect() == QRectF(-1.0, 0, 3.0, 2.0)

    # clear data
    item.setData([], [])
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    _display()


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
    _display()

    # test different lengths
    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(3))

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(2), y_min=np.arange(3), y_max=np.arange(2))

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(np.arange(2), np.arange(2), y_min=np.arange(2), y_max=np.arange(3))

    # test log mode
    view._cw._onLogXScaleToggled(True)
    _display()
    assert item.boundingRect() == QRectF(-0.5, -1.0, 2.0, 11.0)
    view._cw._onLogYScaleToggled(True)
    _display()
    assert item.boundingRect().topLeft() == QPointF(-0.5, 0.0)
    assert 1.5, item.boundingRect().bottomRight().x()
    assert 1.0 < item.boundingRect().bottomRight().y() < 1.1

    # clear data
    item.setData([], [])
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    _display()


class TestScatterPlotItem:
    def test_symbols(self, view):
        FSymbol.buildSymbols()
        for sym in FSymbol._symbol_map:
            x = np.arange(10)
            y = np.arange(10)
            item = ScatterPlotItem(x, y, label=sym, symbol=sym, size=np.random.randint(15, 30))
            view.removeAllItems()
            view.addItem(item)
            view.addLegend()
            _display(interval=0.2)

    def test_item(self, view):
        dtype = float
        x = np.arange(10).astype(dtype)
        y = x * 1.5

        # x and y are lists
        item = ScatterPlotItem(x.tolist(), y.tolist(), label='scatter')
        view.addItem(item)
        view.addLegend()
        assert isinstance(item._x, np.ndarray)
        assert isinstance(item._y, np.ndarray)

        # x and y are numpy.arrays
        item.setData(x, y)

        _display()

        # test different lengths
        with pytest.raises(ValueError, match="different lengths"):
            item.setData(np.arange(2).astype(dtype), np.arange(3).astype(dtype))

        # test log mode
        view._cw._onLogXScaleToggled(True)

        _display()

        view._cw._onLogYScaleToggled(True)

        _display()

        # clear data
        item.setData([], [])
        assert isinstance(item._x, np.ndarray)
        assert isinstance(item._y, np.ndarray)

        _display()


def test_annotation_item(view):
    item = AnnotationItem()
    view.addItem(item)
