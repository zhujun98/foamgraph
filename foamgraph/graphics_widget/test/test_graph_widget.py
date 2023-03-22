import pytest
from unittest.mock import patch

from foamgraph.backend.QtCore import QPoint, QPointF, Qt
from foamgraph.graphics_item import (
    BarPlotItem, CurvePlotItem, ErrorbarPlotItem, CrossMouseCursorItem,
    MouseCursorItem, RectROI, ScatterPlotItem
)
from foamgraph.graphics_widget import (
    AxisWidget, LabelWidget, LegendWidget, GraphWidget
)
from foamgraph.test import processEvents


@pytest.fixture(scope="function")
def gwidget():
    widget = GraphWidget()
    processEvents()
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


def test_mouse_cursor_context_menu(gwidget):
    canvas = gwidget._canvas
    cursor_show_act = canvas.getMenuAction("Cursor_Show")

    assert not cursor_show_act.isChecked()
    assert canvas.getMenuAction("Cursor_Style_Cross").isChecked()
    assert isinstance(gwidget._mouse_cursor, CrossMouseCursorItem)
    assert not gwidget._mouse_cursor.isVisible()

    canvas.getMenuAction("Cursor_Style_Simple").trigger()
    assert cursor_show_act.isChecked()
    assert isinstance(gwidget._mouse_cursor, MouseCursorItem)
    assert not hasattr(gwidget._mouse_cursor, "_v_line")
    assert gwidget._mouse_cursor.isVisible()

    canvas.getMenuAction("Cursor_Style_InfiniteCross").trigger()
    assert isinstance(gwidget._mouse_cursor, CrossMouseCursorItem)

    cursor_show_act.trigger()
    assert not gwidget._mouse_cursor.isVisible()


def test_log_scale_context_menu(gwidget):
    x_axis = gwidget._axes["bottom"]
    y_axis = gwidget._axes["left"]
    y2_axis = gwidget._axes["right"]
    log_x_act = x_axis.getMenuAction("LogScale")
    log_y_act = y_axis.getMenuAction("LogScale")
    log_y2_act = y2_axis.getMenuAction("LogScale")

    plot_item1 = CurvePlotItem()
    plot_item2 = ScatterPlotItem()
    plot_item3 = BarPlotItem()
    gwidget.addItem(plot_item1)
    gwidget.addItem(plot_item2)
    gwidget.addItem(plot_item3, y2=True)
    with patch.object(plot_item1, "updateGraph") as mocked1:
        with patch.object(plot_item2, "updateGraph") as mocked2:
            with patch.object(plot_item3, "updateGraph") as mocked3:

                assert not x_axis.logScale()
                assert not y_axis.logScale()
                assert not y2_axis.logScale()

                log_x_act.setChecked(True)
                assert x_axis.logScale()
                assert not y_axis.logScale()
                mocked1.assert_called_once()
                mocked2.assert_called_once()
                mocked3.assert_called_once()
                mocked1.reset_mock()
                mocked2.reset_mock()
                mocked3.reset_mock()

                log_y_act.setChecked(True)
                assert x_axis.logScale()
                assert y_axis.logScale()
                assert not y2_axis.logScale()
                mocked1.assert_called_once()
                mocked2.assert_called_once()
                mocked3.assert_not_called()
                mocked1.reset_mock()
                mocked2.reset_mock()

                log_y2_act.setChecked(True)
                assert y2_axis.logScale()
                mocked1.assert_not_called()
                mocked2.assert_not_called()
                mocked3.assert_called_once()
