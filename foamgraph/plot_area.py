"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import OrderedDict
import warnings
from itertools import chain
from typing import Optional

from .backend.QtCore import pyqtSignal, pyqtSlot, QPointF, Qt
from .backend.QtWidgets import (
    QCheckBox, QGraphicsGridLayout, QGraphicsItem, QGraphicsTextItem, QHBoxLayout,
    QLabel, QMenu, QSizePolicy, QSlider, QWidget, QWidgetAction
)

from .axis_item import AxisItem
from .graphics_item import GraphicsWidget
from .label_item import LabelItem
from .legend_item import LegendItem
from .plot_item import PlotItem
from .view_box import ViewBox


class PlotArea(GraphicsWidget):
    """GraphicsWidget implementing a standard 2D plotting area with axes.

    It has the following functionalities:

    - Manage placement of a ViewBox, AxisItems, and LabelItems;
    - Manage a list of GraphicsItems displayed inside the ViewBox;
    - Implement a context menu with display options.
    """

    cross_toggled_sgn = pyqtSignal(bool)

    _METER_ROW = 0
    _TITLE_ROW = 1

    def __init__(self, *,
                 enable_meter: bool = True,
                 enable_grid: bool = True,
                 enable_transform: bool = True,
                 parent: QGraphicsItem = None):
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

        self._vb = ViewBox(parent=self)
        self._vb_y2 = None

        self._legend = None
        self._axes = {}
        self._meter = LabelItem('')
        self._title = LabelItem('')

        # context menu
        self._show_cross_cb = QCheckBox("Cross cursor")

        self._show_x_grid_cb = QCheckBox("Show X Grid")
        self._show_y_grid_cb = QCheckBox("Show Y Grid")
        self._grid_opacity_sld = QSlider(Qt.Orientation.Horizontal)
        self._grid_opacity_sld.setMinimum(0)
        self._grid_opacity_sld.setMaximum(255)
        self._grid_opacity_sld.setValue(160)
        self._grid_opacity_sld.setSingleStep(1)

        self._log_x_cb = QCheckBox("Log X")
        self._log_y_cb = QCheckBox("Log Y")

        self._menus = []
        self._enable_meter = enable_meter
        self._enable_grid = enable_grid
        self._enable_transform = enable_transform

        self._show_meter = False

        self._layout = QGraphicsGridLayout()

        self.initUI()
        self.initConnections()

    def initUI(self):
        layout = self._layout

        layout.setContentsMargins(1, 1, 1, 1)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        layout.addItem(self._meter, self._METER_ROW, 1)
        layout.addItem(self._title, self._TITLE_ROW, 1,
                       alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addItem(self._vb, 3, 1)

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

        self._initAxisItems()
        self.setTitle()
        self.showMeter(self._show_meter)

        self._initContextMenu()

    def initConnections(self):
        self._show_cross_cb.toggled.connect(self._onShowCrossChanged)

        self._show_x_grid_cb.toggled.connect(self._onShowGridChanged)
        self._show_y_grid_cb.toggled.connect(self._onShowGridChanged)
        self._grid_opacity_sld.sliderReleased.connect(self._onShowGridChanged)

        self._log_x_cb.toggled.connect(self._onLogXChanged)
        self._log_y_cb.toggled.connect(self._onLogYChanged)

    def _initMeterManu(self):
        menu = QMenu("Meter")
        self._menus.append(menu)

        cross_act = QWidgetAction(menu)
        cross_act.setDefaultWidget(self._show_cross_cb)
        menu.addAction(cross_act)

    def _initGridMenu(self):
        menu = QMenu("Grid")
        self._menus.append(menu)

        show_x_act = QWidgetAction(menu)
        show_x_act.setDefaultWidget(self._show_x_grid_cb)
        menu.addAction(show_x_act)
        show_y_act = QWidgetAction(menu)
        show_y_act.setDefaultWidget(self._show_y_grid_cb)
        menu.addAction(show_y_act)
        opacity_act = QWidgetAction(menu)
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Opacity"))
        layout.addWidget(self._grid_opacity_sld)
        widget.setLayout(layout)
        opacity_act.setDefaultWidget(widget)
        menu.addAction(opacity_act)

    def _initTransformMenu(self):
        menu = QMenu("Transform")
        self._menus.append(menu)

        log_x_act = QWidgetAction(menu)
        log_x_act.setDefaultWidget(self._log_x_cb)
        menu.addAction(log_x_act)
        log_y_act = QWidgetAction(menu)
        log_y_act.setDefaultWidget(self._log_y_cb)
        menu.addAction(log_y_act)

    def _initContextMenu(self):
        if self._enable_meter:
            self._initMeterManu()

        if self._enable_grid:
            self._initGridMenu()

        if self._enable_transform:
            self._initTransformMenu()

    def _initAxisItems(self):
        for name, edge, pos in (('top', Qt.Edge.TopEdge, (2, 1)),
                                ('bottom', Qt.Edge.BottomEdge, (4, 1)),
                                ('left', Qt.Edge.LeftEdge, (3, 0)),
                                ('right', Qt.Edge.RightEdge, (3, 2))):
            axis = AxisItem(edge, parent=self)

            axis.linkToView(self._vb)
            self._axes[name] = {'item': axis, 'pos': pos}
            self._layout.addItem(axis, *pos)
            axis.setZValue(-1000)
            axis.setFlag(axis.GraphicsItemFlag.ItemNegativeZStacksBehindParent)

            self.showAxis(name, name in ['left', 'bottom'])

    def getViewBox(self):
        return self._vb

    def clearAllPlotItems(self):
        """Clear data on all the plot items."""
        for item in chain(self._plot_items, self._plot_items_y2):
            item.setData([], [])

    @pyqtSlot(bool)
    def _onShowCrossChanged(self, state):
        self.showMeter(state)
        self.cross_toggled_sgn.emit(state)

    @pyqtSlot()
    def _onShowGridChanged(self):
        alpha = self._grid_opacity_sld.value()
        x = alpha if self._show_x_grid_cb.isChecked() else False
        y = alpha if self._show_y_grid_cb.isChecked() else False
        self.getAxis('bottom').setGrid(x)
        self.getAxis('left').setGrid(y)

    @pyqtSlot(bool)
    def _onLogXChanged(self, state):
        for item in chain(self._plot_items, self._plot_items_y2):
            item.setLogX(state)
        self.getAxis("bottom").setLogMode(state)
        self._vb.autoRange(disableAutoRange=False)

    @pyqtSlot(bool)
    def _onLogYChanged(self, state):
        for item in self._plot_items:
            item.setLogY(state)
        self.getAxis("left").setLogMode(state)
        self._vb.autoRange(disableAutoRange=False)

    def _updateY2View(self):
        self._vb_y2.setGeometry(self._vb.sceneBoundingRect())
        # not sure this is required
        # vb.linkedViewChanged(self._plot_area.vb, vb.XAxis)

    def addItem(self, item, *,
                ignore_bounds: bool = False,
                y2: bool = False) -> None:
        """Add a graphics item to ViewBox."""
        if item in self._items:
            warnings.warn(f"Item {item} already added to PlotItem.")
            return

        self._items.add(item)

        if isinstance(item, PlotItem):
            if y2:
                if self._log_x_cb.isChecked():
                    item.setLogX(True)

                self._plot_items_y2[item] = None
            else:
                if self._log_x_cb.isChecked():
                    item.setLogX(True)

                if self._log_y_cb.isChecked():
                    item.setLogY(True)

                self._plot_items[item] = None

            if self._legend is not None:
                self._legend.addItem(item)

        if y2:
            vb = self._vb_y2
            if vb is None:
                vb = ViewBox()
                self.scene().addItem(vb)
                right_axis = self.getAxis('right')
                right_axis.linkToView(vb)
                right_axis.show()
                vb.setXLink(self._vb)
                self._vb_y2 = vb
                self._vb.sigResized.connect(self._updateY2View)
        else:
            vb = self._vb

        vb.addItem(item, ignoreBounds=ignore_bounds)

    def removeItem(self, item):
        """Add a graphics item to ViewBox."""
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
        """Remove all graphics items from the ViewBox."""
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

    def getContextMenus(self, event):
        """Override."""
        return self._menus

    def getAxis(self, axis: str):
        """Return the specified AxisItem.

        :param axis: one of 'left', 'bottom', 'right', or 'top'.
        """
        return self._axes[axis]['item']

    def showAxis(self, axis: str, show: bool = True) -> None:
        """Show or hide the given axis.

        :param axis: one of 'left', 'bottom', 'right', or 'top'.
        :param show: whether to show the axis.
        """
        s = self.getAxis(axis)
        if show:
            s.show()
        else:
            s.hide()

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

    def setLabel(self, axis, text=None, units=None, **args) -> None:
        """Set the label for an axis. Basic HTML formatting is allowed.

        :param str axis: one of 'left', 'bottom', 'right', or 'top'.
        :param str text: text to display along the axis. HTML allowed.
        """
        self.getAxis(axis).setLabel(text=text, units=units, **args)
        self.showAxis(axis)

    def showLabel(self, axis, show=True) -> None:
        """Show or hide one of the axis labels.

        :param str axis: one of 'left', 'bottom', 'right', or 'top'.
        :param bool show: whether to show the label.
        """
        self.getAxis(axis).showLabel(show)

    def showMeter(self, show=True):
        """Show or hide the meter bar.

        :param bool show: whether to show the meter bar.
        """
        row = self._METER_ROW
        if not show:
            self._meter.setMaximumHeight(0)
            self._layout.setRowFixedHeight(row, 0)
            self._meter.setVisible(False)
        else:
            self._meter.setMaximumHeight(30)
            self._layout.setRowFixedHeight(row, 30)
            self._meter.setVisible(True)

        self._show_meter = show

    def setMeter(self, pos):
        """Set the meter of the plot."""
        if not self._show_meter:
            return

        if pos is None:
            self._meter.setText("")
        else:
            x, y = pos
            self._meter.setText(f"x = {x}, y = {y}")

    def setTitle(self, *args) -> None:
        """Set the title of the plot."""
        row = self._TITLE_ROW
        title = None if len(args) == 0 else args[0]
        if title is None:
            self._title.setMaximumHeight(0)
            self._layout.setRowFixedHeight(row, 0)
            self._title.setVisible(False)
        else:
            self._title.setMaximumHeight(30)
            self._layout.setRowFixedHeight(row, 30)
            self._title.setPlainText(title)
            self._title.setVisible(True)

    def setAspectLocked(self, *args, **kwargs) -> None:
        self._vb.setAspectLocked(*args, **kwargs)

    def invertX(self, *args, **kwargs) -> None:
        self._vb.invertX(*args, **kwargs)

    def invertY(self, *args, **kwargs) -> None:
        self._vb.invertY(*args, **kwargs)

    def autoRange(self, *args, **kwargs) -> None:
        self._vb.autoRange(*args, **kwargs)

    def mapSceneToView(self, *args, **kwargs):
        return self._vb.mapSceneToView(*args, **kwargs)
