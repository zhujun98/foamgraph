"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from collections.abc import Callable

import numpy as np

from ..backend.QtGui import (
    QGraphicsSceneMouseEvent, QPainter, QPicture, QTransform
)
from ..backend.QtCore import pyqtSignal, pyqtSlot, QPointF, QRectF, Qt

from ..pyqtgraph_be import Point
from ..pyqtgraph_be import functions as fn

from ..algorithm import quick_min_max
from ..graphics_scene import HoverEvent
from .graphics_item import GraphicsObject


class ImageItem(GraphicsObject):
    """GraphicsObject displaying a 2D image."""

    image_changed_sgn = pyqtSignal()

    mouse_moved_sgn = pyqtSignal(int, int, float)  # (x, y, value)

    def __init__(self, image=None, *, parent=None):
        super().__init__(parent=parent)

        self._image = None   # original image data
        self._qimage = None  # rendered image for display

        self._levels = [0, 1]  # [min, max]
        self._auto_level_quantile = 0.99
        self._lut = None
        self._ds_rate = (1., 1.)  # down-sample rates

        # In some cases, a modified lookup table is used to handle both
        # rescaling and LUT more efficiently
        self._fast_lut = None

        self.setImage(image, auto_levels=True)

    def width(self):
        if self._image is None:
            return None
        return self._image.shape[1]

    def height(self):
        if self._image is None:
            return None
        return self._image.shape[0]

    def setLevels(self, levels):
        """Set image colormap scaling levels.

        :param tuple levels: (min, max).
        """
        if self._levels != levels:
            self._levels = levels
            self._fast_lut = None
            self.setImage(auto_levels=False)

    def levels(self) -> tuple:
        return self._levels

    def setLookupTable(self, lut, update=True) -> None:
        if lut is not self._lut:
            self._lut = lut
            self._fast_lut = None
            if update:
                self.setImage(auto_levels=False)

    def clear(self):
        self._image = None
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.update()

    def setImage(self, image=None, auto_levels=False):
        image_changed = False
        if image is None:
            if self._image is None:
                return
        else:
            image_changed = True
            shape_changed = \
                self._image is None or image.shape != self._image.shape

            image = image.view(np.ndarray)

            if self._image is None or image.dtype != self._image.dtype:
                self._fast_lut = None

            self._image = image

            if shape_changed:
                self.prepareGeometryChange()
                self.informViewBoundsChanged()

        if auto_levels:
            self._levels = quick_min_max(
                self._image, q=self._auto_level_quantile)

        self._qimage = None
        self.update()

        if image_changed:
            self.image_changed_sgn.emit()

    def render(self):
        """Convert data to QImage for displaying."""
        if self._image is None or self._image.size == 0:
            return

        # Request a lookup table
        if isinstance(self._lut, Callable):
            lut = self._lut(self._image)
        else:
            lut = self._lut

        # Downsample

        # reduce dimensions of image based on screen resolution
        o = self.mapToDevice(QPointF(0, 0))
        x = self.mapToDevice(QPointF(1, 0))
        y = self.mapToDevice(QPointF(0, 1))

        # Check if graphics view is too small to render anything
        if o is None or x is None or y is None:
            return

        w = Point(x-o).length()
        h = Point(y-o).length()
        if w == 0 or h == 0:
            self._qimage = None
            return

        xds = max(1, int(1.0 / w))
        yds = max(1, int(1.0 / h))
        # TODO: replace fn.downsample
        image = fn.downsample(self._image, xds, axis=1)
        image = fn.downsample(image, yds, axis=0)
        self._ds_rate = (xds, yds)

        # Check if downsampling reduced the image size to zero due to inf values.
        if image.size == 0:
            return

        # if the image data is a small int, then we can combine levels + lut
        # into a single lut for better performance
        levels = self._levels
        if levels is not None and image.dtype in (np.ubyte, np.uint16):
            if self._fast_lut is None:
                eflsize = 2**(image.itemsize*8)
                ind = np.arange(eflsize)
                minlev, maxlev = levels
                levdiff = maxlev - minlev
                # avoid division by 0
                levdiff = 1 if levdiff == 0 else levdiff
                if lut is None:
                    efflut = fn.rescaleData(
                        ind, scale=255./levdiff, offset=minlev, dtype=np.ubyte)
                else:
                    lutdtype = np.min_scalar_type(lut.shape[0]-1)
                    efflut = fn.rescaleData(
                        ind, scale=(lut.shape[0]-1)/levdiff,
                        offset=minlev, dtype=lutdtype, clip=(0, lut.shape[0]-1))
                    efflut = lut[efflut]

                self._fast_lut = efflut
            lut = self._fast_lut
            levels = None

        # TODO: replace fn.makeARGB and fn.makeQImage
        argb, alpha = fn.makeARGB(image, lut=lut, levels=levels)
        self._qimage = fn.makeQImage(argb, alpha, transpose=False)

    def paint(self, p, *args) -> None:
        """Override."""
        if self._image is None:
            return

        if self._qimage is None:
            self.render()
            if self._qimage is None:
                return

        p.drawImage(QRectF(0, 0, *self._image.shape[::-1]), self._qimage)

    def histogram(self):
        """Return estimated histogram of image pixels.

        :returns: (hist, bin_centers)
        """
        if self._image is None or self._image.size == 0:
            return None, None

        step = (max(1, int(np.ceil(self._image.shape[0] / 200))),
                max(1, int(np.ceil(self._image.shape[1] / 200))))

        sliced_data = self._image[::step[0], ::step[1]]

        lb, ub = np.nanmin(sliced_data), np.nanmax(sliced_data)

        if np.isnan(lb) or np.isnan(ub):
            # the data are all-nan
            return None, None

        if lb == ub:
            # degenerate image, arange will fail
            lb -= 0.5
            ub += 0.5

        n_bins = 500
        if sliced_data.dtype.kind in "ui":
            # step >= 1
            step = np.ceil((ub - lb) / n_bins)
            # len(bins) >= 2
            bins = np.arange(lb, ub + 0.01 * step, step, dtype=int)
        else:
            # for float data, let numpy select the bins.
            bins = np.linspace(lb, ub, n_bins)

        hist, bin_edges = np.histogram(sliced_data, bins=bins)

        return hist, (bin_edges[:-1] + bin_edges[1:]) / 2.

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._image is None:
            return QRectF(0., 0., 0., 0.)
        return QRectF(0., 0., float(self.width()), float(self.height()))

    def hoverEvent(self, ev: HoverEvent) -> None:
        if ev.isExit():
            x = -1  # out of image
            y = -1  # out of image
            value = 0.0
        else:
            pos = ev.pos()
            x = int(pos.x())
            y = int(pos.y())
            value = self._image[y, x]

        self.mouse_moved_sgn.emit(x, y, value)
