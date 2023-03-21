"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import namedtuple
from typing import Optional

import numpy as np

from ..backend.QtCore import pyqtSignal, pyqtSlot, QLineF, QPointF, QRectF, Qt
from ..backend.QtGui import QImage

from ..aesthetics import ColorMap
from ..algorithm import quick_min_max
from .graphics_item import GraphicsObject


class ImageItem(GraphicsObject):
    """GraphicsObject displaying a 2D image."""

    image_changed_sgn = pyqtSignal()

    Levels = namedtuple("Levels", ["min", "max"])

    def __init__(self, data: Optional[np.ndarray] = None, *, parent=None):
        super().__init__(parent=parent)

        self._data = None   # original image data
        self._qimage = None  # rendered image for display
        self._buffer = None

        self._levels = self.Levels(0, 1)
        self._auto_level_quantile = 0.99
        self._cmap = None
        self._lut = None

        self.setData(data, auto_levels=True)

    def setLevels(self, levels: tuple[float, float]):
        """Set image colormap scaling levels."""
        if self._levels != levels:
            self._levels = self.Levels(*levels)
            self._prepareForRender()

    def levels(self) -> "ImageItem.Levels":
        return self._levels

    def setColorMap(self, cmap: ColorMap):
        self._cmap = cmap
        self._lut = None
        self._prepareForRender()

    def _prepareForRender(self):
        self._qimage = None
        self.update()

    def clearData(self):
        self.setData(None)

    def _parseImageData(self, data):
        if not isinstance(data, np.ndarray):
            raise TypeError("Image data must be a numpy.ndarray!")

        if data.ndim != 2:
            raise ValueError("Image data must be 2 dimensional!")

        dtype_changed = False
        shape_changed = False
        if self._data is None:
            shape_changed = True
            dtype_changed = True
        elif data.shape != self._data.shape:
            shape_changed = True
        elif data.dtype != self._data.dtype:
            dtype_changed = True

        return dtype_changed, shape_changed

    def setData(self, data, *, auto_levels=False):
        if data is None:
            return

        shape_changed, dtype_changed = self._parseImageData(data)
        self._data = data

        if dtype_changed:
            self._lut = None

        if shape_changed:
            self.prepareGeometryChange()
            self.informViewBoundsChanged()

        if auto_levels:
            self._levels = self.Levels(*self.quick_min_max(
                self._data, q=self._auto_level_quantile))

        self._prepareForRender()

        self.image_changed_sgn.emit()

    def dataAt(self, x: int, y: int) -> float:
        return self._data[y, x]

    def _generateLookUpTable(self):
        n = 256 if self._data.dtype == np.uint8 else 512
        self._lut = self._cmap.getLookUpTable(n)

    @staticmethod
    def scaleForDisplay(data, v_min: float, v_max: float, num_colors: int):
        if data.dtype.kind in 'iu':
            # FIXME
            data = data.astype(float)
        else:
            data = data.copy()
        data -= v_min
        data *= num_colors / (v_max - v_min)
        data = np.clip(data, 0, num_colors - 1)
        return data.astype(np.min_scalar_type(num_colors - 1))

    @staticmethod
    def arrayToQImage(arr: np.ndarray, fmt: QImage.Format):
        h, w = arr.shape[:2]
        qimg = QImage(arr.ctypes.data, w, h, arr.strides[0], fmt)
        return qimg

    def _process_f(self):
        num_colors = self._lut.shape[0]
        v_min, v_max = self._levels
        if v_min == v_max:
            v_max = np.nextafter(v_max, 2 * v_max)

        scaled = self.scaleForDisplay(self._data, v_min, v_max, num_colors)

        data = np.take(self._lut, scaled, axis=0)

        order = [2, 1, 0, 3]
        for i in range(0, data.shape[2]):
            self._buffer[..., i] = data[..., order[i]]

    def _render(self):
        """Convert data to QImage for displaying."""
        data = self._data
        if data is None or data.size == 0:
            return

        if self._lut is None:
            self._generateLookUpTable()

        if self._buffer is None or self._buffer.shape[:2] != data.shape[:2]:
            self._buffer = np.empty(data.shape[:2] + (4,), dtype=np.uint8)

        self._process_f()

        self._qimage = self.arrayToQImage(
            self._buffer, QImage.Format.Format_ARGB32)

    def paint(self, p, *args) -> None:
        """Override."""
        if self._qimage is None:
            self._render()
            if self._qimage is None:
                return

        p.drawImage(QRectF(0, 0, *self._data.shape[::-1]), self._qimage)

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
