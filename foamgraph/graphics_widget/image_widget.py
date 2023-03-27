"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

from ..backend.QtCore import QPointF, Qt

from ..aesthetics import FColor
from ..graphics_item import (
    EllipseROI, ImageItem, MouseCursorStyle, RectROI, ROIBase, RectROI
)
from .axis_widget import AxisWidget
from .colormap_controller import ColormapController
from .plot_widget import PlotWidget


class ImageWidget(PlotWidget):
    """PlotWidget for displaying an image.

    It contains a :class:`Canvas`, a :class:`ColormapController`, a
    :class"`LabelWidget` for displaying the title and a
    :class:`MouseCursorItem`.
    """

    ROI_COLORS = ['b', 'r', 'g', 'y']

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._image_item = ImageItem()
        self.addItem(self._image_item)

        self._rois = []

        self._cmap_controller = ColormapController(self._image_item)

        self._initUI()
        self._initConnections()

    def _initUI(self) -> None:
        """Override."""
        super()._initUI()
        self._layout.addItem(self._cmap_controller, 1, 2)
        self.setAspectLocked(True)

    def _initConnections(self) -> None:
        """Override."""
        super()._initConnections()
        self._canvas.setMouseMode(self._canvas.MouseMode.Off)
        self._setMouseCursorStyle(MouseCursorStyle.Simple)
        self._canvas.getMenuAction("Cursor_Show").setChecked(False)

    def _extendCanvasContextMenu(self):
        """Override."""
        super()._extendCanvasContextMenu()

        menu = self._canvas.extendContextMenu("ROI")
        menu.setObjectName("ROI")

        # action = menu.addAction("Show")
        # action.setObjectName("Cursor_Show")
        # action.setCheckable(True)
        # action.toggled.connect(self._onMouseCursorToggled)

    def imageItem(self):
        return self._image_item

    def _addROI(self, roi_type, *args, **kwargs) -> ROIBase:
        if len(self._rois) == len(self.ROI_COLORS):
            raise RuntimeError("The maximum ROIs allowed is 4")

        roi = roi_type(*args, **kwargs)
        roi.setPen(FColor.mkPen(
            self.ROI_COLORS[len(self._rois)], width=2))
        self._rois.append(roi)
        self._canvas.addItem(roi, ignore_bounds=True)

        menu = self._canvas.getMenu("ROI")
        action = menu.addAction(roi.label())
        action.setCheckable(True)
        action.toggled.connect(lambda x: roi.setVisible(x))

        roi.hide()
        return roi

    def addRectROI(self, *args, **kwargs) -> RectROI:
        return self._addROI(RectROI, *args, **kwargs)

    def addEllipseROI(self, *args, **kwargs) -> EllipseROI:
        return self._addROI(EllipseROI, *args, **kwargs)

    def setImage(self, *args, **kwargs):
        self._image_item.setData(*args, **kwargs)

    def setColorMap(self, *args, **kwargs):
        self._cmap_controller.setColorMap(*args, **kwargs)

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
            self._mouse_cursor.setLabel("")

    def _updateMouseCursorLabel(self) -> None:
        """Override."""
        # image size could change
        ...

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
