"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..aesthetics import FColor
from ..backend.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from ..graph_view import GraphView
from ..graphics_item import DroppableItem


class SmartView(GraphView):
    """SmartView class.

    SmartView only accepts a single type of plot.
    """
    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)
        self.setAcceptDrops(True)

        self._data_items = {}
        self._plot_type = "curve"

    def _addPlot(self, *args, **kwargs):
        if self._plot_type == "curve":
            return self.addCurvePlot(*args, **kwargs)

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
