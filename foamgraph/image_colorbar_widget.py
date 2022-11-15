"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from .backend.QtGui import QPainter
from .backend.QtCore import pyqtSignal, Qt
from .backend.QtWidgets import QGraphicsGridLayout

from . import pyqtgraph_be as pg
from .pyqtgraph_be import Point

from .gradient_editor_widget import GradientEditorWidget
from .linear_region_item import LinearRegionItem
from .plot_items import CurvePlotItem
from .aesthetics import ColorMap, FColor


class ImageColorbarWidget(pg.GraphicsWidget):
    """GraphicsWidget for adjusting the display of an image."""

    lut_changed_sgn = pyqtSignal(object)

    def __init__(self, image_item, *, parent=None):
        super().__init__(parent=parent)
        self._lut = None

        self._gradient = GradientEditorWidget()
        self._gradient.show()

        self._lri = LinearRegionItem(
            (0, 1), orientation=Qt.Orientation.Horizontal)
        self._lri.setZValue(1000)

        self._pen = FColor.mkPen("Gray", alpha=100)
        self._lri.setLinePen(FColor.mkPen("Gray"))
        self._lri.setLineHoverPen(FColor.mkPen("Gray", alpha=50))

        self._hist = CurvePlotItem(pen=FColor.mkPen('k'))
        self._hist.rotate(90)

        vb = pg.ViewBox(parent=self)
        vb.setMaximumWidth(152)
        vb.setMinimumWidth(45)
        vb.setMouseEnabled(x=False, y=True)
        vb.addItem(self._hist)
        vb.addItem(self._lri)
        vb.enableAutoRange(pg.ViewBox.XYAxes)
        self._vb = vb

        self._axis = pg.AxisItem(
            'left', linkView=self._vb, maxTickLength=-10, parent=self)

        self.initUI()
        self.initConnections()

        image_item.image_changed_sgn.connect(self.onImageChanged)
        # send function pointer, not the result
        image_item.setLookupTable(self.getLookupTable)
        self._image_item = image_item
        # If image_item._image is None, the following line does not initialize
        # image_item._levels
        self.onImageChanged(auto_levels=True)
        # synchronize levels
        image_item.setLevels(self.levels())

    def initUI(self):
        layout = QGraphicsGridLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addItem(self._axis, 0, 0)
        layout.addItem(self._vb, 0, 1)
        layout.addItem(self._gradient, 0, 2)
        self.setLayout(layout)

    def initConnections(self):
        self._lri.region_changed_sgn.connect(self.regionChanging)
        self._lri.region_change_finished_sgn.connect(self.regionChanged)

        self._gradient.gradient_changed_sgn.connect(self.gradientChanged)

        self._vb.sigRangeChanged.connect(self.update)

    def paint(self, p, *args) -> None:
        """Override."""
        levels = self.levels()
        p1 = self._vb.mapFromViewToItem(
            self, Point(self._vb.viewRect().center().x(), levels[0]))
        p2 = self._vb.mapFromViewToItem(
            self, Point(self._vb.viewRect().center().x(), levels[1]))
        rect = self._gradient.mapRectToParent(
            self._gradient.gradientItem().rect())

        p.setPen(self._pen)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.drawLine(p1, rect.bottomLeft())
        p.drawLine(p2, rect.topLeft())

    def gradientChanged(self):
        self._image_item.setLookupTable(self.getLookupTable)
        self._lut = None
        self.lut_changed_sgn.emit(self)

    def getLookupTable(self, img=None, n=None):
        """Return the look-up table."""
        if self._lut is None:
            if n is None:
                n = 256 if img.dtype == np.uint8 else 512
            self._lut = self._gradient.getLookupTable(n)
        return self._lut

    def regionChanging(self):
        """One line of the region is being dragged."""
        self._image_item.setLevels(self.levels())
        self.update()

    def regionChanged(self):
        """Line dragging has finished."""
        self._image_item.setLevels(self.levels())

    def onImageChanged(self, auto_levels=False):
        hist, bin_centers = self._image_item.histogram()

        if hist is None:
            self._hist.setData([], [])
            return

        self._hist.setData(bin_centers, hist)
        if auto_levels:
            self._lri.setRegion((bin_centers[0], bin_centers[-1]))
        else:
            # synchronize levels if ImageItem updated its image with
            # auto_levels = True
            self._lri.setRegion(self._image_item.levels())

    def setColorMap(self, cm: ColorMap) -> None:
        self._gradient.setColorMap(cm)

    def levels(self) -> tuple:
        return self._lri.region()

    def setLevels(self, levels: tuple) -> None:
        self._lri.setRegion(levels)
