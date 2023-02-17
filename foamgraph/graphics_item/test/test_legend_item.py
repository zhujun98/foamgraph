import pytest

from foamgraph import mkQApp, GraphView
from foamgraph.aesthetics import FColor
from foamgraph.backend.QtCore import QPoint, Qt
from foamgraph.backend.QtTest import QTest


app = mkQApp()


@pytest.fixture(scope='function')
def widget():
    class FooPlotWidget(GraphView):
        def __init__(self):
            super().__init__()
            self.plot1 = self.addBarPlot(label="1")
            self.plot2 = self.addCurvePlot(label="2")
            self.plot3 = self.addScatterPlot(label="3")
            self.plot4 = self.addErrorbarPlot()

            self.all_plots = [self.plot1, self.plot2, self.plot3, self.plot4]

    return FooPlotWidget()


class TestLegendItem:

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_initialization(self, widget, orientation):
        widget.addLegend(orientation=orientation)

        legend = widget._cw._legend

        # test setLabelColor
        color = FColor.mkColor('r')
        legend.setLabelColor(color)
        for plot in widget.all_plots:
            assert legend._items[plot][1]._item.defaultTextColor() == color

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_visible_change(self, widget, orientation):
        widget.addLegend(orientation=orientation)
        legend = widget._cw._legend

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

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_removal(self, widget, orientation):
        widget.addLegend(orientation=orientation)
        legend = widget._cw._legend

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

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_set_label(self, widget, orientation):
        widget.addLegend(orientation=orientation)
        legend = widget._cw._legend

        assert legend._items[widget.plot1][1].toPlainText() == "1"
        widget.plot1.setLabel("new 1")
        assert legend._items[widget.plot1][1].toPlainText() == "new 1"

        assert legend._items[widget.plot4][1].toPlainText() == ""
        widget.plot4.setLabel("new 4")
        assert legend._items[widget.plot4][1].toPlainText() == "new 4"

    def test_dragging(self, widget):
        widget.addLegend()

        # FIXME:
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton,
                         pos=QPoint(int(widget.width() / 2), int(widget.height() / 2)))
