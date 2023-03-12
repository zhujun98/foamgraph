"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from ..backend.QtCore import QPointF, Qt
from ..backend.QtWidgets import QGraphicsGridLayout, QGraphicsItem, QMenu

from ..aesthetics import ColorMap, FColor
from ..config import config
from ..graphics_item import (
    CurvePlotItem, LinearVRegionItem
)
from .axis_widget import AxisWidget
from .canvas import Canvas
from .colorbar_widget import ColorbarWidget
from .graphics_widget import GraphicsWidget


class ImageColormapEditor(GraphicsWidget):
    """GraphicsWidget for adjusting the display of an image."""

    def __init__(self, image_item, *, parent=None):
        super().__init__(parent=parent)

        self._cbar = ColorbarWidget(parent=self)
        self._lut = None

        self._lri = LinearVRegionItem(0, 1)

        self._hist = CurvePlotItem(pen=FColor.mkPen('k'))
        self._hist.rotate(90)

        self._auto_levels = True

        self._image_item = image_item
        # send function pointer, not the result
        image_item.setLookupTable(self.getLookupTable)
        image_item.setLevels(self._lri.region())

        canvas = Canvas(auto_range_x_locked=True,
                        parent=self)
        canvas.setMaximumWidth(152)
        canvas.setMinimumWidth(45)
        canvas.addItem(self._hist)
        canvas.addItem(self._lri, ignore_bounds=True)
        self._canvas = canvas

        self._axis = AxisWidget(Qt.Edge.LeftEdge, parent=self)
        self._axis.linkToCanvas(self._canvas)

        self._auto_levels_action = None

        self.initUI()
        self.initConnections()

    def initUI(self):
        layout = QGraphicsGridLayout()
        layout.setContentsMargins(*self.CONTENT_MARGIN)
        layout.setSpacing(0)
        layout.addItem(self._axis, 0, 0)
        layout.addItem(self._canvas, 0, 1)
        layout.addItem(self._cbar, 0, 2)
        self.setLayout(layout)

        self.setColorMap(config["COLOR_MAP"])

        self._extendContextMenu()

    def initConnections(self):
        self._lri.region_changed_sgn.connect(self.onRegionChanged)
        self._lri.region_dragged_sgn.connect(
            lambda: self._auto_levels_action.setChecked(False))

        self._cbar.gradient_changed_sgn.connect(self.gradientChanged)

        self._image_item.image_changed_sgn.connect(self.onImageChanged)

    def _extendContextMenu(self):
        action = self._canvas.extendContextMenuAction("Auto Levels")
        action.setCheckable(True)
        action.toggled.connect(self._onAutoLevelsToggled)
        action.setChecked(True)
        self._auto_levels_action = action

    def gradientChanged(self):
        self._image_item.setLookupTable(self.getLookupTable)
        self._lut = None

    def getLookupTable(self, img=None, n=None):
        """Return the look-up table."""
        if self._lut is None:
            if n is None:
                n = 256 if img.dtype == np.uint8 else 512
            self._lut = self._cbar.getLookupTable(n)
        return self._lut

    def _onAutoLevelsToggled(self, state: bool) -> None:
        self._auto_levels = state

    def onRegionChanged(self):
        self._image_item.setLevels(self._lri.region())
        self.update()

    def onImageChanged(self):
        hist, bin_centers = self._image_item.histogram()

        if hist is None:
            self._hist.clearData()
            return

        self._hist.setData(bin_centers, hist)

        if self._auto_levels:
            lower, upper = bin_centers[0], bin_centers[-1]
        else:
            # synchronize levels if ImageItem updated its image with
            # auto_levels = True
            lower, upper = self._image_item.levels()

        self._lri.setRegion(lower, upper)

    def setColorMap(self, name: str) -> None:
        self._cbar.setColorMap(ColorMap.fromName(name))
