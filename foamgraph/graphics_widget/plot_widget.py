"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod
from typing import Optional

from ..backend.QtCore import pyqtSignal, QPointF, Qt
from ..backend.QtGui import QActionGroup
from ..backend.QtWidgets import QGraphicsGridLayout, QSizePolicy

from ..aesthetics import FColor
from ..graphics_item import (
    CrossMouseCursorItem, MouseCursorItem, MouseCursorStyle
)
from .canvas import Canvas
from .graphics_widget import GraphicsWidget
from .label_widget import LabelWidget


class PlotWidget(GraphicsWidget):
    """2D plot widget for displaying graphs or an image.

    It contains a :class:`Canvas`, up to four :class:`AxisItem`s,
    a :class"`LabelWidget` for displaying the title and
    a :class:`MouseCursorItem`.
    """

    _TITLE_LOC = (0, 1)
    _CANVAS_LOC = (1, 1)
    _AXIS_BOTTOM_LOC = (2, 1)
    _AXIS_LEFT_LOC = (1, 0)
    _AXIS_RIGHT_LOC = (1, 2)

    cross_toggled_sgn = pyqtSignal(bool)

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self._canvas = Canvas(parent=self)

        self._axes = {}
        self._title = LabelWidget('')

        self._layout = QGraphicsGridLayout()

        self._mouse_cursor = None

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

        self._extendCanvasContextMenu()

    def _initConnections(self) -> None:
        ...

    def _extendCanvasContextMenu(self):
        menu = self._canvas.extendContextMenu("Cursor")
        menu.setObjectName("Cursor")

        action = menu.addAction("Show")
        action.setObjectName("Cursor_Show")
        action.setCheckable(True)
        action.toggled.connect(self._onMouseCursorToggled)

        style_menu = menu.addMenu("Style")
        style_menu.setObjectName("Cursor_Style")
        group = QActionGroup(style_menu)

        action = style_menu.addAction("Simple")
        action.setObjectName("Cursor_Style_Simple")
        action.setActionGroup(group)
        action.setCheckable(True)
        action.toggled.connect(lambda x: self._createMouseCursor(
            MouseCursorStyle.Simple, x))

        action = style_menu.addAction("Cross")
        action.setObjectName("Cursor_Style_Cross")
        action.setActionGroup(group)
        action.setCheckable(True)
        action.toggled.connect(lambda x: self._createMouseCursor(
            MouseCursorStyle.Cross, x))

        action = style_menu.addAction("Infinite Cross")
        action.setObjectName("Cursor_Style_InfiniteCross")
        action.setActionGroup(group)
        action.setCheckable(True)
        action.toggled.connect(lambda x: self._createMouseCursor(
            MouseCursorStyle.InfiniteCross, x))

    def _initAxisItems(self):
        ...

    def _setMouseCursorStyle(self, style: int) -> None:
        if style == MouseCursorStyle.Simple:
            action = "Cursor_Style_Simple"
        elif style == MouseCursorStyle.Cross:
            action = "Cursor_Style_Cross"
        else:  # style == MouseCursorStyle.InfiniteCross:
            action = "Cursor_Style_InfiniteCross"
        self._canvas.getMenuAction(action).setChecked(True)

    def _createMouseCursor(self, style: int, state: bool = True):
        if not state:
            return

        if self._mouse_cursor is not None:
            self._canvas.removeItem(self._mouse_cursor)

        # The parent of a mouse cursor cannot be the canvas because the mouse
        # cursor should not move when the canvas (e.g. its view range) has
        # changed. In another word, the mouse cursor should always stay at
        # the position where the real mouse cursor points at.
        if style == MouseCursorStyle.Simple:
            cursor = MouseCursorItem(parent=self)
        elif style == MouseCursorStyle.Cross:
            cursor = CrossMouseCursorItem(40, parent=self)
        else:
            cursor = CrossMouseCursorItem(-1, parent=self)
        cursor.setPen(FColor.mkPen("Magenta"))
        self._mouse_cursor = cursor

        # Mouse cursor should not be added to the Canvas because: when the view
        # range of the canvas changed, the mouse cursor should not move. Instead,
        # its label should get updated.

        cursor_show_act = self._canvas.getMenuAction("Cursor_Show")
        if cursor_show_act.isChecked():
            # initialize connections
            self._onMouseCursorToggled(True)
        else:
            # When a new cursor style is selected, we can assume that the user
            # wants to show it immediately. We also need the following line for
            # initializing signal-slot connections.
            cursor_show_act.setChecked(True)

    def _onMouseCursorToggled(self, state: bool):
        if state:
            self._mouse_cursor.show()
            self._canvas.mouse_moved_sgn.connect(self._onMouseCursorMoved)
            self._canvas.mouse_hovering_toggled_sgn.connect(
                self._mouse_cursor.setVisible)
            self._canvas.transform_changed_sgn.connect(
                self._updateMouseCursorLabel)
        else:
            self._mouse_cursor.hide()
            self._canvas.mouse_moved_sgn.disconnect(self._onMouseCursorMoved)
            self._canvas.mouse_hovering_toggled_sgn.disconnect(
                self._mouse_cursor.setVisible)
            self._canvas.transform_changed_sgn.disconnect(
                self._updateMouseCursorLabel)

    def _onMouseCursorMoved(self, pos: QPointF) -> None:
        pos = self._canvas.mapFromViewToItem(self, pos)
        self._mouse_cursor.setPos(pos)

    @abstractmethod
    def _updateMouseCursorLabel(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def clearData(self) -> None:
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

    def setAspectLocked(self, state: bool) -> None:
        self._canvas.setAspectRatioLocked(state)

    def close(self) -> None:
        """Override"""
        self._canvas.close()
        super().close()
