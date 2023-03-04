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
from .backend.QtWidgets import QSizePolicy, QWidget

from .graphics_item import (
    AnnotationItem, BarPlotItem, CurvePlotItem, ErrorbarPlotItem,
    PlotWidget, ScatterPlotItem
)
from .graphics_view import GraphicsView


class GraphView(GraphicsView):
    """QGraphicsView widget for displaying various graphs.

    This is normally used as a base class.
    """

    def __init__(self, parent=None, *, image: bool = False):
        """Initialization."""
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self._cw = PlotWidget(image=image)

        self.setCentralWidget(self._cw)

        if parent is not None and hasattr(parent, 'registerPlotWidget'):
            parent.registerPlotWidget(self)

    def reset(self):
        """Clear the data of all the items in the PlotWidget object."""
        self._cw.clearAllPlotItems()

    @abc.abstractmethod
    def updateF(self, data):
        """This method is called by the parent window."""
        raise NotImplementedError

    def close(self):
        self._cw.close()
        self._cw = None
        self.setParent(None)
        super().close()

    def addItem(self, *args, **kwargs):
        """Explicitly call PlotWidget.addItem.

        This method must be here to override the addItem method in
        GraphicsView. Otherwise, people may misuse the addItem method.
        """
        self._cw.addItem(*args, **kwargs)

    def removeItem(self, *args, **kwargs):
        self._cw.removeItem(*args, **kwargs)

    def addCurvePlot(self, *args, y2=False, **kwargs):
        """Add and return a :class:`CurvePlotItem`."""
        item = CurvePlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addScatterPlot(self, *args, y2=False, **kwargs):
        """Add and return a :class:`ScatterPlotItem`."""
        item = ScatterPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addBarPlot(self, *args, y2=False, **kwargs):
        """Add and return a :class:`BarPlotItem`."""
        item = BarPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addErrorbarPlot(self, *args, y2=False, **kwargs):
        """Add and return an :class:`ErrorbarPlotItem`."""
        item = ErrorbarPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addImage(self, *args, **kargs):
        """Add and return a image item."""
        # TODO: this will be done when another branch is merged
        raise NotImplementedError

    def addAnnotation(self, **kwargs):
        item = AnnotationItem(**kwargs)
        self._cw.addItem(item)
        return item

    def setLabel(self, *args, **kwargs):
        self._cw.setLabel(*args, **kwargs)

    def setXLabel(self, label: str):
        self._cw.setLabel("bottom", label)

    def setYLabel(self, label: str):
        self._cw.setLabel("left", label)

    def setXYLabels(self, x: str, y: str, *, y2: Optional[str] = None):
        self._cw.setLabel("bottom", x)
        self._cw.setLabel("left", y)
        if y2 is not None:
            self._cw.setLabel("right", y2)

    def setTitle(self, *args, **kwargs):
        self._cw.setTitle(*args, **kwargs)

    def setAnnotationList(self, *args, **kwargs):
        self._cw.setAnnotationList(*args, **kwargs)

    def addLegend(self, *args, **kwargs):
        self._cw.addLegend(*args, **kwargs)

    def invertX(self, *args, **kargs):
        self._cw.invertX(*args, **kargs)

    def invertY(self, *args, **kargs):
        self._cw.invertY(*args, **kargs)

    def hideAxis(self):
        """Hide x and y axis."""
        # FIXME: hide also y2?
        for v in ["left", 'bottom']:
            self._cw.hideAxis(v)

    def showAxis(self):
        """Show x and y axis."""
        # FIXME: hide also y2?
        for v in ["left", 'bottom']:
            self._cw.showAxis(v)

    def hideLegend(self):
        """Hide legend."""
        self._cw.showLegend(False)

    def showLegend(self):
        """Show legend."""
        self._cw.showLegend(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Override."""
        parent = self.parent()
        if parent is not None:
            parent.unregisterPlotWidget(self)
        super().closeEvent(event)


class TimedGraphView(GraphView):

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


class HistWidgetF(GraphView):
    """Base class for a histogram plot widget."""

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._plot = self.addBarPlot()

        self._title_template = Template(
            f"mean: $mean, median: $median, std: $std")
        self.updateTitle()

    def updateTitle(self, mean=np.nan, median=np.nan, std=np.nan):
        self.setTitle(self._title_template.substitute(
            mean=f"{mean:.2e}", median=f"{median:.2e}", std=f"{std:.2e}"))

    def reset(self):
        super().reset()
        self.updateTitle()
