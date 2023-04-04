import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF, QRectF
from foamgraph.graphics_item import CurvePlotItem, SimpleCurvePlotItem

from foamgraph.test import processEvents


class TestSimpleCurvePlotItem:
    @pytest.fixture(params=[SimpleCurvePlotItem, CurvePlotItem])
    def item(self, view, request):
        item = request.param(label="curve")
        view.addItem(item)
        view.addLegend()
        return item

    @pytest.fixture(params=[SimpleCurvePlotItem, CurvePlotItem])
    def item_type(self, request):
        return request.param

    def test_input_data_parsing(self, view, item_type):
        x = y = np.arange(10).astype(float)

        # x and y are lists
        item = item_type(x.tolist(), y.tolist(), label="curve")
        view.addItem(item)
        assert isinstance(item._x, np.ndarray)
        assert isinstance(item._y, np.ndarray)

        # test different lengths
        with pytest.raises(ValueError, match="different lengths"):
            item.setData(np.arange(2), np.arange(3))

    @pytest.mark.parametrize("dtype", [float, np.int64, np.uint16])
    def test_plot(self, item, dtype):
        item.setData([1], [2])
        processEvents()

        item.clearData()
        assert item.boundingRect() == QRectF()
        processEvents()

    def test_log_mode(self, view, item):
        x = np.arange(11).astype(np.float64)
        y = x * 10.
        item.setData(x, y)
        processEvents()

        # test log mode
        view._cw._onLogXScaleToggled(True)
        processEvents()
        assert item.boundingRect() == QRectF(-1., 0., 2., 100.)

        view._cw._onLogYScaleToggled(True)
        processEvents()
        assert item.boundingRect() == QRectF(-1., -1., 2., 3.)

    def test_bounding_rect_1(self, view, item_type):
        item = item_type()
        view.addItem(item)
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        item.setData(x, y)
        assert item.boundingRect() == QRectF(1., 2, 4., 8.)
        processEvents()

    @pytest.mark.parametrize("check_finite", [True, False])
    def test_bounding_rect_2(self, view, item_type, check_finite):
        item = item_type(check_finite=check_finite)
        view.addItem(item)
        x = [1, 2, 3, np.nan, 5]  # nan in x will be ignored
        y = [2, 4, 6, 8, 10]
        item.setData(x, y)
        assert item.boundingRect() == QRectF(1., 2, 4., 8.)

    @pytest.mark.parametrize("check_finite", [True, False])
    def test_bounding_rect_3(self, view, item_type, check_finite):
        item = item_type(check_finite=check_finite)
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


class TestCurvePlotItem:
    @pytest.fixture
    def item(self, view):
        item = view.addCurvePlot(label="curve")
        view.addLegend()
        return item

    def test_input_data_parsing(self, view):
        x = y = np.arange(10).astype(float)
        y_err = 0.1 * y

        # x and y are lists
        item = CurvePlotItem(x.tolist(), y.tolist(), y_err.tolist(), label="curve")
        view.addItem(item)
        assert isinstance(item._y_err, np.ndarray)
        assert item._y_err.size == 10

        with pytest.raises(ValueError, match="different lengths"):
            item.setData(np.arange(3), np.arange(3), np.arange(2))

    def test_bounding_rect_1(self, item):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        y_err = [1, 1, 1, 1, 1]
        item.setData(x, y, y_err)
        assert item.boundingRect() == QRectF(1., 1., 4., 10.)

    @pytest.mark.parametrize("check_finite", [True, False])
    def test_bounding_rect_2(self, view, check_finite):
        item = CurvePlotItem(check_finite=check_finite)
        view.addItem(item)
        x = [1, 2, 3, np.nan, 5]  # nan in x will be ignored
        y = [2, 4, 6, 8, 10]
        y_err = [1, 1, 1, 1, 1]
        item.setData(x, y, y_err)
        assert item.boundingRect() == QRectF(1., 1., 4., 10.)
