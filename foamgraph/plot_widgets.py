"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from string import Template
from typing import final, Optional

import numpy as np

from .backend.QtCore import pyqtSlot, QTimer
from .backend.QtGui import QCloseEvent
from .backend.QtWidgets import QSizePolicy

from . import pyqtgraph_be as pg

from .plot_area import PlotArea
from .line_items import InfiniteHorizontalLineItem, InfiniteVerticalLineItem
from .plot_items import (
    BarGraphItem, CurvePlotItem, ScatterPlotItem, ErrorbarItem
)
from .signal_proxy import SignalProxy


class PlotWidgetF(pg.GraphicsView):
    """PlotWidget base class.

    GraphicsView widget displaying PlotItems.

    This base class should be used to display plots except images.
    For displaying images, please refer to ImageViewF class.
    """

    def __init__(self, parent=None, *,
                 background='default',
                 enable_meter=True,
                 enable_grid=True,
                 enable_transform=True):
        """Initialization."""
        super().__init__(parent, background=background)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.enableMouse(False)

        self._title = ""

        self._plot_area = PlotArea(enable_meter=enable_meter,
                                   enable_grid=enable_grid,
                                   enable_transform=enable_transform)
        self.setCentralWidget(self._plot_area)
        self._plot_area.cross_toggled_sgn.connect(self.onCrossToggled)

        self._v_line = None
        self._h_line = None
        if enable_meter:
            self._v_line = InfiniteVerticalLineItem(0., draggable=False)
            self._h_line = InfiniteHorizontalLineItem(0., draggable=False)
            self._v_line.hide()
            self._h_line.hide()
            self._plot_area.addItem(self._v_line, ignore_bounds=True)
            self._plot_area.addItem(self._h_line, ignore_bounds=True)
            # rateLimit should be fast enough to be able to capture
            # the leaveEvent
            self._proxy = SignalProxy(self._plot_area.scene().mouse_moved_sgn,
                                      rateLimit=60, slot=self.onMouseMoved)

        if parent is not None and hasattr(parent, 'registerPlotWidget'):
            parent.registerPlotWidget(self)

    def reset(self):
        """Clear the data of all the items in the PlotArea object."""
        self._plot_area.clearAllPlotItems()

    @abc.abstractmethod
    def updateF(self, data):
        """This method is called by the parent window."""
        raise NotImplementedError

    def close(self):
        self._plot_area.close()
        self._plot_area = None
        self.setParent(None)
        super().close()

    def addItem(self, *args, **kwargs):
        """Explicitly call PlotArea.addItem.

        This method must be here to override the addItem method in
        GraphicsView. Otherwise, people may misuse the addItem method.
        """
        self._plot_area.addItem(*args, **kwargs)

    def removeItem(self, *args, **kwargs):
        self._plot_area.removeItem(*args, **kwargs)

    def removeAllItems(self):
        """Remove all the items in the PlotArea object."""
        self._plot_area.removeAllItems()

    def plotCurve(self, *args, y2=False, **kwargs):
        """Add and return a new curve plot."""
        item = CurvePlotItem(*args, **kwargs)
        self._plot_area.addItem(item, y2=y2)
        return item

    def plotScatter(self, *args, y2=False, **kwargs):
        """Add and return a new scatter plot."""
        item = ScatterPlotItem(*args, **kwargs)
        self._plot_area.addItem(item, y2=y2)
        return item

    def plotBar(self, *args, y2=False, **kwargs):
        """Add and return a new bar plot."""
        item = BarGraphItem(*args, **kwargs)
        self._plot_area.addItem(item, y2=y2)
        return item

    def plotErrorbar(self, *args, y2=False, **kwargs):
        item = ErrorbarItem(*args, **kwargs)
        self._plot_area.addItem(item, y2=y2)
        return item

    def plotImage(self, *args, **kargs):
        """Add and return a image item."""
        # TODO: this will be done when another branch is merged
        raise NotImplementedError

    def setAspectLocked(self, *args, **kwargs):
        self._plot_area.setAspectLocked(*args, **kwargs)

    def setLabel(self, *args, **kwargs):
        self._plot_area.setLabel(*args, **kwargs)

    def setXLabel(self, label: str):
        self._plot_area.setLabel("bottom", label)

    def setYLabel(self, label: str):
        self._plot_area.setLabel("left", label)

    def setXYLabels(self, x: str, y: str, *, y2: Optional[str] = None):
        self._plot_area.setLabel("bottom", x)
        self._plot_area.setLabel("left", y)
        if y2 is not None:
            self._plot_area.setLabel("right", y2)

    def setTitle(self, *args, **kwargs):
        self._plot_area.setTitle(*args, **kwargs)

    def setAnnotationList(self, *args, **kwargs):
        self._plot_area.setAnnotationList(*args, **kwargs)

    def addLegend(self, *args, **kwargs):
        self._plot_area.addLegend(*args, **kwargs)

    def invertX(self, *args, **kargs):
        self._plot_area.invertX(*args, **kargs)

    def invertY(self, *args, **kargs):
        self._plot_area.invertY(*args, **kargs)

    def autoRange(self, *args, **kwargs):
        self._plot_area.autoRange(*args, **kwargs)

    def hideAxis(self):
        """Hide x and y axis."""
        # FIXME: hide also y2?
        for v in ["left", 'bottom']:
            self._plot_area.showAxis(v, False)

    def showAxis(self):
        """Show x and y axis."""
        # FIXME: hide also y2?
        for v in ["left", 'bottom']:
            self._plot_area.showAxis(v, True)

    def hideLegend(self):
        """Hide legend."""
        self._plot_area.showLegend(False)

    def showLegend(self):
        """Show legend."""
        self._plot_area.showLegend(True)

    @pyqtSlot(bool)
    def onCrossToggled(self, state):
        if state:
            self._v_line.show()
            self._h_line.show()
        else:
            self._v_line.hide()
            self._h_line.hide()

    def onMouseMoved(self, pos):
        m_pos = self._plot_area.mapSceneToView(pos[0])
        x, y = m_pos.x(), m_pos.y()
        self._v_line.setValue(x)
        self._h_line.setValue(y)
        self._plot_area.setMeter((x, y))

    def closeEvent(self, event: QCloseEvent) -> None:
        """Override."""
        parent = self.parent()
        if parent is not None:
            parent.unregisterPlotWidget(self)
        super().closeEvent(event)


class TimedPlotWidgetF(PlotWidgetF):

    def __init__(self, interval: int = 1000, *args, **kwargs):
        """Initialization.

        :param interval: Plot updating interval in milliseconds.
        """
        super().__init__(*args, **kwargs)

        self._data = None

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_imp)
        self._timer.start(interval)

    @abc.abstractmethod
    def refresh(self):
        pass

    def _refresh_imp(self):
        if self._data is not None:
            self.refresh()

    @final
    def updateF(self, data):
        """Override."""
        self._data = data


class HistWidgetF(PlotWidgetF):
    """Base class for a histogram plot widget."""

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._plot = self.plotBar()

        self._title_template = Template(
            f"mean: $mean, median: $median, std: $std")
        self.updateTitle()

    def updateTitle(self, mean=np.nan, median=np.nan, std=np.nan):
        self.setTitle(self._title_template.substitute(
            mean=f"{mean:.2e}", median=f"{median:.2e}", std=f"{std:.2e}"))

    def reset(self):
        super().reset()
        self.updateTitle()
