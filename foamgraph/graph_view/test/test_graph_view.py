import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from foamgraph import GraphView, TimedGraphView
from foamgraph.graphics_item import (
    AnnotationItem, CandlestickPlotItem, ErrorbarPlotItem
)
from foamgraph.test import processEvents


@pytest.fixture
def graph_view_1():
    # test addLegend before adding plot items
    view = GraphView()
    view.setXLabel("x label")
    view.setYLabel("y label")
    view.setTitle("GraphView test")

    view.addAnnotation()
    view.show()
    processEvents()
    return view


@pytest.fixture
def add_plot_items_1(graph_view_1):
    view = graph_view_1
    view.addLegend()  # add legend before plot items
    return [
        view.addCurvePlot(label="curve1"),
        view.addScatterPlot(label="scatter1"),
        view.addCandlestickPlot(label="candlestick"),
        view.addBarPlot(label="bar2", y2=True),
        view.addErrorbarPlot(label="errorbar2", y2=True),
        view.addAnnotation()
    ]


@pytest.fixture
def graph_view_2():
    view = GraphView()
    view.setXYLabels("x label", "y label", y2="y2 label")
    view.show()
    return view


@pytest.fixture
def add_plot_items_2(graph_view_2):
    view = graph_view_2  # add legend after plot items
    items = [
        view.addBarPlot(label="bar1"),
        view.addCandlestickPlot(label="candlestick"),
        view.addErrorbarPlot(label="errorbar1"),
        view.addCurvePlot(label="curve2", y2=True),
        view.addScatterPlot(label="scatter2", y2=True),
        view.addAnnotation()
    ]
    view.addLegend()
    return items


class TestGraphView:

    def test_forwarded_methods(self, graph_view_1):
        view = graph_view_1
        cw = view._cw

        with patch.object(cw, "clearData") as mocked:
            view.clearData()
            mocked.assert_called_once()

        with patch.object(cw, "addItem") as mocked:
            item = object()
            view.addItem(item)
            mocked.assert_called_once_with(item)

        with patch.object(cw, "removeItem") as mocked:
            item = object()
            view.removeItem(item)
            mocked.assert_called_once_with(item)

    def test_axes(self, graph_view_1):
        view = graph_view_1

        assert view._cw._axes['left'].isVisible()
        assert view._cw._axes['bottom'].isVisible()
        view.showXAxis(False)
        assert not view._cw._axes['bottom'].isVisible()
        view.showYAxis(False)
        assert not view._cw._axes['left'].isVisible()
        view.showXAxis()
        assert view._cw._axes['bottom'].isVisible()
        view.showYAxis()
        assert view._cw._axes['left'].isVisible()

    def test_legend(self, graph_view_1):
        view = graph_view_1

        view.addLegend()
        assert view._cw._legend.isVisible()
        view.showLegend(False)
        assert not view._cw._legend.isVisible()
        view.showLegend()
        assert view._cw._legend.isVisible()

    def test_set_data(self, graph_view_1, add_plot_items_1):
        view = graph_view_1
        assert len(view._cw._canvas._proxy._items) == 5

        plot_items = add_plot_items_1
        for i, plot in enumerate(plot_items):
            x = np.arange(20)
            y = np.random.rand(20)
            # TODO: CI will report segfault with the following line
            #       because of ScatterPlotItem.
            # y[-i-1:-1] = np.nan
            if isinstance(plot, ErrorbarPlotItem):
                plot.setData(x, y, y - 0.1, y + 0.1)
            elif isinstance(plot, AnnotationItem):
                plot.setData(x, y, x)
            elif isinstance(plot, CandlestickPlotItem):
                plot.setData(x, y - 0.1, y + 0.1, y - 0.2, y + 0.2)
            else:
                plot.setData(x, y)
            processEvents()

        view._cw._onLogXScaleToggled(True)
        processEvents()
        view._cw._onLogYScaleToggled(True)
        processEvents()

        for plot in plot_items:
            plot.clearData()
            processEvents()

    def test_set_data_with_nan(self, graph_view_2, add_plot_items_2):
        assert len(graph_view_2._cw._canvas._proxy._items) == 4

        view = graph_view_2
        plot_items = add_plot_items_2
        for i, plot in enumerate(plot_items):
            x = np.arange(20)
            y = np.random.rand(20)
            y[-i-1:-1] = np.nan
            if isinstance(plot, ErrorbarPlotItem):
                plot.setData(x, y, y - 0.1, y + 0.1)
            elif isinstance(plot, AnnotationItem):
                plot.setData(x, y, x)
            elif isinstance(plot, CandlestickPlotItem):
                plot.setData(x, y - 0.1, y + 0.1, y - 0.2, y + 0.2)
            else:
                plot.setData(x, y)
            processEvents()

        view._cw._onLogXScaleToggled(True)
        processEvents()
        view._cw._onLogYScaleToggled(True)
        processEvents()

        for plot in plot_items:
            plot.clearData()
            processEvents()


class TestTimedPlotWidgetF:
    def test_update(self):
        view = TimedGraphView()
        view.refresh = MagicMock()

        assert view._data is None
        view._refresh_imp()
        view.refresh.assert_not_called()

        view.updateF(1)
        view._refresh_imp()
        view.refresh.assert_called_once()
