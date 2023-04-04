"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

from ..aesthetics import FColor
from ..backend.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from ..graphics_item import CurvePlotItem, DroppableItem
from ..graphics_widget import SmartGraphWidget
from .graphics_view import GraphicsView


class SmartView(GraphicsView):
    """SmartView class.

    SmartView only accepts a single type of plot.
    """
    _central_widget_type = SmartGraphWidget

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)
        self.setAcceptDrops(True)

        self._data_items = {}
        self._plot_type = "curve"

    def _addPlot(self, *args, **kwargs):
        if self._plot_type == "curve":
            item = CurvePlotItem(*args, **kwargs)
            self._cw.addItem(item)
            return item

    def addDataItem(self, item: DroppableItem) -> None:
        if item not in self._data_items:
            name = item.name()
            if not name:
                name = f"Data{len(self._data_items)}"
            plot = self._addPlot(label=name,
                                 pen=FColor.mkPen(item.pen().color()),
                                 brush=FColor.mkBrush(item.brush().color()))
            self._data_items[item] = plot
            if len(self._data_items) > 1:
                self.addLegend()

    def updateF(self, data):
        """override."""
        for item, plot in self._data_items.items():
            data_item = item.extract(data['image']['data'])
            if data_item is None:
                plot.clearData()
            else:
                plot.setData(*data_item.get())

    def dragEnterEvent(self, ev: QDragEnterEvent) -> None:
        """Override."""
        ev.acceptProposedAction()

    def dragMoveEvent(self, ev: QDragMoveEvent) -> None:
        """Override."""
        ev.acceptProposedAction()

    def dropEvent(self, ev: QDropEvent) -> None:
        """Override."""
        item = ev.source()
        if not isinstance(item, DroppableItem):
            return
        self.addDataItem(item)
        ev.acceptProposedAction()

    def setXYLabels(self, x: str, y: str, *, y2: Optional[str] = None):
        self._cw.setLabel("bottom", x)
        self._cw.setLabel("left", y)
        if y2 is not None:
            self._cw.setLabel("right", y2)

    def addLegend(self, *args, **kwargs):
        self._cw.addLegend(*args, **kwargs)

    def showLegend(self, *args, **kwargs):
        self._cw.showLegend(*args, **kwargs)
