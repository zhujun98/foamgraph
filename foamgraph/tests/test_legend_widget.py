import pytest

from foamgraph import mkQApp, PlotWidgetF

from . import _display


app = mkQApp()


class TestLegendWidget:
    class FooPlotWidget(PlotWidgetF):
        def __init__(self):
            super().__init__()
            self._plot1 = self.plotBar()
            self._plot2 = self.plotCurve()
            self._plot3 = self.plotScatter()
            self._plot4 = self.plotErrorbar()

    def test_initialization(self):
        widget1 = self.FooPlotWidget()
        with pytest.raises(ValueError):
            widget1.addLegend(orientation="hori")
        widget1.addLegend(orientation="horizontal")

        widget2 = self.FooPlotWidget()
        widget2.addLegend(orientation="vertical")

        if _display():
            widget1.show()
            widget2.show()
