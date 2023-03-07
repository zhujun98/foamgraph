"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from ..backend.QtCore import QPointF, Qt
from ..backend.QtWidgets import QGraphicsGridLayout, QGraphicsItem

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

        self._image_item = image_item

        self._lut = None

        self._cbar = ColorbarWidget(parent=self)

        self._lri = LinearVRegionItem(0, 1)

        self._hist = CurvePlotItem(pen=FColor.mkPen('k'))
        self._hist.rotate(90)

        canvas = Canvas(draggable=False, scalable=False, parent=self)
        canvas.setMaximumWidth(152)
        canvas.setMinimumWidth(45)
        canvas.addItem(self._hist)
        canvas.addItem(self._lri)
        self._canvas = canvas

        self._axis = AxisWidget(Qt.Edge.LeftEdge, parent=self)
        self._axis.linkToCanvas(self._canvas)

        self.initUI()
        self.initConnections()

        # send function pointer, not the result
        image_item.setLookupTable(self.getLookupTable)

        # synchronize levels
        image_item.setLevels(self._lri.region())

    def initUI(self):
        layout = QGraphicsGridLayout()
        layout.setContentsMargins(*self.CONTENT_MARGIN)
        layout.setSpacing(0)
        layout.addItem(self._axis, 0, 0)
        layout.addItem(self._canvas, 0, 1)
        layout.addItem(self._cbar, 0, 2)
        self.setLayout(layout)

        self.setColorMap(config["COLOR_MAP"])

    def initConnections(self):
        self._lri.region_changed_sgn.connect(self.onRegionChanged)
        self._cbar.gradient_changed_sgn.connect(self.gradientChanged)

        self._image_item.image_changed_sgn.connect(self.onImageChanged)
        # If image_item._image is None, the following line does not initialize
        # image_item._levels
        self.onImageChanged(auto_levels=True)

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

    def onRegionChanged(self):
        self._image_item.setLevels(self._lri.region())
        self.update()

    def onImageChanged(self, auto_levels=False):
        hist, bin_centers = self._image_item.histogram()

        if hist is None:
            self._hist.clearData()
            return

        self._hist.setData(bin_centers, hist)

        if auto_levels:
            lower, upper = bin_centers[0], bin_centers[-1]
        else:
            # synchronize levels if ImageItem updated its image with
            # auto_levels = True
            lower, upper = self._image_item.levels()

        self._lri.setRegion(lower, upper)

    def setColorMap(self, name: str) -> None:
        self._cbar.setColorMap(ColorMap.fromName(name))
