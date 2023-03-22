import pytest

from foamgraph.backend.QtCore import QPoint, QPointF, Qt
from foamgraph.backend.QtTest import QTest
from foamgraph.aesthetics import FColor
from foamgraph.graph_view import GraphView
from foamgraph.test import processEvents


@pytest.fixture(scope='function')
def graph_view():
    class FooGraphView(GraphView):
        def __init__(self):
            super().__init__()
            self.plot1 = self.addBarPlot(label="1")
            self.plot2 = self.addCurvePlot(label="2")
            self.plot3 = self.addScatterPlot(label="3")
            self.plot4 = self.addErrorbarPlot()

            # PlotItem without label will not be added into Legend
            self.all_plots = [self.plot1, self.plot2, self.plot3]

    view = FooGraphView()
    view.show()
    processEvents()
    return view


class TestLegendWidget:

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_initialization(self, graph_view, orientation):
        graph_view.addLegend(orientation=orientation)

        legend = graph_view._cw._legend

        # test setLabelColor
        color = FColor.mkColor('r')
        legend.setLabelColor(color)
        for plot in graph_view.all_plots:
            assert legend._items[plot][1]._item.defaultTextColor() == color

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_visible_change(self, graph_view, orientation):
        graph_view.addLegend(orientation=orientation)
        legend = graph_view._cw._legend

        # setting a PlotItem invisible only changes the visibility of the
        # sample and label in the legend
        graph_view.plot1.setVisible(False)
        assert list(legend._items.keys()) == graph_view.all_plots
        if orientation == "vertical":
            assert legend._layout.rowCount() == 4
        else:
            assert legend._layout.count() == 2 * len(graph_view.all_plots)
        sample, label = legend._items[graph_view.plot1]
        assert not sample.isVisible()
        assert not label.isVisible()

    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_removal(self, graph_view, orientation):
        graph_view.addLegend(orientation=orientation)
        legend = graph_view._cw._legend

        # Note: An empty row or col in QGraphicsGridLayout will stay unless it is the
        #       last one.

        graph_view.removeItem(graph_view.plot1)
        assert list(legend._items.keys()) == [graph_view.plot2, graph_view.plot3]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 4
        else:
            assert legend._layout.count() == 4

        graph_view.removeItem(graph_view.plot3)
        graph_view.removeItem(graph_view.plot4)
        assert list(legend._items.keys()) == [graph_view.plot2]
        if orientation == "vertical":
            assert legend._layout.rowCount() == 2
        else:
            assert legend._layout.count() == 2

        graph_view._cw.removeItem(graph_view.plot2)
        if orientation == "vertical":
            assert legend._layout.rowCount() == 0
        else:
            assert legend._layout.count() == 0

    @pytest.mark.xfail
    @pytest.mark.parametrize("orientation",
                             [Qt.Orientation.Vertical, Qt.Orientation.Horizontal])
    def test_plot_item_set_label(self, graph_view, orientation):
        graph_view.addLegend(orientation=orientation)
        legend = graph_view._cw._legend

        assert legend._items[graph_view.plot1][1].toPlainText() == "1"
        graph_view.plot1.setLabel("new 1")
        assert legend._items[graph_view.plot1][1].toPlainText() == "new 1"

        assert graph_view.plot4 not in legend._items
        graph_view.plot4.setLabel("new 4")
        assert legend._items[graph_view.plot4][1].toPlainText() == "new 4"

    def test_legend_pos(self):
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

    def test_dragging(self, graph_view):
        graph_view.addLegend()

        # FIXME:
        QTest.mouseClick(graph_view, Qt.MouseButton.LeftButton,
                         pos=QPoint(int(graph_view.width() / 2),
                                    int(graph_view.height() / 2)))
