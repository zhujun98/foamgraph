"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod
from collections import OrderedDict
import warnings
from itertools import chain
from typing import Optional

from ..backend.QtCore import pyqtSignal, pyqtSlot, QPointF, Qt
from ..backend.QtWidgets import (
    QCheckBox, QGraphicsGridLayout, QGraphicsWidget,
    QGridLayout, QHBoxLayout, QLabel, QMenu, QSizePolicy, QSlider, QWidget,
    QWidgetAction
)

from ..aesthetics import FColor
from ..graphics_item import CrossCursorItem, PlotItem
from .axis_widget import AxisWidget
from .canvas import Canvas
from .graphics_widget import GraphicsWidget
from .label_widget import LabelWidget
from .legend_widget import LegendWidget


class PlotWidgetBase(GraphicsWidget):
    """2D plot widget for displaying graphs or an image."""

    _TITLE_LOC = (0, 1)
    _CANVAS_LOC = (1, 1)
    _AXIS_BOTTOM_LOC = (2, 1)
    _AXIS_LEFT_LOC = (1, 0)
    _AXIS_RIGHT_LOC = (1, 2)

    def __init__(self, *, parent: QGraphicsWidget = None):
        super().__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self._items = set()
        self._plot_items = OrderedDict()  # PlotItem: None

        self._canvas = Canvas(parent=self)

        self._axes = {}
        self._title = LabelWidget('')

        self._layout = QGraphicsGridLayout()

    def _init(self) -> None:
        self._initUI()
        self._initConnections()

    def _initUI(self) -> None:
        layout = self._layout

        layout.setContentsMargins(*self.CONTENT_MARGIN)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        layout.addItem(self._title, *self._TITLE_LOC,
                       alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addItem(self._canvas, *self._CANVAS_LOC)

        for i in range(4):
            layout.setRowPreferredHeight(i, 0)
            layout.setRowMinimumHeight(i, 0)
            layout.setRowSpacing(i, 0)
            layout.setRowStretchFactor(i, 1)

        for i in range(3):
            layout.setColumnPreferredWidth(i, 0)
            layout.setColumnMinimumWidth(i, 0)
            layout.setColumnSpacing(i, 0)
            layout.setColumnStretchFactor(i, 1)

        layout.setRowStretchFactor(1, 100)
        layout.setColumnStretchFactor(1, 100)

        self.setLayout(layout)

        self._initAxisItems()
        self.setTitle()

    def _initConnections(self) -> None:
        ...

    def _initAxisItems(self):
        ...

    @abstractmethod
    def clearData(self) -> None:
        raise NotImplementedError

    def addItem(self, item) -> None:
        """Add a graphics item to Canvas."""
        if item in self._items:
            warnings.warn(f"Item {item} already existed.")
            return

        self._items.add(item)
        self._canvas.addItem(item)

    def removeItem(self, item):
        """Add a graphics item to Canvas."""
        if item not in self._items:
            return

        self._items.remove(item)
        if item in self._plot_items:
            del self._plot_items[item]

        self._canvas.removeItem(item)

    def _removeAllItems(self):
        """Remove all graphics items from the Canvas."""
        for item in self._items:
            self._canvas.removeItem(item)

        self._plot_items.clear()
        self._items.clear()

    def showAxis(self, axis: str, visible: bool = True) -> None:
        """Show the given axis.

        :param axis: axis name.
        :param visible: axis visibility.
        """
        self._axes[axis].setVisible(visible)

    def setLabel(self, axis: str, text: Optional[str] = None) -> None:
        """Set the label for an axis.

        :param axis: axis name.
        :param text: text to display along the axis.
        """
        self._axes[axis].setLabel(text=text)
        self.showAxis(axis)

    def showLabel(self, axis: str, visible: bool = True) -> None:
        """Show or hide one of the axis labels.

        :param axis: axis name.
        :param visible: label visibility.
        """
        self._axes[axis].showLabel(visible)

    def setTitle(self, text: Optional[str] = None) -> None:
        if text is None:
            self._title.setMaximumHeight(0)
            self._layout.setRowFixedHeight(self._TITLE_LOC[0], 0)
            self._title.setVisible(False)
        else:
            self._title.setMaximumHeight(30)
            self._layout.setRowFixedHeight(self._TITLE_LOC[0], 30)
            self._title.setPlainText(text)
            self._title.setVisible(True)

    def invertX(self, inverted: bool = True) -> None:
        self._canvas.invertX(inverted)

    def invertY(self, inverted: bool = True) -> None:
        self._canvas.invertY(inverted)

    def close(self) -> None:
        """Override."""
        self._removeAllItems()
        super().close()


class PlotWidget(PlotWidgetBase):
    """2D plot widget for displaying graphs."""

    cross_toggled_sgn = pyqtSignal(bool)

    def __init__(self, *, parent: QGraphicsWidget = None):
        super().__init__(parent=parent)

        self._plot_items_y2 = OrderedDict()  # PlotItem: None
        self._canvas_y2 = None

        self._canvas.enableCrossCursor(True)
        self._cross_cursor = CrossCursorItem(parent=self._canvas)
        self._cross_cursor.setPen(FColor.mkPen("Magenta"))

        self._legend = None

        self._init()

    def _initConnections(self):
        """Override."""
        self._canvas.cross_cursor_toggled_sgn.connect(self.onCrossCursorToggled)
        self.onCrossCursorToggled(False)

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

    def clearData(self):
        """Override."""
        for item in chain(self._plot_items, self._plot_items_y2):
            item.clearData()

    def onCrossCursorToggled(self, state: bool):
        # scene is None at initialization
        scene = self.scene()
        if state:
            self._cross_cursor.show()
            scene.mouse_moved_sgn.connect(self.onCrossCursorMoved)
        else:
            self._cross_cursor.hide()
            if scene is not None:
                scene.mouse_moved_sgn.disconnect(self.onCrossCursorMoved)

    def onCrossCursorMoved(self, pos: QPointF):
        pos = self._canvas.mapFromScene(pos)
        self._cross_cursor.setPos(pos)
        v = self._canvas.mapToView(pos)
        self._cross_cursor.setLabel(v.x(), v.y())

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
        if item in self._items:
            warnings.warn(f"Item {item} already added to PlotItem.")
            return

        self._items.add(item)

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
                if self._axes['bottom'].log_scale:
                    item.setLogX(True)

                self._plot_items_y2[item] = None
            else:
                if self._axes['bottom'].log_scale:
                    item.setLogX(True)

                if self._axes['left'].log_scale:
                    item.setLogY(True)

                self._plot_items[item] = None

            if self._legend is not None:
                self._legend.addItem(item)

        canvas.addItem(item)

    def removeItem(self, item):
        """Override."""
        if item not in self._items:
            return

        self._items.remove(item)

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

    def _removeAllItems(self):
        """Override."""
        for item in self._items:
            if item in self._plot_items_y2:
                self._canvas_y2.removeItem(item)
            else:
                self._canvas.removeItem(item)

        if self._legend is not None:
            self._legend.removeAllItems()

        self._plot_items.clear()
        self._plot_items_y2.clear()
        self._items.clear()

    def addLegend(self, pos: Optional[QPointF] = None,
                  **kwargs):
        """Add a LegendWidget if it does not exist."""
        if self._legend is None:
            self._legend = LegendWidget(parent=self._canvas, **kwargs)

            for item in chain(self._plot_items, self._plot_items_y2):
                self._legend.addItem(item)

            if pos is None:
                # TODO: use a value which is proportional to the plot size
                pos = QPointF(20., 20.)
            self._legend.setPos(pos)

        return self._legend

    def showLegend(self, visible: bool = True) -> None:
        """Show or hide the legend.

        :param visible: whether to show the legend.
        """
        self._legend.setVisible(visible)
