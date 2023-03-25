"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from enum import IntEnum
from typing import Any

import numpy as np

from ..backend.QtCore import pyqtSignal, QLineF, QPointF, QRectF, Qt
from ..backend.QtGui import (
    QAction, QActionGroup, QDoubleValidator,
    QTransform
)
from ..backend.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsRectItem,
    QGraphicsSceneResizeEvent, QGraphicsSceneWheelEvent, QGraphicsWidget,
    QHBoxLayout, QLabel, QMenu, QSizePolicy, QWidget, QWidgetAction
)

from ..aesthetics import FColor
from ..graphics_item import MouseCursorItem
from ..graphics_scene import HoverEvent, MouseClickEvent, MouseDragEvent


_DEBUG_CANVAS = False


class Canvas(QGraphicsWidget):
    """Canvas."""

    _Z_SELECTION_RECT = 100
    _Z_MOUSE_CURSOR = 200

    class CanvasProxy(QGraphicsObject):

        def __init__(self, parent: "Canvas"):
            super().__init__(parent=parent)
            self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)

            self._items = set()

        def addItem(self, item: QGraphicsItem, ignore_bounds: bool):
            if item in self.childItems():
                raise RuntimeError(f"Item {item} already exists!")
            if not ignore_bounds:
                self._items.add(item)
            item.setParentItem(self)

        def removeItem(self, item: QGraphicsItem):
            if item not in self._items:
                return
            self._items.remove(item)

        def itemChange(self, change, value) -> Any:
            ret = super().itemChange(change, value)
            if change in [
                self.GraphicsItemChange.ItemChildAddedChange,
                self.GraphicsItemChange.ItemChildRemovedChange,
            ]:
                self.parentItem().updateAutoRange()
            return ret

        def graphRect(self) -> QRectF:
            rect = QRectF()
            for item in self._items:
                if not item.isVisible():
                    continue
                rect = rect.united(
                    self.mapRectFromItem(item, item.boundingRect()))
            return rect

        def boundingRect(self) -> QRectF:
            """Override."""
            return self.parentItem().viewRect()

        def paint(self, p, *args):
            """Override."""
            ...

        def cleanUp(self) -> None:
            for item in self.childItems():
                item.setParentItem(None)
            self._items.clear()

    # Change the range of the AxisWidget
    # Change the range of the linked Canvas
    x_range_changed_sgn = pyqtSignal()
    y_range_changed_sgn = pyqtSignal()

    transform_changed_sgn = pyqtSignal()

    # Change the check state of the QAction in AxisWidget
    auto_range_x_toggled_sgn = pyqtSignal(bool)
    auto_range_y_toggled_sgn = pyqtSignal(bool)

    x_link_state_toggled_sgn = pyqtSignal(bool)
    y_link_state_toggled_sgn = pyqtSignal(bool)

    mouse_hovering_toggled_sgn = pyqtSignal(bool)
    mouse_moved_sgn = pyqtSignal(object)

    class MouseMode(IntEnum):
        Off = 0
        Pan = 1
        Zoom = 2

    class Axis(IntEnum):
        X = 0
        Y = 1

    WHEEL_SCALE_FACTOR = 0.00125

    def __init__(self, *,
                 auto_range_x_locked: bool = False,
                 auto_range_y_locked: bool = False,
                 parent=None):
        """Initialization."""
        super().__init__(parent)

        # The lock status of auto range is not allowed to be changed after
        # initialization. Otherwise, a few other things, e.g. Menu, are
        # required to be regenerated!
        self._auto_range_x_locked = auto_range_x_locked
        self._auto_range_y_locked = auto_range_y_locked

        self._auto_range_x = True
        self._auto_range_y = True

        self._aspect_ratio_locked = False

        self._x_inverted = False
        self._y_inverted = False

        # desired rect, which can be changed by mouse panning, zooming,
        # mouse wheel scrolling, etc.
        self._target_rect = QRectF()
        # actual view rect, which can be different from the desired rect
        # due to constraint such as aspect ratio.
        self._view_rect = QRectF()

        self._linked_x = None
        self._linked_y = None
        self._mouse_mode = self.MouseMode.Pan

        # clips the painting of all its descendants to its own shape
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)

        if _DEBUG_CANVAS:
            self._view_border = QGraphicsRectItem(0, 0, 1, 1, parent=self)
            self._view_border.setPen(FColor.mkPen('r', width=2))
            self._target_border = QGraphicsRectItem(0, 0, 1, 1, parent=self)
            self._target_border.setPen(FColor.mkPen('b', width=2))
        else:
            self._view_border = None
            self._target_border = None

        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Expanding))

        self._menu = self._createContextMenu()

        self._proxy = self.CanvasProxy(self)

        # region shown in MouseMode.Rect
        self._selection_rect = self._createSelectionRect()
        self.addItem(self._selection_rect, ignore_bounds=True)

    def _createContextMenu(self):
        root = QMenu()

        action = root.addAction("View All")
        action.setObjectName("ViewAll")
        action.triggered.connect(lambda: self.setTargetRange(
            self._proxy.graphRect(), disable_auto_range=True))

        # ---
        if not self._auto_range_x_locked and not self._auto_range_y_locked:
            menu = root.addMenu("Mouse Mode")
            menu.setObjectName("MouseMode")
            group = QActionGroup(menu)

            action = menu.addAction("Off")
            action.setObjectName("MouseMode_Off")
            action.setActionGroup(group)
            action.setCheckable(True)
            action.toggled.connect(
                lambda: self.__setMouseMode(self.MouseMode.Off))

            action = menu.addAction("Pan")
            action.setObjectName("MouseMode_Pan")
            action.setActionGroup(group)
            action.setCheckable(True)
            action.toggled.connect(
                lambda: self.__setMouseMode(self.MouseMode.Pan))
            action.setChecked(True)

            action = menu.addAction("Zoom")
            action.setObjectName("MouseMode_Zoom")
            action.setActionGroup(group)
            action.setCheckable(True)
            action.toggled.connect(
                lambda: self.__setMouseMode(self.MouseMode.Zoom))

        return root

    def getMenu(self, name: str) -> QMenu:
        return self._menu.findChild(QMenu, name)

    def getMenuAction(self, name: str) -> QAction:
        return self._menu.findChild(QAction, name)

    def extendContextMenu(self, label: str) -> QMenu:
        return self._menu.addMenu(label)

    def extendContextMenuAction(self, label: str) -> QAction:
        return self._menu.addAction(label)

    def setMouseMode(self, mode: int) -> None:
        self.getMenu("MouseMode").actions()[mode].setChecked(True)

    def __setMouseMode(self, mode: "Canvas.MouseMode"):
        self._mouse_mode = mode

    def setAspectRatioLocked(self, state: bool) -> None:
        self._aspect_ratio_locked = state
        self.resizeEvent(QGraphicsSceneResizeEvent())

    def _createSelectionRect(self):
        rect = QGraphicsRectItem(0, 0, 1, 1)
        rect.setPen(FColor.mkPen('Gold'))
        rect.setBrush(FColor.mkBrush('Gold', alpha=100))
        rect.setZValue(self._Z_SELECTION_RECT)
        rect.hide()
        return rect

    def addItem(self, item: QGraphicsItem, *, ignore_bounds=False):
        """Add a QGraphicsItem to this view."""
        if item.zValue() < self.zValue():
            item.setZValue(self.zValue() + 1)

        self._proxy.addItem(item, ignore_bounds)

        if hasattr(item, "setCanvas"):
            item.setCanvas(self)

        if isinstance(item, MouseCursorItem):
            item.setZValue(self._Z_MOUSE_CURSOR)

    def removeItem(self, item: QGraphicsItem) -> None:
        self._proxy.removeItem(item)

        scene = self.scene()
        if scene is not None:
            scene.removeItem(item)
        item.setParentItem(None)

    def targetRect(self) -> QRectF:
        return self._target_rect

    def viewRect(self) -> QRectF:
        return self._view_rect

    def _addPaddingToRange(self, vmin, vmax):
        delta = vmax - vmin
        # FIXME: not sure this is a good function
        padding = np.clip(1./(delta**0.5), 0.02, 0.1) \
            if delta > 0 else 0.02
        return vmin - padding, vmax + padding

    def _addPaddingToRect(self, rect: QRectF):
        x_min, x_max = self._addPaddingToRange(rect.left(), rect.right())
        y_min, y_max = self._addPaddingToRange(rect.top(), rect.bottom())
        rect.setRect(x_min, y_min, x_max - x_min, y_max - y_min)

    def _updateAll(self):
        self.x_range_changed_sgn.emit()
        self.y_range_changed_sgn.emit()
        self.updateMatrix()

        if _DEBUG_CANVAS:
            self._view_border.setRect(
                self.mapRectFromItem(self._proxy, self._view_rect))
            self._target_border.setRect(
                self.mapRectFromItem(self._proxy, self._target_rect))

        self.update()

    @staticmethod
    def scaleRange(x0, x1, scale):
        xc = (x0 + x1) / 2.
        hw = (x1 - x0) / 2.
        return xc - scale * hw, xc + scale * hw

    def _getLockedXRange(self, y0: float, y1: float):
        geometry = self.rect()
        if geometry.isEmpty():
            return
        geometry_ratio = geometry.width() / geometry.height()
        x0, x1 = self._view_rect.left(), self._view_rect.right()
        one_over_view_ratio = (y1 - y0) / (x1 - x0)
        scale = geometry_ratio * one_over_view_ratio
        return self.scaleRange(x0, x1, scale)

    def _getLockedYRange(self, x0: float, x1: float):
        geometry = self.rect()
        if geometry.isEmpty():
            return
        geometry_ratio = geometry.height() / geometry.width()
        y0, y1 = self._view_rect.top(), self._view_rect.bottom()
        one_over_view_ratio = (x1 - x0) / (y1 - y0)
        scale = geometry_ratio * one_over_view_ratio
        return self.scaleRange(y0, y1, scale)

    def _maybeAdjustAspectRatio(self, rect: QRectF) -> None:
        geometry = self.rect()
        if rect.isEmpty() or geometry.isEmpty():
            return

        geometry_ratio = geometry.height() / geometry.width()
        y0, y1 = rect.top(), rect.bottom()
        x0, x1 = rect.left(), rect.right()
        one_over_view_ratio = (x1 - x0) / (y1 - y0)
        scale = geometry_ratio * one_over_view_ratio

        if scale > 1:
            y0, y1 = self.scaleRange(y0, y1, scale)
            rect.setTop(y0)
            rect.setBottom(y1)
        elif scale < 1:
            x0, x1 = self.scaleRange(x0, x1, 1. / scale)
            rect.setLeft(x0)
            rect.setRight(x1)

    def setTargetXRange(self, x_min: float, x_max: float, *,
                        disable_auto_range: bool = True,
                        respect_aspect_ratio: bool = True,
                        update: bool = True):
        self._target_rect.setLeft(x_min)
        self._target_rect.setRight(x_max)

        if self._aspect_ratio_locked and respect_aspect_ratio:
            y_range = self._getLockedYRange(x_min, x_max)
            if y_range is not None:
                self._target_rect.setTop(y_range[0])
                self._target_rect.setBottom(y_range[1])

        self._view_rect = QRectF(self._target_rect)

        if disable_auto_range:
            self.enableAutoRangeX(False)

        if update:
            self._updateAll()

    def setTargetYRange(self, y_min: float, y_max: float, *,
                        disable_auto_range: bool = True,
                        respect_aspect_ratio: bool = True,
                        update: bool = True):
        self._target_rect.setTop(y_min)
        self._target_rect.setBottom(y_max)

        if self._aspect_ratio_locked and respect_aspect_ratio:
            x_range = self._getLockedXRange(y_min, y_max)
            if x_range is not None:
                self._target_rect.setLeft(x_range[0])
                self._target_rect.setRight(x_range[1])

        self._view_rect = QRectF(self._target_rect)

        if disable_auto_range:
            self.enableAutoRangeY(False)

        if update:
            self._updateAll()

    def setTargetRange(self, *args,
                       disable_auto_range: bool = True,
                       add_padding: bool = True,
                       aspect_ratio_changed: bool = True):
        if len(args) == 1:
            rect = args[0]
        else:
            xrange, yrange = args
            rect = QRectF(xrange[0], yrange[0],
                          xrange[1] - xrange[0], yrange[1] - yrange[0])

        if add_padding:
            self._addPaddingToRect(rect)

        if self._aspect_ratio_locked and aspect_ratio_changed:
            self._maybeAdjustAspectRatio(rect)

        self.setTargetXRange(rect.left(), rect.right(),
                             disable_auto_range=disable_auto_range,
                             respect_aspect_ratio=False,
                             update=False)

        self.setTargetYRange(rect.top(), rect.bottom(),
                             disable_auto_range=disable_auto_range,
                             respect_aspect_ratio=False,
                             update=False)

        self._updateAll()

    def enableAutoRangeX(self, state: bool = True) -> None:
        if self._auto_range_x_locked:
            return
        if self._auto_range_x ^ state:
            self._auto_range_x = state
            self.auto_range_x_toggled_sgn.emit(state)

    def enableAutoRangeY(self, state: bool = True) -> None:
        if self._auto_range_y_locked:
            return
        if self._auto_range_y ^ state:
            self._auto_range_y = state
            self.auto_range_y_toggled_sgn.emit(state)

    def linkXTo(self, canvas: "Canvas"):
        """Make X-axis change as X-axis of the given canvas changes."""
        if self._linked_x is not None:
            self._linked_x.x_range_changed_sgn.disconnect(self.linkedXChanged)
        canvas.x_range_changed_sgn.connect(self.linkedXChanged)
        self._linked_x = canvas

        self.enableAutoRangeX(False)
        canvas.x_range_changed_sgn.emit()

    def linkYTo(self, canvas: "Canvas"):
        """Link the Y-axis of this canvas to the x-axis of another one."""
        if self._linked_y is not None:
            self._linked_y.y_range_changed_sgn.disconnect(self.linkedYChanged)
        canvas.y_range_changed_sgn.connect(self.linkedYChanged)
        self._linked_y = canvas

        self.enableAutoRangeY(False)
        canvas.y_range_changed_sgn.emit()

    def linkedXChanged(self):
        rect = self._linked_x.targetRect()
        self.setTargetXRange(rect.left(), rect.right())

    def linkedYChanged(self):
        rect = self._linked_y.targetRect()
        self.setTargetYRange(rect.top(), rect.bottom())

    def updateAutoRange(self) -> None:
        if not self._auto_range_x and not self._auto_range_y:
            return

        rect = self._proxy.graphRect()
        if self._auto_range_x and self._auto_range_y:
            self._addPaddingToRect(rect)

            if self._aspect_ratio_locked:
                self._maybeAdjustAspectRatio(rect)

            self.setTargetXRange(rect.left(), rect.right(),
                                 disable_auto_range=False,
                                 respect_aspect_ratio=False,
                                 update=False)
            self.setTargetYRange(rect.top(), rect.bottom(),
                                 disable_auto_range=False,
                                 respect_aspect_ratio=False,
                                 update=False)
        elif self._auto_range_x:
            x_min, x_max = self._addPaddingToRange(rect.left(), rect.right())
            self.setTargetXRange(x_min, x_max,
                                 disable_auto_range=False,
                                 update=False)

        elif self._auto_range_y:
            y_min, y_max = self._addPaddingToRange(rect.top(), rect.bottom())
            self.setTargetYRange(y_min, y_max,
                                 disable_auto_range=False,
                                 update=False)

        self._updateAll()

    def invertX(self, inverted: bool = True) -> None:
        self._x_inverted = inverted
        self.x_range_changed_sgn.emit()
        self.updateMatrix()
        self.update()

    def invertY(self, inverted: bool = True) -> None:
        self._y_inverted = inverted
        self.y_range_changed_sgn.emit()
        self.updateMatrix()
        self.update()

    def graphTransform(self) -> QTransform:
        return self._proxy.transform()

    def invertedGraphTransform(self) -> QTransform:
        return self.itemTransform(self._proxy)[0]

    def mapRectToDevice(self, rect):
        """
        Return *rect* mapped from local coordinates to device coordinates (pixels).
        If there is no device mapping available, return None.
        """
        scene = self.scene()
        if scene is None:
            return

        views = scene.views()
        if not views:
            return

        view = self.scene().views()[0]

        dt = super().deviceTransform(view.viewportTransform())

        if dt.determinant() == 0:  # occurs when deviceTransform is invalid because widget has not been displayed
            return None

        return dt.mapRect(rect)

    def mapSceneToView(self, obj):
        """Maps from scene coordinates to coordinates displayed inside Canvas."""
        return self.invertedGraphTransform().map(self.mapFromScene(obj))

    def mapToView(self, obj):
        return self.invertedGraphTransform().map(obj)

    def mapFromView(self, obj):
        return self.graphTransform().map(obj)

    def mapFromViewToItem(self, item, obj):
        """Maps *obj* from view coordinates to the local coordinate system of *item*."""
        return self._proxy.mapToItem(item, obj)

    def mapFromItemToView(self, item, obj):
        return self._proxy.mapFromItem(item, obj)

    def scaleXBy(self, sx: float, xc: float) -> None:
        rect = self._view_rect
        center = self.invertedGraphTransform().map(QPointF(xc, 0))
        xc = center.x()
        x0 = xc + (rect.left() - xc) * sx
        x1 = xc + (rect.right() - xc) * sx
        self.setTargetXRange(x0, x1)

    def scaleYBy(self, sy: float, yc: float) -> None:
        rect = self._view_rect
        center = self.invertedGraphTransform().map(QPointF(0, yc))
        yc = center.y()
        y0 = yc + (rect.top() - yc) * sy
        y1 = yc + (rect.bottom() - yc) * sy
        self.setTargetYRange(y0, y1)

    def scaleBy(self, sx: float, sy: float, xc: float, yc: float) -> None:
        rect = self._view_rect
        center = self.invertedGraphTransform().map(QPointF(xc, yc))
        xc, yc = center.x(), center.y()
        x0 = xc + (rect.left() - xc) * sx
        x1 = xc + (rect.right() - xc) * sx
        y0 = yc + (rect.top() - yc) * sy
        y1 = yc + (rect.bottom() - yc) * sy
        self.setTargetRange((x0, x1), (y0, y1),
                            add_padding=False,
                            aspect_ratio_changed=(not sx == sy))

    def wheelMovementToScaleFactor(self, delta: float) -> float:
        return 1 + delta * self.WHEEL_SCALE_FACTOR

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent) -> None:
        """Override."""
        if self._auto_range_x_locked and self._auto_range_y_locked:
            return

        s = self.wheelMovementToScaleFactor(ev.delta())
        pos = ev.pos()
        if self._auto_range_x_locked:
            self.scaleYBy(s, pos.y())
        elif self._auto_range_y_locked:
            self.scaleXBy(s, pos.x())
        else:
            self.scaleBy(s, s, pos.x(), pos.y())
        ev.accept()

    def translateXBy(self, dx: float) -> None:
        rect = self._view_rect
        tr = self.invertedGraphTransform()
        l = tr.map(QLineF(0, 0, dx, 0))
        self.setTargetXRange(rect.left() + l.dx(), rect.right() + l.dx())

    def translateYBy(self, dy: float) -> None:
        rect = self._view_rect
        tr = self.invertedGraphTransform()
        l = tr.map(QLineF(0, 0, 0, dy))
        self.setTargetYRange(rect.top() + l.dy(), rect.bottom() + l.dy())

    def translateBy(self, dx: float, dy: float) -> None:
        rect = self._view_rect
        tr = self.invertedGraphTransform()
        l = tr.map(QLineF(0, 0, dx, dy))
        self.setTargetRange(rect.adjusted(l.dx(), l.dy(), l.dx(), l.dy()),
                            add_padding=False,
                            aspect_ratio_changed=False)

    def hoverEvent(self, ev: HoverEvent) -> None:
        if ev.isExit():
            self.mouse_hovering_toggled_sgn.emit(False)
        else:
            if ev.isEnter():
                self.mouse_hovering_toggled_sgn.emit(True)
            pos = self.mapToView(ev.pos())
            self.mouse_moved_sgn.emit(pos)

    def mouseDragEvent(self, ev: MouseDragEvent):
        if self._auto_range_x_locked and self._auto_range_y_locked:
            return

        if self._mouse_mode == self.MouseMode.Off:
            return

        pos = ev.pos()
        delta = ev.lastPos() - pos

        # Scale or translate based on mouse button
        if ev.button() == Qt.MouseButton.LeftButton:
            # Rect mode cannot be selected if any of _auto_range_x_locked
            # or _auto_range_y_locked is True.
            if self._mouse_mode == self.MouseMode.Zoom:
                rect = self._proxy.mapRectFromParent(
                    QRectF(ev.buttonDownPos(), ev.pos()))
                srect = self._selection_rect
                if ev.exiting():
                    srect.hide()
                    # should not go beyond the bounding rect of the canvas
                    self.setTargetRange(
                        rect.intersected(self._view_rect), add_padding=False)
                else:
                    if ev.entering():
                        srect.show()
                    srect.setPos(rect.topLeft())
                    tr = QTransform()
                    tr.scale(rect.width(), rect.height())
                    srect.setTransform(tr)

            else:  # self._mouse_mode == self.MouseMode.Pan
                if self._auto_range_x_locked:
                    self.translateYBy(delta.y())
                elif self._auto_range_y_locked:
                    self.translateXBy(delta.x())
                else:
                    self.translateBy(delta.x(), delta.y())

            ev.accept()

    def updateMatrix(self):
        """Update the proxy's transform matrix."""
        rect = self.rect()
        view_rect = self._view_rect

        if view_rect.isEmpty():
            return

        x_scale = rect.width() / view_rect.width()
        y_scale = rect.height() / view_rect.height()

        if self._x_inverted:
            x_scale = -x_scale
        if not self._y_inverted:
            y_scale = -y_scale

        m = QTransform()

        # First center the viewport at 0
        center = rect.center()
        m.translate(center.x(), center.y())

        # Now scale and translate properly
        m.scale(x_scale, y_scale)

        center = view_rect.center()
        m.translate(-center.x(), -center.y())

        self._proxy.setTransform(m)
        self.transform_changed_sgn.emit()

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos())

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent):
        """Override."""
        if self._aspect_ratio_locked:
            self._view_rect = QRectF(self._target_rect)
            self._maybeAdjustAspectRatio(self._view_rect)
        self._updateAll()

    def close(self) -> None:
        """Override."""
        self._proxy.cleanUp()
        super().close()
