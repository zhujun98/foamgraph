"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtWidgets import (
    QGraphicsItem, QGraphicsLinearLayout, QGraphicsGridLayout, QGraphicsTextItem
)

from ..aesthetics import FColor
from .graphics_item import GraphicsWidget


class AnnotationItem(GraphicsWidget):
    """Add annotation to a plot."""

    MAX_ITEMS = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations)

        self._items = []

    def setData(self, x, y, values):
        """Set a list of annotation items.

        :param list-like x: x coordinate of the annotated point.
        :param list-like y: y coordinate of the annotated point.
        :param list-like values: a list of annotation text.
        """
        if not len(x) == len(y) == len(values):
            raise ValueError("data have different lengths!")

        values = values[:self.MAX_ITEMS]
        n_pts = len(values)
        n_items = len(self._items)
        if n_items < n_pts:
            for i in range(n_pts - n_items):
                item = QGraphicsTextItem(parent=self)
                item.setDefaultTextColor(FColor.mkColor('b'))
                self._items.append(item)

        # n_vis = self._n_vis_annotation_items
        # if n_vis < n_pts:
        #     for i in range(n_vis, n_pts):
        #         a_items[i].show()
        # elif n_vis > n_pts:
        #     for i in range(n_pts, n_vis):
        #         a_items[i].hide()
        # self._n_vis_annotation_items = n_pts

        for i in range(n_pts):
            self._items[i].setPos(x[i], y[i])
            self._items[i].setPlainText(str(values[i]))
            self._items[i].show()
