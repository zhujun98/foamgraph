import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from foamgraph import mkQApp, HistWidgetF, PlotWidgetF, TimedPlotWidgetF
from foamgraph.graphics_item.plot_item import ErrorbarPlotItem

from . import _display


app = mkQApp()


@pytest.fixture
def plot_widget1():
    # test addLegend before adding plot items
    widget = PlotWidgetF()
    widget.setXLabel("x label")
    widget.setYLabel("y label")

    widget.addAnnotation()

    if _display():
        widget.show()
    return widget


@pytest.fixture
def add_plot_items1(plot_widget1):
    widget = plot_widget1
    widget.addLegend()  # add legend before plot items
    return [widget.addCurvePlot(label="curve1"),
            widget.addScatterPlot(label="scatter1"),
            widget.addBarPlot(label="bar2", y2=True),
            widget.addErrorbarPlot(label="errorbar2", y2=True)]


@pytest.fixture
def plot_widget2():
    widget = PlotWidgetF()
    widget.setXYLabels("x label", "y label", y2="y2 label")
    if _display():
        widget.show()
    return widget


@pytest.fixture
def add_plot_items2(plot_widget2):
    widget = plot_widget2  # add legend after plot items
    items = [widget.addBarPlot(label="bar1"),
             widget.addErrorbarPlot(label="errorbar1"),
             widget.addCurvePlot(label="curve2", y2=True),
             widget.addScatterPlot(label="scatter2", y2=True)]
    widget.addLegend()
    return items


class TestPlotWidget:

    def test_plots(self, plot_widget1, plot_widget2, add_plot_items1, add_plot_items2):
        assert len(plot_widget1._plot_area._items) == 7
        assert len(plot_widget2._plot_area._items) == 6

    def test_forwarded_methods(self, plot_widget1):
        for method in ["removeAllItems", "setLabel", "setTitle",
                       "addLegend", "invertX", "invertY", "autoRange"]:
            with patch.object(plot_widget1._plot_area, method) as mocked:
                getattr(plot_widget1, method)()
                mocked.assert_called_once()

    def test_axis_and_legend(self, plot_widget1):
        widget = plot_widget1

        widget.showAxis()
        assert widget._plot_area.getAxis("left").isVisible()
        assert widget._plot_area.getAxis("left").isVisible()
        widget.hideAxis()
        assert not widget._plot_area.getAxis("left").isVisible()
        assert not widget._plot_area.getAxis("left").isVisible()

        widget.addLegend()
        assert widget._plot_area._legend.isVisible()
        widget.hideLegend()
        assert not widget._plot_area._legend.isVisible()
        widget.showLegend()
        assert widget._plot_area._legend.isVisible()

    def test_plot1(self, plot_widget1, add_plot_items1):
        widget = plot_widget1
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

        widget._plot_area._onLogXChanged(True)
        _display()
        widget._plot_area._onLogYChanged(True)
        _display()

        for plot in plot_items:
            plot.setData([], [])
            _display()

    def test_plot2(self, plot_widget2, add_plot_items2):
        widget = plot_widget2
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

        widget._plot_area._onLogXChanged(True)
        _display()
        widget._plot_area._onLogYChanged(True)
        _display()

        for plot in plot_items:
            plot.setData([], [])
            _display()

    def test_cross_cursor(self, plot_widget1):
        widget = plot_widget1

        assert not widget._v_line.isVisible()
        assert not widget._h_line.isVisible()
        widget._plot_area._show_cross_cb.setChecked(True)
        assert widget._v_line.isVisible()
        assert widget._h_line.isVisible()

        # TODO: test mouse move


class TestTimedPlotWidgetF:
    def test_update(self):
        widget = TimedPlotWidgetF()
        widget.refresh = MagicMock()

        assert widget._data is None
        widget._refresh_imp()
        widget.refresh.assert_not_called()

        widget.updateF(1)
        widget._refresh_imp()
        widget.refresh.assert_called_once()


class TestHistPlotWidgetF:
    def test_update(self):
        widget = HistWidgetF()
        # TODO
