"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtCore import QPointF, Qt
from ..backend.QtWidgets import QGraphicsGridLayout, QGraphicsItem, QMenu

from ..aesthetics import FColor
from ..config import config
from ..graphics_item import (
    SimpleCurvePlotItem, ImageItem, LinearVRegionItem
)
from .axis_widget import AxisWidget
from .canvas import Canvas
from .colorbar_widget import ColorbarWidget
from .graphics_widget import GraphicsWidget


class ColormapController(GraphicsWidget):
    """GraphicsWidget for adjust the colormap and colorscale of an image."""

    def __init__(self, image_item: ImageItem, *, parent=None):
        super().__init__(parent=parent)

        self._image_item = image_item
        self._cbar = ColorbarWidget(parent=self)
        self._lri = LinearVRegionItem(0, 1)
        self._hist = SimpleCurvePlotItem(pen=FColor.mkPen('k'))

        self._auto_levels = True

        canvas = Canvas(auto_range_x_locked=True, parent=self)
        canvas.setMaximumWidth(152)
        canvas.setMinimumWidth(45)
        canvas.addItem(self._hist)
        canvas.addItem(self._lri, ignore_bounds=True)
        canvas.invertX(True)
        self._canvas = canvas

        self._axis = AxisWidget(Qt.Edge.LeftEdge, parent=self)
        self._axis.linkToCanvas(self._canvas)
        self._axis.log_Scale_toggled_sgn.connect(self._onLogScaleToggled)

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

        self._extendContextMenu()

    def initConnections(self):
        self._lri.region_changed_sgn.connect(self.onRegionChanged)
        self._lri.region_dragged_sgn.connect(
            lambda: self._auto_levels_action.setChecked(False))

        self._cbar.colormap_changed_sgn.connect(self.onColorMapChanged)

        self._image_item.image_changed_sgn.connect(self.onImageChanged)

        self._image_item.setLevels(self._lri.region())
        self.setColorMap(config["COLOR_MAP"])

    def _extendContextMenu(self):
        action = self._canvas.extendContextMenuAction("Auto Levels")
        action.setCheckable(True)
        action.toggled.connect(self._onAutoLevelsToggled)
        action.setChecked(True)
        self._auto_levels_action = action

    def _onAutoLevelsToggled(self, state: bool) -> None:
        self._auto_levels = state

    def _onLogScaleToggled(self, state: bool) -> None:
        self._hist.setLogY(state)
        self._canvas.updateAutoRange()

    def onColorMapChanged(self):
        self._image_item.setColorMap(self._cbar.colorMap())

    def onRegionChanged(self):
        self._image_item.setLevels(self._lri.region())
        self.update()

    def onImageChanged(self):
        hist, bin_centers = self._image_item.histogram()

        if hist is None:
            self._hist.clearData()
            return

        # we need a normal curve plot rotated by 90 degrees
        self._hist.setData(hist, bin_centers)

        if self._auto_levels:
            lower, upper = bin_centers[0], bin_centers[-1]
        else:
            # synchronize levels if ImageItem updated its image with
            # auto_levels = True
            lower, upper = self._image_item.levels()

        self._lri.setRegion(lower, upper)

    def setColorMap(self, name: str) -> None:
        self._cbar.setColorMap(name)
