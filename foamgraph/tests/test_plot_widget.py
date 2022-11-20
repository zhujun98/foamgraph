from unittest.mock import MagicMock, patch

import numpy as np

from foamgraph import mkQApp, HistWidgetF, PlotWidgetF, TimedPlotWidgetF
from foamgraph.plot_items import ErrorbarItem

from . import _display


app = mkQApp()


class TestPlotWidget:
    @classmethod
    def setup_class(cls):
        # test addLegend before adding plot items
        widget = PlotWidgetF()
        widget.setXLabel("x label")
        widget.setYLabel("y label")
        widget.addLegend()
        cls._curve1 = widget.plotCurve(label="curve1")
        cls._scatter1 = widget.plotScatter(label="scatter1")
        cls._bar2 = widget.plotBar(label="bar2", y2=True)
        cls._statistics2 = widget.plotErrorbar(label="errorbar2", y2=True)
        cls._widget1 = widget
        if _display():
            widget.show()

        # test addLegend after adding plot items
        widget = PlotWidgetF()
        widget.setXYLabels("x label", "y label", y2="y2 label")
        cls._bar1 = widget.plotBar(label="bar1")
        cls._statistics1 = widget.plotErrorbar(label="errorbar1")
        cls._curve2 = widget.plotCurve(label="curve2", y2=True)
        cls._scatter2 = widget.plotScatter(label="scatter2", y2=True)
        widget.addLegend()
        cls._widget2 = widget
        if _display():
            widget.show()

        cls._plot_items1 = [cls._curve1, cls._scatter1, cls._bar2, cls._statistics2]
        cls._plot_items2 = [cls._bar1, cls._statistics1, cls._curve2, cls._scatter2]

    def test_plots(self):
        assert len(self._widget1._plot_area._items) == 6
        assert len(self._widget2._plot_area._items) == 6

    def test_forwarded_methods(self):
        widget = self._widget1

        for method in ["removeAllItems", "setAspectLocked", "setLabel", "setTitle",
                       "setAnnotationList", "addLegend", "invertX", "invertY", "autoRange"]:
            with patch.object(widget._plot_area, method) as mocked:
                getattr(widget, method)()
                mocked.assert_called_once()

    def test_axis_and_legend(self):
        widget = self._widget1

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

    def test_plot1(self):
        # widget1

        for i, plot in enumerate(self._plot_items1):
            x = np.arange(20)
            y = np.random.rand(20)
            y[-i-1:-1] = np.nan
            if isinstance(plot, ErrorbarItem):
                plot.setData(x, y, y - 0.1, y + 0.1)
            else:
                plot.setData(x, y)
            _display()

        self._widget1._plot_area._onLogXChanged(True)
        _display()
        self._widget1._plot_area._onLogYChanged(True)
        _display()

        for plot in self._plot_items1:
            plot.setData([], [])
            _display()

        # widget2

        for i, plot in enumerate(self._plot_items2):
            x = np.arange(20)
            y = np.random.rand(20)
            y[-i-1:-1] = np.nan
            if isinstance(plot, ErrorbarItem):
                plot.setData(x, y, y - 0.1, y + 0.1)
            else:
                plot.setData(x, y)
            _display()

        self._widget2._plot_area._onLogXChanged(True)
        _display()
        self._widget2._plot_area._onLogYChanged(True)
        _display()

        for plot in self._plot_items2:
            plot.setData([], [])
            _display()

    def test_cross_cursor(self):
        widget = self._widget1
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
