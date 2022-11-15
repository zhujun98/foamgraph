"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from .backend.QtGui import (
    QAction, QBrush, QColor, QGraphicsRectItem, QGraphicsWidget,
    QHBoxLayout, QLabel, QLinearGradient, QMenu, QPainter, QPixmap,
    QGraphicsSceneMouseEvent, QGraphicsSceneResizeEvent, QWidget,
    QWidgetAction
)
from .backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from .backend.QtWidgets import QSizePolicy

from . import pyqtgraph_be as pg

from .aesthetics import ColorMap


class GradientEditorWidget(pg.GraphicsWidget):

    gradient_changed_sgn = pyqtSignal(object)

    def __init__(self, orientation=Qt.Orientation.Vertical):
        """Initialization.

        :param orientation: Orientation of the widget.
        """
        super().__init__()

        self._colormap = None
        self._gradient = QGraphicsRectItem(parent=self)
        self._gradient_width = 15

        self._width = 20
        self._orientation = orientation
        if self._orientation == Qt.Orientation.Vertical:
            self.setMaximumWidth(self._width)
            self.setMinimumWidth(self._width)
            self.setSizePolicy(QSizePolicy.Policy.Fixed,
                               QSizePolicy.Policy.Expanding)
        elif orientation == Qt.Orientation.Horizontal:
            self.setMaximumHeight(self._width)
            self.setMinimumHeight(self._width)
            self.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Fixed)
        else:
            raise ValueError(f"Unknown orientation value: {orientation}")

        self._menu = QMenu()
        for name, ticks in ColorMap.gradients.items():
            self._menu.addAction(self._createCmapActionWidget(name, ticks))

    def gradientItem(self) -> QGraphicsRectItem:
        return self._gradient

    def _createCmapActionWidget(self, name: str, ticks: tuple) -> None:
        cmap = QPixmap(100, 15)
        p = QPainter(cmap)
        positions, colors = ticks
        grad = QLinearGradient(QPointF(0, 0), QPointF(cmap.width(), 0))
        grad.setStops([(x, QColor(*c)) for x, c in zip(positions, colors)])
        brush = QBrush(grad)
        p.fillRect(cmap.rect(), brush)
        p.end()

        label = QLabel(name)

        cbar = QLabel()
        cbar.setPixmap(cmap)
        cbar.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(cbar)

        widget = QWidget()
        widget.setLayout(layout)

        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        action.triggered.connect(self.onContextMenuClicked)
        action.setData(name)
        return action

    def onContextMenuClicked(self) -> None:
        self.setColorMap(ColorMap.fromName(self.sender().data()))

    def _colorAt(self, x: float):
        positions = self._colormap.positions
        colors = self._colormap.colors
        if x <= positions[0]:
            c = colors[0]
            return c.red(), c.green(), c.blue(), c.alpha()
        if x >= positions[-1]:
            c = colors[-1]
            return c.red(), c.green(), c.blue(), c.alpha()

        x2 = positions[0]
        for i in range(1, len(positions)):
            x1 = x2
            x2 = positions[i]
            if x1 <= x <= x2:
                break

        dx = x2 - x1
        if dx == 0:
            f = 0.
        else:
            f = (x - x1) / dx

        c1 = colors[i-1]
        c2 = colors[i]

        r = c1.red() * (1.-f) + c2.red() * f
        g = c1.green() * (1.-f) + c2.green() * f
        b = c1.blue() * (1.-f) + c2.blue() * f
        a = c1.alpha() * (1.-f) + c2.alpha() * f

        return r, g, b, a
                    
    def getLookupTable(self, n: int) -> np.ndarray:
        """Return an RGBA lookup table.

        :param n: The number of points in the returned lookup table.
        """
        table = np.empty((n, 4), dtype=np.ubyte)
            
        for i in range(n):
            x = float(i)/(n - 1)
            table[i] = self._colorAt(x)

        return table

    def setColorMap(self, colormap: ColorMap) -> None:
        self._colormap = colormap

        if self._orientation == Qt.Orientation.Vertical:
            gradient = QLinearGradient(0., 0., 0., self.geometry().height())
        else:
            gradient = QLinearGradient(0., 0., self.geometry().width(), 0.)

        gradient.setStops([
            (x, QColor(c)) for x, c in zip(self._colormap.positions,
                                           self._colormap.colors)])
        self._gradient.setBrush(QBrush(gradient))
        self.gradient_changed_sgn.emit(self)

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent) -> None:
        if self._orientation in ['bottom', 'top']:
            return self._gradient.setRect(
                0, 0, self.geometry().width(), self._gradient_width)
        self._gradient.setRect(
            0, 0, self._gradient_width, self.geometry().height())

    def mouseClickEvent(self, ev: QGraphicsSceneMouseEvent) -> None:
        if ev.button() == Qt.MouseButton.RightButton:
            self._menu.popup(ev.screenPos().toQPoint())
