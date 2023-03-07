"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import ABCMeta, abstractmethod
from typing import Optional
import weakref

import numpy as np

from ..backend.QtGui import (
    QColor, QFont, QImage, QPainter, QPainterPath, QPicture, QPixmap,
    QPolygonF, QTransform
)
from ..backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from ..backend.QtWidgets import (
    QGraphicsObject, QGraphicsTextItem, QGraphicsView
)

from ..aesthetics import FColor, FSymbol


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

    def _parseInputData(self, x, y, **kwargs):
        """Convert input to np.array and apply shape check."""
        if isinstance(x, list):
            x = np.array(x)
        elif x is None:
            x = np.array([])

        if isinstance(y, list):
            y = np.array(y)
        elif y is None:
            y = np.array([])

        if len(x) != len(y):
            raise ValueError("'x' and 'y' data have different lengths!")

        # do not set data unless they pass the sanity check!
        self._x, self._y = x, y

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
        canvas = self.canvas()
        if canvas is not None:
            canvas.updateAutoRange()

    def updateGraph(self):
        self._graph = None
        self.prepareGeometryChange()
        self.informBoundsChanged()

    def paint(self, p, *args) -> None:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        p.setPen(self._pen)
        p.drawPath(self._graph)

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return QRectF(self._graph.boundingRect())

    def setLogX(self, state):
        """Set log mode for x axis."""
        self._log_x_mode = state
        self.updateGraph()

    def setLogY(self, state):
        """Set log mode for y axis."""
        self._log_y_mode = state
        self.updateGraph()

    def transformedData(self):
        """Transform and return the internal data to log scale if requested.

        Child class should re-implement this method if it has a
        different internal data structure.
        """
        return (self.toLogScale(self._x) if self._log_x_mode else self._x,
                self.toLogScale(self._y) if self._log_y_mode else self._y)

    @staticmethod
    def toLogScale(arr, policy=None):
        """Convert array result to logarithmic scale."""
        ret = np.nan_to_num(arr)
        ret[ret < 0] = 0
        return np.log10(ret + 1)

    def label(self):
        """An identity of the PlotItem.

        Used in LegendWidget.
        """
        return self._label

    def setLabel(self, label: str) -> None:
        self._label = label
        self.label_changed_sgn.emit(label)

    def hasSample(self) -> bool:
        return self._has_sample

    def drawSample(self, p: Optional[QPainter] = None) -> bool:
        """Draw a sample used in LegendWidget."""
        return False


class CurvePlotItem(PlotItem):
    """CurvePlotItem."""

    def __init__(self, x=None, y=None, *,
                 pen=None, label=None, check_finite=True):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        self._pen = FColor.mkPen('g') if pen is None else pen

        self._check_finite = check_finite

        self.setData(x, y)

    def setData(self, x, y):
        """Override."""
        self._parseInputData(x, y)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [])

    def data(self):
        """Override."""
        return self._x, self._y

    def transformedData(self):
        """Override."""
        if not self._check_finite:
            return super().transformedData()

        # inf/nans completely prevent the plot from being displayed starting on
        # Qt version 5.12.3
        # we do not expect to have nan in x
        return (self.toLogScale(self._x) if self._log_x_mode else self._x,
                self.toLogScale(self._y)
                if self._log_y_mode else np.nan_to_num(self._y))

    def _prepareGraph(self) -> None:
        """Override."""
        x, y = self.transformedData()
        self._graph = self.array2Path(x, y)

    @staticmethod
    def array2Path(x, y):
        """Convert array to QPainterPath."""
        n = x.shape[0]
        if n < 2:
            return QPainterPath()

        polyline = QPolygonF()
        polyline.fill(QPointF(), n)

        buffer = polyline.data()
        if buffer is None:
            buffer = Qt.sip.voidptr(0)
        buffer.setsize(2 * n * np.dtype(np.double).itemsize)

        arr = np.frombuffer(buffer, np.double).reshape((-1, 2))

        arr[:, 0] = x
        arr[:, 1] = y
        path = QPainterPath()
        path.addPolygon(polyline)
        return path

    def drawSample(self, p=None) -> bool:
        """Override."""
        if p is not None:
            p.setPen(self._pen)
            # Legend sample has a bounding box of (0, 0, 20, 20)
            p.drawLine(0, 11, 20, 11)
        return True


class BarPlotItem(PlotItem):
    """BarPlotItem"""
    def __init__(self, x=None, y=None, *,
                 width=1.0, pen=None, brush=None, label=None):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        if width > 1.0 or width <= 0:
            width = 1.0
        self._width = width

        if pen is None and brush is None:
            self._pen = FColor.mkPen()
            self._brush = FColor.mkBrush('b')
        else:
            self._pen = FColor.mkPen() if pen is None else pen
            self._brush = FColor.mkBrush() if brush is None else brush

        self.setData(x, y)

    def setData(self, x, y):
        """Override."""
        self._parseInputData(x, y)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [])

    def data(self):
        """Override."""
        return self._x, self._y

    def _prepareGraph(self) -> None:
        """Override."""
        self._graph = QPicture()
        p = QPainter(self._graph)
        p.setPen(self._pen)
        p.setBrush(self._brush)

        x, y = self.transformedData()
        # Now it works for bar plot with equalized gaps
        # TODO: extend it
        if len(x) > 1:
            width = self._width * (x[1] - x[0])
        else:
            width = self._width

        for px, py in zip(x, y):
            p.drawRect(QRectF(px - width/2, 0, width, py))

        p.end()

    def paint(self, p, *args) -> None:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        self._graph.play(p)

    def boundingRect(self) -> QRectF:
        """Override."""
        return QRectF(PlotItem.boundingRect(self))

    def drawSample(self, p=None) -> bool:
        """Override."""
        if p is not None:
            p.setBrush(self._brush)
            p.setPen(self._pen)
            # Legend sample has a bounding box of (0, 0, 20, 20)
            p.drawRect(QRectF(2, 2, 18, 18))
        return True


class ErrorbarPlotItem(PlotItem):
    """ErrorbarPlotItem."""

    def __init__(self, x=None, y=None, *, y_min=None, y_max=None, beam=None,
                 line=False, pen=None, label=None):
        """Initialization.

        Note: y is not used for now.
        """
        super().__init__(label=label)

        self._x = None
        self._y = None
        self._y_min = None
        self._y_max = None

        self._beam = 0.0 if beam is None else beam
        self._line = line
        self._pen = FColor.mkPen('m') if pen is None else pen

        self.setData(x, y, y_min=y_min, y_max=y_max)

    def setData(self, x, y, y_min=None, y_max=None, beam=None):
        """Override."""
        self._parseInputData(x, y, y_min=y_min, y_max=y_max)

        if beam is not None:
            # keep the default beam if not specified
            self._beam = beam

        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [])

    def _parseInputData(self, x, y, **kwargs):
        """Override."""
        if isinstance(x, list):
            x = np.array(x)
        elif x is None:
            x = np.array([])

        if isinstance(y, list):
            y = np.array(y)
        elif y is None:
            y = np.array([])

        if len(x) != len(y):
            raise ValueError("'x' and 'y' data have different lengths!")

        y_min = kwargs.get('y_min', None)
        if isinstance(y_min, list):
            y_min = np.array(y_min)
        elif y_min is None:
            y_min = y

        y_max = kwargs.get('y_max', None)
        if isinstance(y_max, list):
            y_max = np.array(y_max)
        elif y_max is None:
            y_max = y

        if not len(y) == len(y_min) == len(y_max):
            raise ValueError(
                "'y_min' and 'y_max' data have different lengths!")

        # do not set data unless they pass the sanity check!
        self._x, self._y = x, y
        self._y_min, self._y_max = y_min, y_max

    def data(self):
        """Override."""
        return self._x, self._y, self._y_min, self._y_max

    def setBeam(self, w):
        self._beam = w

    def _prepareGraph(self) -> None:
        p = QPainterPath()

        x, y, y_min, y_max = self.transformedData()
        beam = self._beam
        for px, u, l in zip(x, y_min, y_max):
            # plot the lower horizontal lines
            p.moveTo(px - beam / 2., l)
            p.lineTo(px + beam / 2., l)

            # plot the vertical line
            p.moveTo(px, l)
            p.lineTo(px, u)

            # plot the upper horizontal line
            p.moveTo(px - beam / 2., u)
            p.lineTo(px + beam / 2., u)

        if self._line and len(x) > 2:
            p.moveTo(x[-1], y[-1])
            for px, py in zip(reversed(x[:-1]), reversed(y[:-1])):
                p.lineTo(px, py)

        self._graph = p

    def drawSample(self, p=None) -> bool:
        """Override."""
        if p is not None:
            p.setPen(self._pen)
            # Legend sample has a bounding box of (0, 0, 20, 20)
            p.drawLine(2, 2, 8, 2)  # lower horizontal line
            p.drawLine(5, 2, 5, 18)  # vertical line
            p.drawLine(2, 18, 8, 18)  # upper horizontal line
        return True

    def transformedData(self):
        """Override."""
        y_min = self.toLogScale(self._y_min) if self._log_y_mode else self._y_min
        y_max = self.toLogScale(self._y_max) if self._log_y_mode else self._y_max
        return super().transformedData() + (y_min, y_max)


class ScatterPlotItem(PlotItem):
    """ScatterPlotItem.

    Implemented based on pyqtgraph.ScatterPlotItem.
    """

    def __init__(self, x=None, y=None, *, symbol='o', size=8,
                 pen=None, brush=None, label=None):
        """Initialization."""
        super().__init__(label=label)

        self._x = None
        self._y = None

        if pen is None and brush is None:
            self._pen = FColor.mkPen()
            self._brush = FColor.mkBrush('b')
        else:
            self._pen = FColor.mkPen() if pen is None else pen
            self._brush = FColor.mkBrush() if brush is None else brush

        self._size = size

        self._symbol_path = FSymbol.mkSymbol(symbol)
        self._fragment = None
        self._buildFragment()

        self._graph = None

        self.setData(x, y)

    def setData(self, x, y):
        """Override."""
        self._parseInputData(x, y)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [])

    def data(self):
        """Override."""
        return self._x, self._y

    def _computePaddings(self) -> tuple[float, float]:
        w, h = self._fragment.width(), self._fragment.height()
        canvas = self.canvas()
        if canvas is None:
            return 0, 0
        rect = canvas.mapSceneToView(QRectF(0, 0, w, h)).boundingRect()
        return rect.width(), rect.height()

    def _prepareGraph(self) -> None:
        """Override."""
        self._graph = QRectF()
        if len(self._x) == 0:
            return

        x, y = self.transformedData()
        x_min, x_max = np.nanmin(x), np.nanmax(x)
        y_min, y_max = np.nanmin(y), np.nanmax(y)
        if np.isnan(x_min) or np.isnan(x_max):
            x_min, x_max = 0, 0
        if np.isnan(y_min) or np.isnan(y_max):
            y_min, y_max = 0, 0

        padding_x, padding_y = self._computePaddings()

        self._graph.setRect(x_min - padding_x,
                            y_min - padding_y,
                            x_max - x_min + 2 * padding_x,
                            y_max - y_min + 2 * padding_y)

    @staticmethod
    def transformCoordinates(matrix: QTransform, x: np.array, y: np.array,
                             dx: float = 0, dy: float = 0):
        # TODO: do it inplace?
        x = matrix.m11() * x + matrix.m21() * y + matrix.m31() + dx
        y = matrix.m12() * x + matrix.m22() * y + matrix.m32() + dy
        return x, y

    def paint(self, p, *args):
        """Override."""
        p.resetTransform()

        x, y = self.transformedData()
        w, h = self._fragment.width(), self._fragment.height()
        x, y = self.transformCoordinates(
            self.deviceTransform(), x, y, -w / 2., -h / 2.)
        src_rect = QRectF(self._fragment.rect())
        for px, py in zip(x, y):
            p.drawPixmap(QRectF(px, py, w, h), self._fragment, src_rect)

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return self._graph

    def drawSample(self, p=None):
        """Override."""
        if p is not None:
            p.translate(10, 10)
            self.drawSymbol(p)
        return True

    def drawSymbol(self, p: QPainter):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self._size, self._size)
        p.setPen(self._pen)
        p.setBrush(self._brush)
        p.drawPath(self._symbol_path)

    def _buildFragment(self):
        size = int(self._size + max(np.ceil(self._pen.widthF()), 1))
        symbol = QPixmap(size, size)
        symbol.fill(FColor.mkColor('w', alpha=0))
        p = QPainter(symbol)
        center = 0.5 * size
        p.translate(center, center)
        self.drawSymbol(p)
        p.end()

        self._fragment = symbol


class AnnotationItem(PlotItem):
    """Add annotation to a plot."""

    def __init__(self):
        super().__init__()

        self._x = None
        self._y = None
        self._annotations = None

        self._items = []

        self._offset_x = 0
        self._offset_y = 20

        self._font = None
        # self.setFont(self._font)

        self._color = None
        self.setColor(FColor.mkColor('b'))

        self.setData(self._x, self._y, self._annotations)

    def setOffsetX(self, x: float) -> None:
        """Set x offset of text items with respect to annotated points."""
        self._offset_x = x

    def setOffsetY(self, y: float) -> None:
        """Set y offset of text items with respect to annotated points."""
        self._offset_y = y

    def setFont(self, font: QFont) -> None:
        """Set the font of the text items."""
        self._font = font
        for item in self._items:
            item.setFont(self._font)
        self.update()

    def setColor(self, color: QColor) -> None:
        """Set the color of the text items."""
        self._color = color
        for item in self._items:
            item.setDefaultTextColor(self._color)
        self.update()

    def setData(self, x, y, annotations) -> None:
        """Override.

        :param x: x coordinates of the annotated points.
        :param y: y coordinates of the annotated points.
        :param annotations: displayed texts of the annotations.
        """
        self._parseInputData(x, y, annotations=annotations)
        self._updateTextItems(annotations)
        self.updateGraph()

    def clearData(self) -> None:
        """Override."""
        self.setData([], [], [])

    def data(self):
        """Override."""
        return self._x, self._y

    def _parseInputData(self, x, y, **kwargs):
        """Override."""
        super()._parseInputData(x, y)

        annotations = kwargs.get("annotations")
        if isinstance(annotations, list):
            annotations = np.array(annotations)
        elif annotations is None:
            annotations = self._x
        if len(self._x) != len(annotations):
            raise ValueError("Annotations have different lengths!")
        self._annotations = annotations

    def _updateTextItems(self, annotations):
        for i in range(len(self._items), len(self._x)):
            self._addItem()

    def _addItem(self):
        item = QGraphicsTextItem(parent=self)
        item.setDefaultTextColor(self._color)
        item.setFlag(item.GraphicsItemFlag.ItemIgnoresTransformations)
        item.show()
        self._items.append(item)

    def _mapOffsetToView(self):
        rect = self.canvas().mapSceneToView(
            QRectF(0, 0, self._offset_x, self._offset_y)).boundingRect()
        return (rect.width() if self._offset_x > 0 else -rect.width(),
                rect.height() if self._offset_y > 0 else -rect.height())

    def _computePaddings(self):
        padding_x = self._items[np.argmax(self._x)].boundingRect().width()
        padding_y = self._items[np.argmax(self._y)].boundingRect().height()
        rect = self.canvas().mapSceneToView(
            QRectF(0, 0, padding_x, padding_y)).boundingRect()
        return rect.width(), rect.height()

    def _prepareGraph(self) -> None:
        self._graph = QRectF()
        if len(self._x) == 0:
            return

        x, y = self.transformedData()

        offset_x, offset_y = self._mapOffsetToView()
        for i in range(len(self._items)):
            self._items[i].setPos(x[i] + offset_x, y[i] + offset_y)
            self._items[i].setPlainText(str(self._annotations[i]))

        padding_x, padding_y = self._computePaddings()
        x_min, x_max = np.min(x), np.max(x)
        y_min, y_max = np.min(y), np.max(y)

        self._graph.setRect(x_min,
                            y_min,
                            x_max - x_min + padding_x,
                            y_max - y_min + padding_y)

    def paint(self, p, *args) -> None:
        """Override."""
        ...

    def boundingRect(self) -> QRectF:
        """Override."""
        if self._graph is None:
            self._prepareGraph()
        return self._graph
