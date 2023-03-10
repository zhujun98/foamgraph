"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod
from typing import Optional

from ..backend.QtCore import pyqtSignal, QPointF, Qt
from ..backend.QtWidgets import QGraphicsGridLayout, QSizePolicy

from .canvas import Canvas
from .graphics_widget import GraphicsWidget
from .label_widget import LabelWidget


class PlotWidget(GraphicsWidget):
    """2D plot widget for displaying graphs or an image."""

    _TITLE_LOC = (0, 1)
    _CANVAS_LOC = (1, 1)
    _AXIS_BOTTOM_LOC = (2, 1)
    _AXIS_LEFT_LOC = (1, 0)
    _AXIS_RIGHT_LOC = (1, 2)

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self._canvas = Canvas(parent=self)

        self._axes = {}
        self._title = LabelWidget('')

        self._layout = QGraphicsGridLayout()

    def _init(self) -> None:
        self._initUI()
        self._initConnections()

    def _initUI(self) -> None:
        layout = self._layout

        layout.setContentsMargins(*self.CONTENT_MARGIN)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        layout.addItem(self._title, *self._TITLE_LOC,
                       alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addItem(self._canvas, *self._CANVAS_LOC)

        for i in range(4):
            layout.setRowPreferredHeight(i, 0)
            layout.setRowMinimumHeight(i, 0)
            layout.setRowSpacing(i, 0)
            layout.setRowStretchFactor(i, 1)

        for i in range(3):
            layout.setColumnPreferredWidth(i, 0)
            layout.setColumnMinimumWidth(i, 0)
            layout.setColumnSpacing(i, 0)
            layout.setColumnStretchFactor(i, 1)

        layout.setRowStretchFactor(1, 100)
        layout.setColumnStretchFactor(1, 100)

        self.setLayout(layout)

        self._initAxisItems()
        self.setTitle()

    def _initConnections(self) -> None:
        ...

    def _initAxisItems(self):
        ...

    @abstractmethod
    def clearData(self):
        raise NotImplementedError

    def addItem(self, item) -> None:
        """Add a graphics item to Canvas."""
        self._canvas.addItem(item)

    def removeItem(self, item):
        """Add a graphics item to Canvas."""
        self._canvas.removeItem(item)

    def showAxis(self, axis: str, visible: bool = True) -> None:
        """Show the given axis.

        :param axis: axis name.
        :param visible: axis visibility.
        """
        self._axes[axis].setVisible(visible)

    def setLabel(self, axis: str, text: Optional[str] = None) -> None:
        """Set the label for an axis.

        :param axis: axis name.
        :param text: text to display along the axis.
        """
        self._axes[axis].setLabel(text=text)
        self.showAxis(axis)

    def showLabel(self, axis: str, visible: bool = True) -> None:
        """Show or hide one of the axis labels.

        :param axis: axis name.
        :param visible: label visibility.
        """
        self._axes[axis].showLabel(visible)

    def setTitle(self, text: Optional[str] = None) -> None:
        if text is None:
            self._title.setMaximumHeight(0)
            self._layout.setRowFixedHeight(self._TITLE_LOC[0], 0)
            self._title.setVisible(False)
        else:
            self._title.setMaximumHeight(30)
            self._layout.setRowFixedHeight(self._TITLE_LOC[0], 30)
            self._title.setPlainText(text)
            self._title.setVisible(True)

    def invertX(self, inverted: bool = True) -> None:
        self._canvas.invertX(inverted)

    def invertY(self, inverted: bool = True) -> None:
        self._canvas.invertY(inverted)

    def close(self) -> None:
        """Override"""
        self._canvas.close()
        super().close()
