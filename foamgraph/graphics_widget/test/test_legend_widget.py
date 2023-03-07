import pytest

from foamgraph import mkQApp
from foamgraph.backend.QtCore import QPoint, QPointF, Qt
from foamgraph.backend.QtTest import QTest
from foamgraph.aesthetics import FColor
from foamgraph.graph_view import GraphView

app = mkQApp()


@pytest.fixture(scope='function')
def widget():
    class FooPlot(GraphView):
        def __init__(self):
            super().__init__()
            self.plot1 = self.addBarPlot(label="1")
            self.plot2 = self.addCurvePlot(label="2")
            self.plot3 = self.addScatterPlot(label="3")
            self.plot4 = self.addErrorbarPlot()

            # PlotItem without label will not be added into Legend
            self.all_plots = [self.plot1, self.plot2, self.plot3]

    return FooPlot()


class TestLegendWidget:

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
        assert list(legend._items.keys()) == widget.all_plots
        if orientation == "vertical":
            assert legend._layout.rowCount() == 4
        else:
            assert legend._layout.count() == 2 * len(widget.all_plots)
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
        assert list(legend._items.keys()) == [widget.plot2, widget.plot3]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 4
        else:
            assert legend._layout.count() == 4

        widget.removeItem(widget.plot3)
        widget.removeItem(widget.plot4)
        assert list(legend._items.keys()) == [widget.plot2]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 2
        else:
            assert legend._layout.count() == 2

        widget._cw.removeItem(widget.plot2)
        if orientation == "vertical":
            assert legend._layout.rowCount() == 0
        else:
            assert legend._layout.count() == 0

    @pytest.mark.xfail
    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_set_label(self, widget, orientation):
        widget.addLegend(orientation=orientation)
        legend = widget._cw._legend

        assert legend._items[widget.plot1][1].toPlainText() == "1"
        widget.plot1.setLabel("new 1")
        assert legend._items[widget.plot1][1].toPlainText() == "new 1"

        assert widget.plot4 not in legend._items
        widget.plot4.setLabel("new 4")
        assert legend._items[widget.plot4][1].toPlainText() == "new 4"

    def test_legend_pos(self, widget):
        class View1(GraphView):
            def __init__(self):
                super().__init__()
                self.plot = self.addCurvePlot(label="curve")
                self.addLegend((15, 5))

        class View2(GraphView):
            def __init__(self):
                super().__init__()
                self.addLegend(QPointF(5, 15))
                self.plot = self.addCurvePlot(label="curve")

        assert View1()._cw._legend.pos() == QPointF(15., 5.)
        assert View2()._cw._legend.pos() == QPointF(5., 15.)

    def test_dragging(self, widget):
        widget.addLegend()

        # FIXME:
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton,
                         pos=QPoint(int(widget.width() / 2), int(widget.height() / 2)))
