"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from typing import final, Optional

from ..backend.QtCore import QTimer

from ..graphics_item import (
    AnnotationItem, BarPlotItem, CurvePlotItem, ErrorbarPlotItem,
    ScatterPlotItem
)
from ..graphics_widget import PlotWidget
from .graphics_view import GraphicsView


class GraphView(GraphicsView):
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

    def clearData(self):
        self._cw.clearData()

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
