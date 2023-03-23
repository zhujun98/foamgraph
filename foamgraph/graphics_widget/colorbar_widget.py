"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtGui import (
    QBrush, QColor, QLinearGradient, QPainter, QPixmap
)
from ..backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from ..backend.QtWidgets import (
    QGraphicsRectItem, QGraphicsSceneMouseEvent, QGraphicsSceneResizeEvent,
    QHBoxLayout, QLabel, QMenu, QSizePolicy, QWidget, QWidgetAction
)

from ..aesthetics import ColorMap
from .graphics_widget import GraphicsWidget


class ColorbarWidget(GraphicsWidget):
    """Widget for visualizing a color map."""

    colormap_changed_sgn = pyqtSignal()

    def __init__(self, orientation=Qt.Orientation.Vertical, *, parent=None):
        """Initialization.

        :param orientation: Orientation of the widget.
        """
        super().__init__(parent=parent)

        self._orientation = orientation

        self._cmap = None
        self._gradient = QGraphicsRectItem(parent=self)
        # self.setColorMap(ColorMap.fromName(config['COLOR_MAP']))

        # FIXME: do not use magic numbers
        self._gradient_width = 15
        self._width = 20

        self._menu = QMenu()

        self._initUI()

    def _initUI(self):
        if self._orientation == Qt.Orientation.Vertical:
            self.setMaximumWidth(self._width)
            self.setMinimumWidth(self._width)
            self.setSizePolicy(QSizePolicy.Policy.Fixed,
                               QSizePolicy.Policy.Expanding)
        elif self._orientation == Qt.Orientation.Horizontal:
            self.setMaximumHeight(self._width)
            self.setMinimumHeight(self._width)
            self.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Fixed)
        else:
            raise ValueError(f"Unknown orientation value: {self._orientation}")

        for name, ticks in ColorMap.gradients.items():
            self._menu.addAction(self._createCmapActionWidget(name, ticks))

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
        action.triggered.connect(
            lambda: self.setColorMap(ColorMap.fromName(action.data())))
        action.setData(name)
        return action

    def setColorMap(self, cmap: ColorMap) -> None:
        if self._orientation == Qt.Orientation.Vertical:
            gradient = QLinearGradient(0., 0., 0., 1.)
        else:
            gradient = QLinearGradient(0., 0., 1., 0.)
        gradient.setCoordinateMode(gradient.CoordinateMode.ObjectMode)

        gradient.setStops([(x, QColor(c)) for x, c in
                           zip(cmap.positions, cmap.colors)])
        self._gradient.setBrush(QBrush(gradient))

        self._cmap = cmap
        self.colormap_changed_sgn.emit()
        self.update()

    def colorMap(self) -> ColorMap:
        return self._cmap

    def mouseClickEvent(self, ev: QGraphicsSceneMouseEvent) -> None:
        if ev.button() == Qt.MouseButton.RightButton:
            self._menu.popup(ev.screenPos().toQPoint())
            ev.accept()

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent) -> None:
        """Override."""
        if self._orientation == Qt.Orientation.Horizontal:
            return self._gradient.setRect(
                0, 0, self.geometry().width(), self._gradient_width)
        self._gradient.setRect(
            0, 0, self._gradient_width, self.geometry().height())
