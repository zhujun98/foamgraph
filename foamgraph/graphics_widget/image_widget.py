"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

from ..backend.QtCore import Qt

from ..graphics_item import ImageItem, RectROI
from .axis_widget import AxisWidget
from .image_colormap_editor import ImageColormapEditor
from .plot_widget import PlotWidgetBase


class ImageWidget(PlotWidgetBase):
    """2D plot widget for displaying an image."""

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._mouse_hover_v_rounding_decimals = 1

        self._image_item = ImageItem()
        self.addItem(self._image_item)

        self._rois = []

        self._cmap_editor = ImageColormapEditor(self._image_item)

        self._init()

    def _initUI(self):
        """Override."""
        super()._initUI()
        self._layout.addItem(self._cmap_editor, 1, 2)

    def _initConnections(self) -> None:
        """Override."""
        self._image_item.mouse_moved_sgn.connect(self.onMouseMoved)

    def imageItem(self):
        return self._image_item

    def addROI(self, roi: Optional[RectROI] = None) -> RectROI:
        if len(self._rois) == 4:
            raise RuntimeError("The maximum ROIs allowed is 4")

        colors = ['b', 'r', 'g', 'y']
        if roi is None:
            i = len(self._rois)
            roi = RectROI(pos=(5 + 15 * i, 5 + 15 * i),
                          size=(100, 100),
                          color=colors[i])
        self._rois.append(roi)
        self.addItem(roi)
        return roi

    def setImage(self, *args, **kwargs):
        self._image_item.setData(*args, **kwargs)

    def _initAxisItems(self):
        """Override."""
        for name, edge, pos in (
                ('bottom', Qt.Edge.BottomEdge, self._AXIS_BOTTOM_LOC),
                ('left', Qt.Edge.LeftEdge, self._AXIS_LEFT_LOC)
        ):
            axis = AxisWidget(edge, parent=self)

            self._axes[name] = axis
            self._layout.addItem(axis, *pos)
            axis.setFlag(axis.GraphicsItemFlag.ItemNegativeZStacksBehindParent)

        x_axis = self._axes['bottom']
        x_axis.linkToCanvas(self._canvas)
        x_axis.hide()

        y_axis = self._axes['left']
        y_axis.linkToCanvas(self._canvas)
        self._canvas.invertY()
        y_axis.hide()

    def onMouseMoved(self, x: int, y: int, v: float):
        if x < 0 or y < 0:
            self.setTitle("")
        else:
            self.setTitle(
                f'x={x}, y={y}, '
                f'value={round(v, self._mouse_hover_v_rounding_decimals)}')