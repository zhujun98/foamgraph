import pytest
from unittest.mock import patch

from foamgraph.backend.QtCore import QPointF

from foamgraph import mkQApp
from foamgraph.graphics_item import (
    BarPlotItem, CurvePlotItem, ErrorbarPlotItem, RectROI, ScatterPlotItem
)
from foamgraph.graphics_widget import (
    AxisWidget, LabelWidget, LegendWidget, GraphWidget
)


app = mkQApp()


@pytest.fixture(scope="function")
def gwidget():
    widget = GraphWidget()
    return widget


def test_axes(gwidget):
    assert len(gwidget._axes) == 3
    for name in ['left', 'bottom']:
        axis = gwidget._axes[name]
        assert isinstance(axis, AxisWidget)
        assert axis.isVisible()

        with patch.object(axis, "setVisible") as mocked:
            gwidget.showAxis(name)
            mocked.assert_called_once_with(True)

            mocked.reset_mock()
            gwidget.showAxis(name, False)
            mocked.assert_called_once_with(False)

        with patch.object(axis, "setLabel") as mocked:
            gwidget.setLabel(name, "abc")
            mocked.assert_called_once_with(text="abc")

        with patch.object(axis, "showLabel") as mocked:
            gwidget.showLabel(name)
            mocked.assert_called_once_with(True)

            mocked.reset_mock()
            gwidget.showLabel(name, False)
            mocked.assert_called_once_with(False)

    for name in ['right']:
        axis = gwidget._axes[name]
        assert not axis.isVisible()

        item = CurvePlotItem(label="curve-1")
        gwidget.addItem(item)
        assert not axis.isVisible()
        item = CurvePlotItem(label="curve-2")
        gwidget.addItem(item, y2=True)
        assert axis.isVisible()


def test_invert(gwidget):
    canvas = gwidget._canvas
    with patch.object(canvas, "invertX") as mocked:
        gwidget.invertX()
        mocked.assert_called_once_with(True)

        mocked.reset_mock()
        gwidget.invertX(False)
        mocked.assert_called_once_with(False)

    with patch.object(canvas, "invertY") as mocked:
        gwidget.invertY()
        mocked.assert_called_once_with(True)

        mocked.reset_mock()
        gwidget.invertY(False)
        mocked.assert_called_once_with(False)


def test_legend(gwidget):
    assert gwidget._legend is None

    legend = gwidget.addLegend(QPointF(-30, -30))
    assert isinstance(legend, LegendWidget)
    assert legend is gwidget._legend

    # test addLegend when legend already exists
    gwidget.addLegend(QPointF(-10, -10))
    assert legend is gwidget._legend

    assert legend.isVisible()
    gwidget.showLegend(False)
    assert not legend.isVisible()


def test_title(gwidget):
    assert isinstance(gwidget._title, LabelWidget)

    assert gwidget._title.maximumHeight() == 0
    assert not gwidget._title.isVisible()

    gwidget.setTitle("abcdefg")
    assert gwidget._title.maximumHeight() > 0
    assert gwidget._title.isVisible()


def test_clear_data(gwidget):
    item1 = CurvePlotItem()
    gwidget.addItem(item1)
    item2 = BarPlotItem()
    gwidget.addItem(item2, y2=True)

    with patch.object(item1, "setData") as mocked1:
        with patch.object(item2, "setData") as mocked2:
            gwidget.clearData()
            mocked1.assert_called_once_with([], [])
            mocked2.assert_called_once_with([], [])  # y2


def test_plot_item_manipulation(gwidget):
    errorbar_item = ErrorbarPlotItem()
    gwidget.addItem(errorbar_item)

    bar_graph_item = BarPlotItem(label="bar")
    gwidget.addItem(bar_graph_item, y2=True)

    roi_item = RectROI()
    gwidget.addItem(roi_item)

    gwidget.addLegend()  # add legend when there are already added PlotItems

    curve_plot_item = CurvePlotItem(label="curve")
    gwidget.addItem(curve_plot_item)
    with pytest.raises(RuntimeError):
        gwidget.addItem(curve_plot_item)

    scatter_plot_item = ScatterPlotItem(label="scatter")
    gwidget.addItem(scatter_plot_item)

    assert len(gwidget._plot_items) == 3
    assert len(gwidget._plot_items_y2) == 1
    assert len(gwidget._canvas._proxy._items) == 4
    assert len(gwidget._canvas_y2._proxy._items) == 1
    assert len(gwidget._legend._items) == 3

    # remove an item which does not exist
    gwidget.removeItem(BarPlotItem())
    assert len(gwidget._plot_items) == 3
    assert len(gwidget._plot_items_y2) == 1
    assert len(gwidget._canvas._proxy._items) == 4
    assert len(gwidget._canvas_y2._proxy._items) == 1
    assert len(gwidget._legend._items) == 3

    # remove an existing item
    gwidget.removeItem(bar_graph_item)
    assert len(gwidget._plot_items) == 3
    assert len(gwidget._plot_items_y2) == 0
    assert len(gwidget._canvas._proxy._items) == 4
    assert len(gwidget._canvas_y2._proxy._items) == 0
    assert len(gwidget._legend._items) == 2

    # remove an existing item which is not a PlotItem
    gwidget.removeItem(roi_item)
    assert len(gwidget._plot_items) == 3
    assert len(gwidget._plot_items_y2) == 0
    assert len(gwidget._canvas._proxy._items) == 3
    assert len(gwidget._canvas_y2._proxy._items) == 0
    assert len(gwidget._legend._items) == 2

    # remove a PlotItem which does not has a name and hence was not added
    # into the legend
    gwidget.removeItem(errorbar_item)
    assert len(gwidget._legend._items) == 2

    gwidget.removeItem(curve_plot_item)
    gwidget.removeItem(scatter_plot_item)
    assert len(gwidget._plot_items) == 0
    assert len(gwidget._plot_items_y2) == 0
    assert len(gwidget._canvas._proxy._items) == 0
    assert len(gwidget._canvas_y2._proxy._items) == 0
    assert len(gwidget._legend._items) == 0


def test_context_menu():
    ...
    # area = self._area
    # event = object()
    # menus = self._area._menus
    #
    # self.assertEqual(3, len(menus))
    # self.assertEqual("Meter", menus[0].title())
    # self.assertEqual("Grid", menus[1].title())
    # self.assertEqual("Transform", menus[2].title())
    #
    # # test "Meter" actions
    # meter_actions = menus[0].actions()
    # self.assertFalse(area._show_meter)
    # self.assertFalse(area._meter.isVisible())
    # spy = QSignalSpy(area.cross_toggled_sgn)
    # meter_actions[0].defaultWidget().setChecked(True)
    # self.assertTrue(area._show_meter)
    # self.assertTrue(area._meter.isVisible())
    # self.assertEqual(1, len(spy))
    # meter_actions[0].defaultWidget().setChecked(False)
    # self.assertFalse(area._show_meter)
    # self.assertFalse(area._meter.isVisible())
    # self.assertEqual(2, len(spy))
    #
    # # test "Grid" actions
    # grid_actions = menus[1].actions()
    # alpha = area._grid_opacity_sld.value()
    # grid_actions[0].defaultWidget().setChecked(True)
    # self.assertEqual(alpha, area.getAxis("bottom").grid)
    # grid_actions[1].defaultWidget().setChecked(True)
    # self.assertEqual(alpha, area.getAxis("left").grid)
    #
    # # test "Transform" actions
    # plot_item = CurvePlotItem()
    # plot_item2 = ScatterPlotItem()
    # area.addItem(plot_item)
    # area.addItem(plot_item2, y2=True)
    # transform_actions = menus[2].actions()
    #
    # with patch.object(plot_item, "updateGraph") as mocked:
    #     with patch.object(plot_item2, "updateGraph") as mocked2:
    #         transform_actions[0].defaultWidget().setChecked(True)
    #         self.assertTrue(area.getAxis("bottom").logMode)
    #         # self.assertTrue(area.getAxis("top").logMode)
    #         self.assertTrue(plot_item._log_x_mode)
    #         self.assertTrue(plot_item2._log_x_mode)
    #         mocked.assert_called_once()
    #         mocked2.assert_called_once()
    #
    #         plot_item3 = CurvePlotItem()
    #         plot_item4 = ScatterPlotItem()
    #         area.addItem(plot_item3)
    #         area.addItem(plot_item4, y2=True)
    #         self.assertTrue(plot_item3._log_x_mode)
    #         self.assertTrue(plot_item4._log_x_mode)
    #
    # with patch.object(plot_item, "updateGraph") as mocked:
    #     with patch.object(plot_item2, "updateGraph") as mocked2:
    #         transform_actions[1].defaultWidget().setChecked(True)
    #         self.assertTrue(area.getAxis("left").logMode)
    #         # self.assertTrue(area.getAxis("right").logMode)
    #         self.assertTrue(plot_item._log_y_mode)
    #         self.assertFalse(plot_item2._log_y_mode)
    #         mocked.assert_called_once()
    #         mocked2.assert_not_called()
    #
    #         plot_item5 = CurvePlotItem()
    #         plot_item6 = ScatterPlotItem()
    #         area.addItem(plot_item5)
    #         area.addItem(plot_item6, y2=True)
    #         self.assertTrue(plot_item5._log_y_mode)
    #         self.assertFalse(plot_item6._log_y_mode)
    #
    # another_area = PlotWidget(
    #     enable_meter=False, enable_transform=False, enable_grid=False)
    # menus = another_area._menus
    # self.assertEqual(0, len(menus))
