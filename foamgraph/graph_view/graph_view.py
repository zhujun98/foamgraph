"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from typing import final, Optional

from ..backend.QtCore import QTimer
from ..backend.QtGui import QCloseEvent
from ..backend.QtWidgets import QSizePolicy

from ..graphics_item import (
    AnnotationItem, BarPlotItem, CurvePlotItem, ErrorbarPlotItem,
    ScatterPlotItem
)
from ..graphics_view import GraphicsView
from ..graphics_widget import PlotWidget


class GraphViewBase(GraphicsView):
    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        if parent is not None and hasattr(parent, 'registerPlotWidget'):
            parent.registerPlotWidget(self)

    def clearData(self):
        self._cw.clearData()

    def addItem(self, *args, **kwargs):
        self._cw.addItem(*args, **kwargs)

    def removeItem(self, *args, **kwargs):
        self._cw.removeItem(*args, **kwargs)

    def setTitle(self, *args, **kwargs):
        self._cw.setTitle(*args, **kwargs)

    def showXAxis(self, *args, **kwargs):
        self._cw.showAxis('bottom', *args, **kwargs)

    def showYAxis(self, *args, **kwargs):
        self._cw.showAxis('left', *args, **kwargs)

    def setXLabel(self, *args, **kwargs):
        self._cw.setLabel("bottom", *args, **kwargs)

    def setYLabel(self, *args, **kwargs):
        self._cw.setLabel("left", *args, **kwargs)

    @abc.abstractmethod
    def updateF(self, data):
        """This method is called by the parent window."""
        raise NotImplementedError

    def close(self) -> None:
        """Override."""
        self._cw.close()
        self.setParent(None)
        super().close()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Override."""
        parent = self.parent()
        if parent is not None:
            parent.unregisterPlotWidget(self)
        super().closeEvent(event)


class GraphView(GraphViewBase):
    """QGraphicsView for displaying graphs.

    This is normally used as a base class.
    """
    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self._cw = PlotWidget()
        self.setCentralWidget(self._cw)

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

    def addAnnotation(self):
        item = AnnotationItem()
        self._cw.addItem(item)
        return item

    def setXYLabels(self, x: str, y: str, *, y2: Optional[str] = None):
        self._cw.setLabel("bottom", x)
        self._cw.setLabel("left", y)
        if y2 is not None:
            self._cw.setLabel("right", y2)

    def addLegend(self, *args, **kwargs):
        self._cw.addLegend(*args, **kwargs)

    def showLegend(self, *args, **kwargs):
        self._cw.showLegend(*args, **kwargs)


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
        raise NotImplementedError

    def _refresh_imp(self):
        if self._data is not None:
            self.refresh()

    @final
    def updateF(self, data):
        """Override."""
        self._data = data
