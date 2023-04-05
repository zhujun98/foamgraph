"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from typing import final, Optional, Union

from ..backend.QtCore import Qt, QTimer

from ..graphics_item import (
    AnnotationItem, BarPlotItem, BarPlotItemManager, CandlestickPlotItem,
    SimpleCurvePlotItem, CurvePlotItem, ErrorbarPlotItem,
    ScatterPlotItem, ShadedPlotItem, StemPlotItem
)
from ..graphics_widget import GraphWidget
from .graphics_view import GraphicsView


class GraphViewBase(GraphicsView):

    def setXYLabels(self, x: str, y: str, *, y2: Optional[str] = None):
        self._cw.setLabel("bottom", x)
        self._cw.setLabel("left", y)
        if y2 is not None:
            self._cw.setLabel("right", y2)

    def addLegend(self, *args, **kwargs):
        self._cw.addLegend(*args, **kwargs)

    def showLegend(self, *args, **kwargs):
        self._cw.showLegend(*args, **kwargs)


class GraphView(GraphViewBase):
    """QGraphicsView for displaying graphs.

    This is normally used as a base class.
    """
    _central_widget_type = GraphWidget

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._bp_manager = BarPlotItemManager()

    def addCurvePlot(self, *args, simple=False, y2=False, **kwargs)\
            -> Union[CurvePlotItem, SimpleCurvePlotItem]:
        """Add and return a :class:`CurvePlotItem` or a :class:`SimpleCurvePlotItem`.

        :param simple: True for adding a :class:`SimpleCurvePlotItem`.
            Otherwise, a :class:`CurvePlotItem` is added.
        """
        if simple:
            item = SimpleCurvePlotItem(*args, **kwargs)
        else:
            item = CurvePlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addScatterPlot(self, *args, y2=False, **kwargs) -> ScatterPlotItem:
        """Add and return a :class:`ScatterPlotItem`."""
        item = ScatterPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def setBarPlotStackOrientation(self, orientation: str = 'v') -> None:
        """Set the stack orientation when there are multiple :class:`BarPlotItem`s.

        :param orientation: Stack orientation which can be either vertical
            ('v', 'vertical') or horizontal ('h', 'horizontal').
        """
        orientation = orientation.lower()
        if orientation in ['v', 'vertical']:
            self._bp_manager.setStackOrientation(Qt.Orientation.Vertical)
        elif orientation in ['h', 'horizontal']:
            self._bp_manager.setStackOrientation(Qt.Orientation.Horizontal)
        else:
            raise ValueError(f"Unknown orientation: {orientation}")

    def addBarPlot(self, *args, y2=False, **kwargs) -> BarPlotItem:
        """Add and return a :class:`BarPlotItem`.

        If there are more than one :class:`BarPlotItem`, they will stack
        vertically by default. To change the stacking orientation, see
        :meth:`GraphView.setBarPlotStackOrientation`.
        """
        item = BarPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        self._bp_manager.addItem(item)
        return item

    def addErrorbarPlot(self, *args, y2=False, **kwargs) -> ErrorbarPlotItem:
        """Add and return an :class:`ErrorbarPlotItem`."""
        item = ErrorbarPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addAnnotation(self, *args, y2=False, **kwargs) -> AnnotationItem:
        """Add and return an :class:`AnnotationItem`."""
        item = AnnotationItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addCandlestickPlot(self, *args, y2=False, **kwargs)\
            -> CandlestickPlotItem:
        """Add and return a :class:`CandlestickPlotItem`."""
        item = CandlestickPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addShadedPlot(self, *args, y2=False, **kwargs) -> ShadedPlotItem:
        """Add and return a :class:`ShadedPlotItem`."""
        item = ShadedPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def addStemPlot(self, *args, y2=False, **kwargs) -> StemPlotItem:
        """Add and return a :class:`StemPlotItem`."""
        item = StemPlotItem(*args, **kwargs)
        self._cw.addItem(item, y2=y2)
        return item

    def removeItem(self, item):
        """Override."""
        if isinstance(item, BarPlotItem):
            self._bp_manager.removeItem(item)
        super().removeItem(item)


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
