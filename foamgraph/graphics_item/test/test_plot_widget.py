import pytest
from unittest.mock import patch

from foamgraph.backend.QtCore import QPointF
from foamgraph.backend.QtTest import QSignalSpy

from foamgraph import mkQApp
from foamgraph.graphics_item.axis_item import AxisItem
from foamgraph.graphics_view import GraphicsView
from foamgraph.graphics_item import ImageItem
from foamgraph.graphics_item.label_item import LabelItem
from foamgraph.graphics_item.legend_item import LegendItem
from foamgraph.graphics_item import PlotWidget
from foamgraph.graphics_item import (
    CurvePlotItem, BarPlotItem, ScatterPlotItem, ErrorbarPlotItem
)
from foamgraph.graphics_item.roi import RectROI


app = mkQApp()


@pytest.fixture(scope="function")
def graphics_view():
    return GraphicsView()


@pytest.fixture(scope="function")
def pwidget(graphics_view):
    widget = PlotWidget()
    graphics_view.setCentralWidget(widget)
    return widget


def test_axes(pwidget):
    assert len(pwidget._axes) == 3
    for name, pos in [('left', (3, 0)), ('bottom', (4, 1))]:
        left_axis = pwidget._axes[name]
        assert isinstance(left_axis, AxisItem)
        assert left_axis.isVisible()
        assert pwidget.getAxis(name) is left_axis

        with patch.object(left_axis, "show") as mocked:
            pwidget.showAxis(name)
            mocked.assert_called_once()

        with patch.object(left_axis, "hide") as mocked:
            pwidget.hideAxis(name)
            mocked.assert_called_once()

        with patch.object(left_axis, "setLabel") as mocked:
            pwidget.setLabel(name, "abc")
            mocked.assert_called_once_with(text="abc")

        with patch.object(left_axis, "showLabel") as mocked:
            pwidget.showLabel(name)
            mocked.assert_called_once()

    for name in ['right']:
        assert not pwidget.getAxis(name).isVisible()


def test_legend(pwidget):
    assert pwidget._legend is None

    legend = pwidget.addLegend(QPointF(-30, -30))
    assert isinstance(pwidget._legend, LegendItem)
    assert legend, pwidget._legend

    # test addLegend when legend already exists
    pwidget.addLegend(QPointF(-10, -10))
    assert isinstance(pwidget._legend, LegendItem)
    assert legend is pwidget._legend


def test_title(pwidget):
    assert isinstance(pwidget._title, LabelItem)

    assert pwidget._title.maximumHeight() == 0
    assert not pwidget._title.isVisible()

    pwidget.setTitle("abcdefg")
    assert pwidget._title.maximumHeight() > 0
    assert pwidget._title.isVisible()


def test_forward_methods(pwidget):
    for method in ["invertY", "invertX"]:
        with patch.object(pwidget._vb, method) as mocked:
            getattr(pwidget, method)()
            mocked.assert_called_once()


def test_plot_item_manipulation(pwidget):
    image_item = ImageItem()
    pwidget.addItem(image_item)
    pwidget.addItem(RectROI(0))
    bar_graph_item = BarPlotItem(label="bar")
    pwidget.addItem(bar_graph_item, y2=True)
    errorbar_item = ErrorbarPlotItem()
    pwidget.addItem(errorbar_item)

    pwidget.addLegend()  # add legend when there are already added PlotItems

    curve_plot_item = CurvePlotItem(label="curve")
    pwidget.addItem(curve_plot_item)
    scatter_plot_item = ScatterPlotItem(label="scatter")
    pwidget.addItem(scatter_plot_item)

    assert len(pwidget._plot_items) == 3
    assert len(pwidget._plot_items_y2) == 1
    assert len(pwidget._items) == 6
    assert len(pwidget._vb._proxy._items) == 5
    assert len(pwidget._vb_y2._proxy._items) == 1
    assert len(pwidget._legend._items) == 3

    with patch.object(curve_plot_item, "setData") as mocked1:
        with patch.object(bar_graph_item, "setData") as mocked2:
            pwidget.clearAllPlotItems()
            mocked1.assert_called_once()
            mocked2.assert_called_once()

    # remove an item which does not exist
    pwidget.removeItem(BarPlotItem())
    assert len(pwidget._plot_items) == 3
    assert len(pwidget._plot_items_y2) == 1
    assert len(pwidget._items) == 6
    assert len(pwidget._vb._proxy._items) == 5
    assert len(pwidget._vb_y2._proxy._items) == 1
    assert len(pwidget._legend._items) == 3

    # remove an existing item
    pwidget.removeItem(bar_graph_item)
    assert len(pwidget._plot_items) == 3
    assert len(pwidget._plot_items_y2) == 0
    assert len(pwidget._items) == 5
    assert len(pwidget._vb._proxy._items) == 5
    assert len(pwidget._vb_y2._proxy._items) == 0
    assert len(pwidget._legend._items) == 2

    # remove an existing item which is not a PlotItem
    pwidget.removeItem(image_item)
    assert len(pwidget._plot_items) == 3
    assert len(pwidget._plot_items_y2) == 0
    assert len(pwidget._items) == 4
    assert len(pwidget._vb._proxy._items) == 4
    assert len(pwidget._vb_y2._proxy._items) == 0
    assert len(pwidget._legend._items) == 2

    # remove a PlotItem which does not has a name and hence was not added
    # into the legend
    pwidget.removeItem(errorbar_item)
    assert len(pwidget._legend._items) == 2

    pwidget.removeAllItems()
    assert len(pwidget._plot_items) == 0
    assert len(pwidget._plot_items_y2) == 0
    assert len(pwidget._items) == 0
    assert len(pwidget._vb._proxy._items) == 0
    assert len(pwidget._vb_y2._proxy._items) == 0
    assert len(pwidget._legend._items) == 0


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
