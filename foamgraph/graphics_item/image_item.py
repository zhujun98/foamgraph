"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections.abc import Callable
from typing import Optional

import numpy as np

from ..backend.QtCore import pyqtSignal, pyqtSlot, QPointF, QRectF, Qt

from ..pyqtgraph_be import Point
from ..pyqtgraph_be import functions as fn

from ..algorithm import quick_min_max
from .graphics_item import GraphicsObject


class ImageItem(GraphicsObject):
    """GraphicsObject displaying a 2D image."""

    image_changed_sgn = pyqtSignal()

    def __init__(self, image=None, *, parent=None):
        super().__init__(parent=parent)

        self._data = None   # original image data
        self._image = None  # rendered image for display

        self._levels = (0, 1)  # [min, max]
        self._auto_level_quantile = 0.99
        self._lut = None

        # In some cases, a modified lookup table is used to handle both
        # rescaling and LUT more efficiently
        self._fast_lut = None

        self.setData(image, auto_levels=True)

    def setLevels(self, levels):
        """Set image colormap scaling levels.

        :param tuple levels: (min, max).
        """
        if self._levels != levels:
            self._levels = levels
            self._fast_lut = None
            self._prepareForRender()

    def levels(self) -> tuple:
        return self._levels

    def setLookupTable(self, lut, update=True) -> None:
        if lut is not self._lut:
            self._lut = lut
            self._fast_lut = None
            if update:
                self._prepareForRender()

    def _prepareForRender(self):
        self._image = None
        self.update()

    def updateGraph(self):
        self._data = None
        self._image = None
        self.prepareGeometryChange()
        self.informViewBoundsChanged()

    def clearData(self):
        self.setData(None)

    def _parseImageData(self, data):
        shape_changed = False
        dtype_changed = False
        if not isinstance(data, np.ndarray):
            raise TypeError("Image data must be a numpy.ndarray!")

        if data.ndim != 2:
            raise ValueError("Image data must be 2 dimensional!")

        if self._data is None:
            shape_changed = True
            dtype_changed = True
        elif data.shape != self._data.shape:
            shape_changed = True
        elif data.dtype != self._data.shape:
            dtype_changed = True

        self._data = data
        return shape_changed, dtype_changed

    def setData(self, data, *, auto_levels=False):
        if data is None:
            return

        shape_changed, dtype_changed = self._parseImageData(data)

        if shape_changed:
            self.prepareGeometryChange()
            self.informViewBoundsChanged()

        if auto_levels:
            self._levels = quick_min_max(
                self._data, q=self._auto_level_quantile)

        self._prepareForRender()

        self.image_changed_sgn.emit()

    def dataAt(self, x: int, y: int) -> float:
        return self._data[y, x]

    def render(self):
        """Convert data to QImage for displaying."""
        if self._data is None or self._data.size == 0:
            return

        # Request a lookup table
        if isinstance(self._lut, Callable):
            lut = self._lut(self._data)
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
            self._image = None
            return

        xds = max(1, int(1.0 / w))
        yds = max(1, int(1.0 / h))
        # TODO: replace fn.downsample
        image = fn.downsample(self._data, xds, axis=1)
        image = fn.downsample(image, yds, axis=0)

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
        self._image = fn.makeQImage(argb, alpha, transpose=False)

    def paint(self, p, *args) -> None:
        """Override."""
        if self._image is None:
            self.render()
            if self._image is None:
                return

        p.drawImage(QRectF(0, 0, *self._data.shape[::-1]), self._image)

    def histogram(self):
        """Return estimated histogram of image pixels.

        :returns: (hist, bin_centers)
        """
        if self._data is None or self._data.size == 0:
            return None, None

        step = (max(1, int(np.ceil(self._data.shape[0] / 200))),
                max(1, int(np.ceil(self._data.shape[1] / 200))))

        sliced_data = self._data[::step[0], ::step[1]]

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
        if self._data is None:
            return QRectF()
        shape = self._data.shape
        return QRectF(0., 0., shape[1], shape[0])
