"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import ABCMeta, abstractmethod
from typing import Optional
import weakref

import numpy as np

from ...backend.QtGui import QPainter, QPolygonF, QTransform
from ...backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from ...backend.QtWidgets import QGraphicsObject, QGraphicsView
from ...utility import array_to_log_scale


class _PlotItemMeta(type(QGraphicsObject), ABCMeta):
    ...


class PlotItem(QGraphicsObject, metaclass=_PlotItemMeta):

    label_changed_sgn = pyqtSignal(str)

    def __init__(self, label: Optional[str] = None):
        super().__init__()

        self._graph = None

        self._canvas = None
        self._view = None

        self._label = "" if label is None else label

        self._log_x_mode = False
        self._log_y_mode = False

    @abstractmethod
    def setData(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def clearData(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @staticmethod
    def _parse_input(x, *, size=None, default=None):
        if isinstance(x, list):
            x = np.array(x)
        elif x is None:
            if default is None:
                x = np.array([])
            else:
                x = default

        if size is not None and len(x) != size:
            raise ValueError("'x' and 'y' data have different lengths!")
        return x

    @abstractmethod
    def _parseInputData(self, x, **kwargs):
        """Convert input to np.array and apply length check."""
        raise NotImplementedError

    @abstractmethod
    def data(self):
        raise NotImplementedError

    @abstractmethod
    def _prepareGraph(self) -> None:
        raise NotImplementedError

    def setCanvas(self, canvas: "Canvas") -> None:
        self._canvas = weakref.ref(canvas)

    def canvas(self) -> Optional["Canvas"]:
        return None if self._canvas is None else self._canvas()

    def view(self) -> Optional[QGraphicsView]:
        """Return the GraphicsView for this item.

        If the scene has multiple views, only the first view is returned.
        """
        if self._view is None:
            scene = self.scene()
            if scene is None:
                return
            views = scene.views()
            if len(views) == 0:
                return
            self._view = weakref.ref(views[0])

        return self._view()

    def deviceTransform(self) -> QTransform:
        view = self.view()
        if view is None:
            return QTransform()

        dt = super().deviceTransform(view.viewportTransform())
        return dt

    def informBoundsChanged(self) -> None:
        """Inform the `Canvas` to update the view range."""
        canvas = self.canvas()
        if canvas is not None:
            canvas.updateAutoRange()

    def updateGraph(self) -> None:
        self._graph = None
        self.prepareGeometryChange()
        self.informBoundsChanged()

    def setLogX(self, state) -> None:
        """Set log mode for x axis."""
        self._log_x_mode = state
        self.updateGraph()

    def setLogY(self, state) -> None:
        """Set log mode for y axis."""
        self._log_y_mode = state
        self.updateGraph()

    def transformedData(self) -> tuple:
        """Transform and return the internal data to log scale if requested.

        Child class should re-implement this method if it has a
        different internal data structure.
        """
        return (array_to_log_scale(self._x) if self._log_x_mode else self._x,
                array_to_log_scale(self._y) if self._log_y_mode else self._y)

    def label(self) -> str:
        """Label displayed in :class:`LegendWidget`."""
        return self._label

    def setLabel(self, label: str) -> None:
        self._label = label
        self.label_changed_sgn.emit(label)

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Draw a sample used in :class:`LegendWidget`."""
        return False

    @staticmethod
    def array2Polygon(x: np.ndarray, y: np.ndarray) -> QPolygonF:
        """Convert array to QPolygonF."""
        # Users are responsible for the validity of the input data.
        polygon = QPolygonF()
        n = x.size
        if n >= 1:
            polygon.fill(QPointF(), n)

            buffer = polygon.data()
            buffer.setsize(2 * n * np.dtype(np.float64).itemsize)
            arr = np.frombuffer(buffer, np.float64).reshape((-1, 2))
            arr[:, 0] = x
            arr[:, 1] = y

        return polygon
