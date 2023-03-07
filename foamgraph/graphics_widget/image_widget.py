"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

import numpy as np

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
        self._image_item.mouse_moved_sgn.connect(self.onMouseMoved)
        self.addItem(self._image_item)

        self._cmap_editor = ImageColormapEditor(self._image_item)
        self._layout.addItem(self._cmap_editor, 1, 2)

        self._rois = []

        self._init()

    def imageItem(self):
        return self._image_item

    def addROI(self, roi: Optional[RectROI] = None):
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

    def setImage(self, img, *, auto_levels=False, scale=None, pos=None):
        """Set the displayed image.

        :param np.ndarray img: the image to be displayed.
        :param bool auto_levels: whether to update the white/black levels
            to fit the image. default = False
        :param tuple/list pos: the origin of the displayed image in (x, y).
        :param tuple/list scale: the origin of the displayed image image in
            (x_scale, y_scale).
        """
        if img is None:
            self.clearData()
            return

        if not isinstance(img, np.ndarray):
            raise TypeError("Image data must be a numpy array!")

        self._image_item.setImage(img, auto_levels=auto_levels)
        self._image_item.resetTransform()

        if scale is not None:
            self._image_item.scale(*scale)
        if pos is not None:
            self._image_item.setPos(*pos)

    def clearData(self) -> None:
        """Override."""
        # FIXME: there is a bug in ImageItem.setImage if the input is None
        self._image_item.clear()

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
