import pytest

from foamgraph import mkQApp, PlotWidgetF

from foamgraph.backend.QtCore import QPoint, Qt
from foamgraph.backend.QtTest import QTest


app = mkQApp()


class TestLegendWidget:
    class FooPlotWidget(PlotWidgetF):
        def __init__(self):
            super().__init__()
            self.plot1 = self.plotBar(label="1")
            self.plot2 = self.plotCurve(label="2")
            self.plot3 = self.plotScatter(label="3")
            self.plot4 = self.plotErrorbar()

    @pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
    def test_initialization(self, orientation):
        widget = self.FooPlotWidget()
        with pytest.raises(ValueError):
            widget.addLegend(orientation="unknown")
        widget.addLegend(orientation=orientation)

    @pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
    def test_plot_item_visible_change(self, orientation):
        widget = self.FooPlotWidget()
        widget.addLegend(orientation=orientation)
        legend = widget._plot_area._legend

        # setting a PlotItem invisible only changes the visibility of the
        # sample and label in the legend
        widget.plot1.setVisible(False)
        assert list(legend._items.keys()) == [widget.plot1, widget.plot2, widget.plot3, widget.plot4]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 4
        else:
            assert legend._layout.count() == 8
        sample, label = legend._items[widget.plot1]
        assert not sample.isVisible()
        assert not label.isVisible()

    @pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
    def test_plot_item_removal(self, orientation):
        widget = self.FooPlotWidget()
        widget.addLegend(orientation=orientation)
        legend = widget._plot_area._legend

        # Note: An empty row or col in QGraphicsGridLayout will stay unless it is the
        #       last one.

        widget.removeItem(widget.plot1)
        assert list(legend._items.keys()) == [widget.plot2, widget.plot3, widget.plot4]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 4
        else:
            assert legend._layout.count() == 6

        widget.removeItem(widget.plot3)
        widget.removeItem(widget.plot4)
        assert list(legend._items.keys()) == [widget.plot2]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 2
        else:
            assert legend._layout.count() == 2

        widget.removeAllItems()
        assert len(legend._items) == 0
        if orientation == "vertical":
            assert legend._layout.rowCount() == 0
        else:
            assert legend._layout.count() == 0

    @pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
    def test_plot_item_set_label(self, orientation):
        widget = self.FooPlotWidget()
        widget.addLegend(orientation=orientation)
        legend = widget._plot_area._legend

        assert legend._items[widget.plot1][1].text == "1"
        widget.plot1.setLabel("new 1")
        assert legend._items[widget.plot1][1].text == "new 1"

        assert legend._items[widget.plot4][1].text == ""
        widget.plot4.setLabel("new 4")
        assert legend._items[widget.plot4][1].text == "new 4"

    def test_dragging(self):
        widget = self.FooPlotWidget()
        widget.addLegend()

        # FIXME:
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton,
                         pos=QPoint(int(widget.width() / 2), int(widget.height() / 2)))
