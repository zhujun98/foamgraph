import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from foamgraph import mkQApp, HistWidgetF, GraphView, TimedGraphView
from foamgraph.graphics_item.plot_item import ErrorbarPlotItem

from . import _display


app = mkQApp()


@pytest.fixture
def graph_view1():
    # test addLegend before adding plot items
    view = GraphView()
    view.setXLabel("x label")
    view.setYLabel("y label")

    view.addAnnotation()

    if _display():
        view.show()
    return view


@pytest.fixture
def add_plot_items1(graph_view1):
    view = graph_view1
    view.addLegend()  # add legend before plot items
    return [view.addCurvePlot(label="curve1"),
            view.addScatterPlot(label="scatter1"),
            view.addBarPlot(label="bar2", y2=True),
            view.addErrorbarPlot(label="errorbar2", y2=True)]


@pytest.fixture
def graph_view2():
    view = GraphView()
    view.setXYLabels("x label", "y label", y2="y2 label")
    if _display():
        view.show()
    return view


@pytest.fixture
def add_plot_items2(graph_view2):
    view = graph_view2  # add legend after plot items
    items = [view.addBarPlot(label="bar1"),
             view.addErrorbarPlot(label="errorbar1"),
             view.addCurvePlot(label="curve2", y2=True),
             view.addScatterPlot(label="scatter2", y2=True)]
    view.addLegend()
    return items


class TestGraphView:

    def test_plots(self, graph_view1, graph_view2, add_plot_items1, add_plot_items2):
        assert len(graph_view1._cw._items) == 5
        assert len(graph_view2._cw._items) == 4

    def test_forwarded_methods(self, graph_view1):
        for method in ["removeAllItems", "setLabel", "setTitle",
                       "addLegend", "invertX", "invertY"]:
            with patch.object(graph_view1._cw, method) as mocked:
                getattr(graph_view1, method)()
                mocked.assert_called_once()

    def test_axis_and_legend(self, graph_view1):
        view = graph_view1

        view.showAxis()
        assert view._cw.getAxis("left").isVisible()
        assert view._cw.getAxis("left").isVisible()
        view.hideAxis()
        assert not view._cw.getAxis("left").isVisible()
        assert not view._cw.getAxis("left").isVisible()

        view.addLegend()
        assert view._cw._legend.isVisible()
        view.hideLegend()
        assert not view._cw._legend.isVisible()
        view.showLegend()
        assert view._cw._legend.isVisible()

    def test_plot1(self, graph_view1, add_plot_items1):
        view = graph_view1
        plot_items = add_plot_items1
        for i, plot in enumerate(plot_items):
            x = np.arange(20)
            y = np.random.rand(20)
            y[-i-1:-1] = np.nan
            if isinstance(plot, ErrorbarPlotItem):
                plot.setData(x, y, y - 0.1, y + 0.1)
            else:
                plot.setData(x, y)
            _display()

        view._cw._onLogXScaleToggled(True)
        _display()
        view._cw._onLogYScaleToggled(True)
        _display()

        for plot in plot_items:
            plot.setData([], [])
            _display()

    def test_plot2(self, graph_view2, add_plot_items2):
        view = graph_view2
        plot_items = add_plot_items2
        for i, plot in enumerate(plot_items):
            x = np.arange(20)
            y = np.random.rand(20)
            y[-i-1:-1] = np.nan
            if isinstance(plot, ErrorbarPlotItem):
                plot.setData(x, y, y - 0.1, y + 0.1)
            else:
                plot.setData(x, y)
            _display()

        view._cw._onLogXScaleToggled(True)
        _display()
        view._cw._onLogYScaleToggled(True)
        _display()

        for plot in plot_items:
            plot.setData([], [])
            _display()


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


class TestHistPlotWidgetF:
    def test_update(self):
        view = HistWidgetF()
        # TODO
