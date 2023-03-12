"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

from ..backend.QtCore import QPointF, Qt

from ..graphics_item import ImageItem, RectROI, MouseCursorStyle
from .axis_widget import AxisWidget
from .image_colormap_editor import ImageColormapEditor
from .plot_widget import PlotWidget


class ImageWidget(PlotWidget):
    """PlotWidget for displaying an image."""

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._image_item = ImageItem()
        self.addItem(self._image_item)

        self._rois = []

        self._cmap_editor = ImageColormapEditor(self._image_item)

        self._initUI()
        self._initConnections()

    def _initUI(self) -> None:
        """Override."""
        super()._initUI()
        self._layout.addItem(self._cmap_editor, 1, 2)

    def _initConnections(self) -> None:
        """Override."""
        super()._initConnections()
        self._canvas.setMouseMode(self._canvas.MouseMode.Off)
        self._setMouseCursorStyle(MouseCursorStyle.Simple)
        self._mouse_cursor_enable_action.setChecked(False)

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

    def clearData(self) -> None:
        """Override."""
        self._image_item.setData(None)

    def _onMouseCursorMoved(self, pos: QPointF) -> None:
        """Override."""
        super()._onMouseCursorMoved(pos)
        x, y = int(pos.x()), int(pos.y())
        if self._image_item.boundingRect().contains(pos):
            v = self._image_item.dataAt(x, y)
            self._mouse_cursor.setLabel(f"    {x}, {y}, {v:.1f}")
        else:
            self._mouse_cursor.setLabel(f"    {x}, {y}")

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
