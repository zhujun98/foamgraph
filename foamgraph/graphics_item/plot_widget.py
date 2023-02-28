"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import OrderedDict
import warnings
from itertools import chain
from typing import Optional

from ..backend.QtCore import pyqtSignal, pyqtSlot, QPointF, Qt
from ..backend.QtWidgets import (
    QAction, QActionGroup, QCheckBox, QGraphicsGridLayout, QGraphicsItem,
    QGridLayout, QHBoxLayout, QLabel, QMenu, QSizePolicy, QSlider, QWidget, QWidgetAction
)

from .axis_item import AxisItem
from .canvas import Canvas
from .graphics_item import GraphicsWidget
from .label_item import LabelItem
from .legend_item import LegendItem
from .line_item import InfiniteHorizontalLineItem, InfiniteVerticalLineItem
from .plot_item import PlotItem


class PlotWidget(GraphicsWidget):
    """2D plot widget for displaying graphs or an image."""

    cross_toggled_sgn = pyqtSignal(bool)

    def __init__(self, *, parent: QGraphicsItem = None, image: bool = False):
        super().__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self._items = set()
        # The insertion order of PlotItems must be kept because of the legend.
        # Although QGraphicsScene maintain the sequence of QGraphicsItem, the
        # LegendItem does not guarantee this since legend can be enabled after
        # all the PlotItems are added, so it must get the order information
        # from somewhere. Therefore, we use OrderedDict here to maintain the
        # insertion order of PlotItems.
        self._plot_items = OrderedDict()  # PlotItem: None
        self._plot_items_y2 = OrderedDict()  # PlotItem: None

        self._vb = Canvas(parent=self, image=image)
        self._vb_y2 = None

        self._v_line = None
        self._h_line = None
        self._cross_cursor_lb = LabelItem('')

        self._legend = None
        self._axes = {}
        self._title = LabelItem('')

        self._layout = QGraphicsGridLayout()

        self.initUI()
        self.initConnections()

    def initUI(self):
        layout = self._layout

        layout.setContentsMargins(*self.CONTENT_MARGIN)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        layout.addItem(self._cross_cursor_lb, 0, 1)
        layout.addItem(self._title, 1, 1,
                       alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addItem(self._vb, 2, 1)

        for i in range(5):
            layout.setRowPreferredHeight(i, 0)
            layout.setRowMinimumHeight(i, 0)
            layout.setRowSpacing(i, 0)
            layout.setRowStretchFactor(i, 1)

        for i in range(3):
            layout.setColumnPreferredWidth(i, 0)
            layout.setColumnMinimumWidth(i, 0)
            layout.setColumnSpacing(i, 0)
            layout.setColumnStretchFactor(i, 1)

        layout.setRowStretchFactor(2, 100)
        layout.setColumnStretchFactor(1, 100)

        self.setLayout(layout)

        self._initCrossCursor()
        self._initAxisItems()
        self.setTitle()

    def initConnections(self):
        self._vb.cross_cursor_toggled_sgn.connect(self.onCrossCursorToggled)

    def _initCrossCursor(self):
        self._v_line = InfiniteVerticalLineItem(0.)
        self._v_line.setDraggable(False)
        self._h_line = InfiniteHorizontalLineItem(0.)
        self._h_line.setDraggable(False)
        self._vb.addItem(self._v_line, ignore_bounds=True)
        self._vb.addItem(self._h_line, ignore_bounds=True)

        self.onCrossCursorToggled(False)

    def _initAxisItems(self):
        for name, edge, pos in (('bottom', Qt.Edge.BottomEdge, (3, 1)),
                                ('left', Qt.Edge.LeftEdge, (2, 0)),
                                ('right', Qt.Edge.RightEdge, (2, 2))):
            axis = AxisItem(edge, parent=self)

            self._axes[name] = axis
            self._layout.addItem(axis, *pos)
            axis.setZValue(-1000)
            axis.setFlag(axis.GraphicsItemFlag.ItemNegativeZStacksBehindParent)

        x_axis = self._axes['bottom']
        x_axis.linkToCanvas(self._vb)
        x_axis.log_Scale_toggled_sgn.connect(self.onLogXScaleToggled)

        y_axis = self._axes['left']
        y_axis.linkToCanvas(self._vb)
        y_axis.log_Scale_toggled_sgn.connect(self.onLogYScaleToggled)

        y2_axis = self._axes['right']
        y2_axis.hide()
        y2_axis.log_Scale_toggled_sgn.connect(self.onLogY2ScaleToggled)

    def clearAllPlotItems(self):
        """Clear data on all the plot items."""
        for item in chain(self._plot_items, self._plot_items_y2):
            item.setData([], [])

    def onCrossCursorToggled(self, state: bool):
        # scene is None at initialization
        scene = self.scene()
        if state:
            self._cross_cursor_lb.setVisible(True)
            self._cross_cursor_lb.setMaximumHeight(30)
            self._layout.setRowFixedHeight(0, 30)

            self._v_line.show()
            self._h_line.show()

            if scene is not None:
                scene.mouse_moved_sgn.connect(self.onCrossCursorMoved)
        else:
            self._cross_cursor_lb.setVisible(False)
            self._cross_cursor_lb.setMaximumHeight(0)
            self._layout.setRowFixedHeight(0, 0)

            self._v_line.hide()
            self._h_line.hide()

            if scene is not None:
                scene.mouse_moved_sgn.disconnect(self.onCrossCursorMoved)

    def onCrossCursorMoved(self, pos):
        m_pos = self._vb.mapSceneToView(pos)
        x, y = m_pos.x(), m_pos.y()
        self._v_line.setValue(x)
        self._h_line.setValue(y)
        self._cross_cursor_lb.setPlainText(f"x = {x}, y = {y}")

    def onLogXScaleToggled(self, state: bool):
        for item in chain(self._plot_items, self._plot_items_y2):
            item.setLogX(state)
        self._vb.updateAutoRange()

    def onLogYScaleToggled(self, state: bool):
        for item in self._plot_items:
            item.setLogY(state)
        self._vb.updateAutoRange()

    def onLogY2ScaleToggled(self, state: bool):
        for item in self._plot_items_y2:
            item.setLogY(state)
        self._vb_y2.updateAutoRange()

    def addItem(self, item, *,
                ignore_bounds: bool = False,
                y2: bool = False) -> None:
        """Add a graphics item to Canvas."""
        if item in self._items:
            warnings.warn(f"Item {item} already added to PlotItem.")
            return

        self._items.add(item)

        if isinstance(item, PlotItem):
            if y2:
                if self.getAxis('bottom').log_scale:
                    item.setLogX(True)

                self._plot_items_y2[item] = None
            else:
                if self.getAxis('bottom').log_scale:
                    item.setLogX(True)

                if self.getAxis('left').log_scale:
                    item.setLogY(True)

                self._plot_items[item] = None

            if self._legend is not None:
                self._legend.addItem(item)

        if y2:
            vb = self._vb_y2
            if vb is None:
                vb = Canvas(parent=self)
                y2_axis = self.getAxis('right')
                y2_axis.linkToCanvas(vb)
                y2_axis.show()
                vb.linkXTo(self._vb)
                vb.setZValue(self._vb.zValue() - 1)
                self._vb_y2 = vb
                # _vb_y2 is not added to the layout
                self._vb.geometryChanged.connect(
                    lambda: vb.setGeometry(self._vb.geometry()))
        else:
            vb = self._vb

        vb.addItem(item, ignore_bounds=ignore_bounds)

    def removeItem(self, item):
        """Add a graphics item to Canvas."""
        if item not in self._items:
            return

        self._items.remove(item)

        if item in self._plot_items_y2:
            del self._plot_items_y2[item]
            if self._legend is not None:
                self._legend.removeItem(item)
            self._vb_y2.removeItem(item)
            return

        if item in self._plot_items:
            del self._plot_items[item]
            if self._legend is not None:
                self._legend.removeItem(item)

        self._vb.removeItem(item)

    def removeAllItems(self):
        """Remove all graphics items from the Canvas."""
        for item in self._items:
            if item in self._plot_items_y2:
                self._vb_y2.removeItem(item)
            else:
                self._vb.removeItem(item)

        if self._legend is not None:
            self._legend.removeAllItems()

        self._plot_items.clear()
        self._plot_items_y2.clear()
        self._items.clear()

    def getAxis(self, axis: str) -> AxisItem:
        """Return the specified AxisItem.

        :param axis: one of 'left', 'bottom', 'right', or 'top'.
        """
        return self._axes[axis]

    def showAxis(self, axis: str) -> None:
        """Show the given axis.

        :param axis: one of 'left', 'bottom', 'right', or 'top'.
        """
        self.getAxis(axis).show()

    def hideAxis(self, axis: str) -> None:
        """Show the given axis.

        :param axis: one of 'left', 'bottom', 'right', or 'top'.
        """
        self.getAxis(axis).hide()

    def addLegend(self, pos: Optional[QPointF] = None,
                  **kwargs):
        """Add a LegendItem if it does not exist."""
        if self._legend is None:
            self._legend = LegendItem(parent=self._vb, **kwargs)

            for item in chain(self._plot_items, self._plot_items_y2):
                self._legend.addItem(item)

            if pos is None:
                # TODO: use a value which is proportional to the plot size
                pos = QPointF(20., 20.)
            self._legend.setPos(pos)

        return self._legend

    def showLegend(self, show=True) -> None:
        """Show or hide the legend.

        :param bool show: whether to show the legend.
        """
        if show:
            self._legend.show()
        else:
            self._legend.hide()

    def setLabel(self, axis: str, text=None) -> None:
        """Set the label for an axis. Basic HTML formatting is allowed.

        :param str axis: one of 'left', 'bottom', 'right', or 'top'.
        :param str text: text to display along the axis. HTML allowed.
        """
        self.getAxis(axis).setLabel(text=text)
        self.showAxis(axis)

    def showLabel(self, axis, show=True) -> None:
        """Show or hide one of the axis labels.

        :param str axis: one of 'left', 'bottom', 'right', or 'top'.
        :param bool show: whether to show the label.
        """
        self.getAxis(axis).showLabel(show)

    def setTitle(self, *args) -> None:
        """Set the title of the plot."""
        title = None if len(args) == 0 else args[0]
        if title is None:
            self._title.setMaximumHeight(0)
            self._layout.setRowFixedHeight(1, 0)
            self._title.setVisible(False)
        else:
            self._title.setMaximumHeight(30)
            self._layout.setRowFixedHeight(1, 30)
            self._title.setPlainText(title)
            self._title.setVisible(True)

    def invertX(self, *args, **kwargs) -> None:
        self._vb.invertX(*args, **kwargs)

    def invertY(self, *args, **kwargs) -> None:
        self._vb.invertY(*args, **kwargs)
