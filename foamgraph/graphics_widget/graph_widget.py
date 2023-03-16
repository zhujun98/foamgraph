"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import OrderedDict
from itertools import chain
from typing import Optional, Union

from ..backend.QtCore import pyqtSignal, QPointF, Qt

from ..graphics_item import MouseCursorStyle, PlotItem
from .axis_widget import AxisWidget
from .canvas import Canvas
from .legend_widget import LegendWidget
from .plot_widget import PlotWidget


class GraphWidget(PlotWidget):
    """PlotWidget for displaying graphs."""

    def __init__(self, *, parent = None):
        super().__init__(parent=parent)

        self._plot_items = OrderedDict()  # PlotItem: None
        self._plot_items_y2 = OrderedDict()  # PlotItem: None
        self._canvas_y2 = None

        self._legend = None

        self._initUI()
        self._initConnections()

    def _initConnections(self) -> None:
        """Override."""
        super()._initConnections()
        self._canvas.setMouseMode(self._canvas.MouseMode.Pan)
        self._setMouseCursorStyle(MouseCursorStyle.Cross)
        self._canvas.getMenuAction("Cursor_Show").setChecked(False)

    def _initAxisItems(self):
        """Override."""
        for name, edge, pos in (
                ('bottom', Qt.Edge.BottomEdge, self._AXIS_BOTTOM_LOC),
                ('left', Qt.Edge.LeftEdge, self._AXIS_LEFT_LOC),
                ('right', Qt.Edge.RightEdge, self._AXIS_RIGHT_LOC)
        ):
            axis = AxisWidget(edge, parent=self)

            self._axes[name] = axis
            self._layout.addItem(axis, *pos)
            axis.setFlag(axis.GraphicsItemFlag.ItemNegativeZStacksBehindParent)

        x_axis = self._axes['bottom']
        x_axis.linkToCanvas(self._canvas)
        x_axis.log_Scale_toggled_sgn.connect(self._onLogXScaleToggled)

        y_axis = self._axes['left']
        y_axis.linkToCanvas(self._canvas)
        y_axis.log_Scale_toggled_sgn.connect(self._onLogYScaleToggled)

        # y2 axis
        y2_axis = self._axes['right']
        y2_axis.hide()
        y2_axis.log_Scale_toggled_sgn.connect(self._onLogY2ScaleToggled)

    def _onMouseCursorMoved(self, pos: QPointF) -> None:
        """Override."""
        super()._onMouseCursorMoved(pos)
        self._setMouseCursorLabel(pos.x(), pos.y())

    def _updateMouseCursorLabel(self) -> None:
        """Override."""
        pos = self._mouse_cursor.pos()
        pos = self._canvas.mapFromItemToView(self, pos)
        self._setMouseCursorLabel(pos.x(), pos.y())

    def _setMouseCursorLabel(self, x: float, y: float) -> None:
        self._mouse_cursor.setLabel(f"    {x:.1f}, {y:.1f}")

    def clearData(self) -> None:
        """Override."""
        for item in chain(self._plot_items, self._plot_items_y2):
            item.clearData()

    def _onLogXScaleToggled(self, state: bool):
        for item in chain(self._plot_items, self._plot_items_y2):
            item.setLogX(state)
        self._canvas.updateAutoRange()

    def _onLogYScaleToggled(self, state: bool):
        for item in self._plot_items:
            item.setLogY(state)
        self._canvas.updateAutoRange()

    def _onLogY2ScaleToggled(self, state: bool):
        for item in self._plot_items_y2:
            item.setLogY(state)
        self._canvas_y2.updateAutoRange()

    def addItem(self, item, *, y2: bool = False) -> None:
        """Override."""
        if y2:
            canvas = self._canvas_y2
            if canvas is None:
                canvas = Canvas(parent=self)
                y2_axis = self._axes['right']
                y2_axis.linkToCanvas(canvas)
                y2_axis.show()
                canvas.linkXTo(self._canvas)
                canvas.setZValue(self._canvas.zValue() - 1)
                self._canvas_y2 = canvas
                # _vb_y2 is not added to the layout
                self._canvas.geometryChanged.connect(
                    lambda: canvas.setGeometry(self._canvas.geometry()))
        else:
            canvas = self._canvas

        if isinstance(item, PlotItem):
            if y2:
                if self._axes['bottom'].logScale():
                    item.setLogX(True)

                self._plot_items_y2[item] = None
            else:
                if self._axes['bottom'].logScale():
                    item.setLogX(True)

                if self._axes['left'].logScale():
                    item.setLogY(True)

                self._plot_items[item] = None

            if self._legend is not None:
                self._legend.addItem(item)

        canvas.addItem(item)

    def removeItem(self, item):
        """Override."""
        if item in self._plot_items_y2:
            del self._plot_items_y2[item]
            if self._legend is not None:
                self._legend.removeItem(item)
            self._canvas_y2.removeItem(item)
            return

        if item in self._plot_items:
            del self._plot_items[item]
            if self._legend is not None:
                self._legend.removeItem(item)

        self._canvas.removeItem(item)

    def addLegend(self, pos: Optional[Union[tuple, list, QPointF]] = None,
                  **kwargs):
        """Add a LegendWidget if it does not exist."""
        if self._legend is None:
            self._legend = LegendWidget(parent=self._canvas, **kwargs)

            for item in chain(self._plot_items, self._plot_items_y2):
                self._legend.addItem(item)

            if pos is None:
                # TODO: use a value which is proportional to the plot size
                pos = QPointF(20., 20.)
            elif not isinstance(pos, QPointF):
                pos = QPointF(*pos)

            self._legend.setPos(pos)

        return self._legend

    def showLegend(self, visible: bool = True) -> None:
        """Show or hide the legend.

        :param visible: whether to show the legend.
        """
        self._legend.setVisible(visible)
