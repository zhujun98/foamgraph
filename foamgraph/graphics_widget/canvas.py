from enum import Enum, IntEnum

import numpy as np

from ..backend.QtCore import pyqtSignal, QLineF, QPointF, QRectF, Qt
from ..backend.QtGui import (
    QAction, QActionGroup, QDoubleValidator, QGraphicsSceneResizeEvent,
    QGraphicsSceneWheelEvent, QSizePolicy, QTransform
)
from ..backend.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsWidget, QGraphicsRectItem,
    QHBoxLayout, QLabel, QMenu, QWidget, QWidgetAction
)

from ..aesthetics import FColor
from ..graphics_scene import MouseClickEvent, MouseDragEvent


_DEBUG_CANVAS = False


class Canvas(QGraphicsWidget):
    """Canvas."""

    _Z_SELECTION_RECT = 100

    class CanvasProxy(QGraphicsObject):

        def __init__(self, parent: "Canvas"):
            super().__init__(parent=parent)

            self._items = set()

        def addItem(self, item: QGraphicsItem):
            if item in self._items:
                raise RuntimeError(f"Item {item} already exists!")
            self._items.add(item)
            item.setParentItem(self)

        def removeItem(self, item: QGraphicsItem):
            if item not in self._items:
                return
            self._items.remove(item)

        def itemChange(self, change, value):
            ret = super().itemChange(change, value)
            if change in [
                self.GraphicsItemChange.ItemChildAddedChange,
                self.GraphicsItemChange.ItemChildRemovedChange,
            ]:
                self.parentItem().updateAutoRange()
            return ret

        def viewRect(self) -> QRectF:
            bounding_rect = QRectF()
            for item in self._items:
                if not item.isVisible():
                    continue

                bounding_rect = bounding_rect.united(
                    self.mapRectFromItem(item, item.boundingRect()))

            return bounding_rect

        def boundingRect(self) -> QRectF:
            """Override."""
            return self.parentItem().graphRect()

        def paint(self, p, *args):
            """Override."""
            ...

        def cleanUp(self) -> None:
            for item in self._items:
                item.setParentItem(None)
            self._items.clear()

    # Change the range of the AxisWidget
    # Change the range of the linked Canvas
    x_range_changed_sgn = pyqtSignal()
    y_range_changed_sgn = pyqtSignal()
    # Change the check state of the QAction in AxisWidget
    auto_range_x_toggled_sgn = pyqtSignal(bool)
    auto_range_y_toggled_sgn = pyqtSignal(bool)

    x_link_state_toggled_sgn = pyqtSignal(bool)
    y_link_state_toggled_sgn = pyqtSignal(bool)

    cross_cursor_toggled_sgn = pyqtSignal(bool)

    class MouseMode(Enum):
        Pan = 3
        Rect = 1

    class Axis(IntEnum):
        X = 0
        Y = 1

    WHEEL_SCALE_FACTOR = 0.00125

    def __init__(self, *,
                 cross_cursor_enabled: bool = False,
                 draggable: bool = True,
                 scalable: bool = True,
                 parent=None):
        """Initialization."""
        super().__init__(parent)

        self._x_inverted = False
        self._y_inverted = False

        self._auto_range_x = True
        self._auto_range_y = True

        self._graph_rect = QRectF(0, 0, 1, 1)
        self._linked_x = None
        self._linked_y = None
        self._mouse_mode = self.MouseMode.Pan

        self._draggable = draggable
        self._scalable = scalable
        self._cross_cursor_enabled = cross_cursor_enabled

        # clips the painting of all its descendants to its own shape
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)

        if _DEBUG_CANVAS:
            self._border = QGraphicsRectItem(0, 0, 1, 1, parent=self)
            self._border.setPen(FColor.mkPen('r', width=2))
        else:
            self._border = None

        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Expanding))

        self._menu = self._createContextMenu()

        self._proxy = self.CanvasProxy(self)

        # region shown in MouseMode.Rect
        self._selection_rect = self._createSelectionRect()
        self.addItem(self._selection_rect)

    def enableCrossCursor(self, state: bool) -> None:
        self._cross_cursor_enabled = state
        self._menu = self._createContextMenu()

    def _createContextMenu(self):
        root = QMenu()

        action = root.addAction("View All")
        action.triggered.connect(lambda: self.setTargetRange(
            self._proxy.viewRect(), disable_auto_range=True))

        # ---
        if self._draggable:
            menu = root.addMenu("Mouse Mode")
            group = QActionGroup(menu)

            action = menu.addAction("Pan")
            action.setActionGroup(group)
            action.setCheckable(True)
            action.triggered.connect(
                lambda: self.setMouseMode(self.MouseMode.Pan))
            action.setChecked(True)

            action = menu.addAction("Zoom")
            action.setActionGroup(group)
            action.setCheckable(True)
            action.triggered.connect(
                lambda: self.setMouseMode(self.MouseMode.Rect))

        if self._cross_cursor_enabled:
            # ---
            action = root.addAction("Cross Cursor")
            action.setCheckable(True)
            action.triggered.connect(self.cross_cursor_toggled_sgn)

        return root

    def _createSelectionRect(self):
        rect = QGraphicsRectItem(0, 0, 1, 1)
        rect.setPen(FColor.mkPen('Gold'))
        rect.setBrush(FColor.mkBrush('Gold', alpha=100))
        rect.setZValue(self._Z_SELECTION_RECT)
        rect.hide()
        return rect

    def setMouseMode(self, mode: "Canvas.MouseMode"):
        self._mouse_mode = mode

    def addItem(self, item: QGraphicsItem):
        """Add a QGraphicsItem to this view."""
        if item.zValue() < self.zValue():
            item.setZValue(self.zValue() + 1)

        self._proxy.addItem(item)

        if hasattr(item, "setCanvas"):
            item.setCanvas(self)

    def removeItem(self, item: QGraphicsItem) -> None:
        self._proxy.removeItem(item)

        scene = self.scene()
        if scene is not None:
            scene.removeItem(item)
        item.setParentItem(None)

    def graphRect(self) -> QRectF:
        return self._graph_rect

    def _regularizeRange(self, vmin, vmax, axis: "Canvas.Axis"):
        # If we requested 0 range, try to preserve previous scale.
        # Otherwise just pick an arbitrary scale.
        if vmin == vmax:
            if axis == self.Axis.X:
                dy = self._graph_rect.width()
            else:
                dy = self._graph_rect.height()

            if dy == 0:
                dy = 1
            vmin -= 0.5 * dy
            vmax += 0.5 * dy

        return vmin, vmax

    def _updateAll(self):
        if self._border is not None:
            self._border.setRect(
                self.mapRectFromItem(self._proxy, self._graph_rect))

        self.x_range_changed_sgn.emit()
        self.y_range_changed_sgn.emit()
        self.updateMatrix()
        self.update()

    def setTargetXRange(self, vmin: float, vmax: float, *,
                        disable_auto_range: bool = True,
                        update: bool = True):
        vmin, vmax = self._regularizeRange(vmin, vmax, self.Axis.X)
        self._graph_rect.setLeft(vmin)
        self._graph_rect.setRight(vmax)

        if disable_auto_range:
            self.enableAutoRangeX(False)

        if update:
            self._updateAll()

    def setTargetYRange(self, vmin: float, vmax: float, *,
                        disable_auto_range: bool = True,
                        update: bool = True):
        vmin, vmax = self._regularizeRange(vmin, vmax, self.Axis.Y)
        self._graph_rect.setTop(vmin)
        self._graph_rect.setBottom(vmax)

        if disable_auto_range:
            self.enableAutoRangeY(False)

        if update:
            self._updateAll()

    def setTargetRange(self, *args, disable_auto_range: bool = True):
        if len(args) == 1:
            rect = args[0]
            xrange = (rect.left(), rect.right())
            # Caveat: y-axis pointing to the opposite direction of the
            #         y axis of a QRect
            yrange = (rect.top(), rect.bottom())
        else:
            xrange, yrange = args

        self.setTargetXRange(xrange[0], xrange[1],
                             disable_auto_range=disable_auto_range,
                             update=False)
        self.setTargetYRange(yrange[0], yrange[1],
                             disable_auto_range=disable_auto_range,
                             update=False)
        self._updateAll()

    def suggestPadding(self, axis):
        l = self.geometry().width() if axis == self.Axis.X else self.geometry().height()
        if l > 0:
            return np.clip(1./(l**0.5), 0.02, 0.1)
        return 0.02

    def enableAutoRangeX(self, state: bool = True):
        if self._auto_range_x ^ state:
            self._auto_range_x = state
            self.auto_range_x_toggled_sgn.emit(state)

    def enableAutoRangeY(self, state: bool = True):
        if self._auto_range_y ^ state:
            self._auto_range_y = state
            self.auto_range_y_toggled_sgn.emit(state)

    def linkXTo(self, canvas: "Canvas"):
        """Make X-axis change as X-axis of the given canvas changes."""
        if self._linked_x is not None:
            self._linked_x.x_range_changed_sgn.disconnect(self.xLinkChanged)
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
        rect = self._linked_x.graphRect()
        self.setTargetXRange(rect.left(), rect.right())

    def linkedYChanged(self):
        rect = self._linked_y.graphRect()
        self.setTargetYRange(rect.top(), rect.bottom())

    def screenGeometry(self):
        """return the screen geometry"""
        view = self.scene().views()[0]

        b = self.sceneBoundingRect()
        wr = view.mapFromScene(b).boundingRect()

        pos = view.mapToGlobal(view.pos())
        wr.adjust(pos.x(), pos.y(), pos.x(), pos.y())
        return wr

    def updateAutoRange(self) -> None:
        rect = self._proxy.viewRect()

        if self._auto_range_x:
            self.setTargetXRange(rect.left(), rect.right(),
                                 disable_auto_range=False,
                                 update=False)

        if self._auto_range_y:
            self.setTargetYRange(rect.top(), rect.bottom(),
                                 disable_auto_range=False,
                                 update=False)

        self._updateAll()

    def invertX(self, inverted: bool = True):
        self._x_inverted = inverted
        self.x_range_changed_sgn.emit()

    def invertY(self, inverted: bool = True):
        self._y_inverted = inverted
        self.y_range_changed_sgn.emit()

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
        rect = self._graph_rect
        center = self.invertedGraphTransform().map(QPointF(xc, 0))
        xc = center.x()
        x0 = xc + (rect.left() - xc) * sx
        x1 = xc + (rect.right() - xc) * sx
        self.setTargetXRange(x0, x1)

    def scaleYBy(self, sy: float, yc: float) -> None:
        rect = self._graph_rect
        center = self.invertedGraphTransform().map(QPointF(0, yc))
        yc = center.y()
        y0 = yc + (rect.top() - yc) * sy
        y1 = yc + (rect.bottom() - yc) * sy
        self.setTargetYRange(y0, y1)

    def scaleBy(self, sx: float, sy: float, xc: float, yc: float) -> None:
        rect = self._graph_rect
        center = self.invertedGraphTransform().map(QPointF(xc, yc))
        xc, yc = center.x(), center.y()
        x0 = xc + (rect.left() - xc) * sx
        x1 = xc + (rect.right() - xc) * sx
        y0 = yc + (rect.top() - yc) * sy
        y1 = yc + (rect.bottom() - yc) * sy
        self.setTargetRange((x0, x1), (y0, y1))

    def wheelMovementToScaleFactor(self, delta: float) -> float:
        return 1 + delta * self.WHEEL_SCALE_FACTOR

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent) -> None:
        """Override."""
        if not self._scalable:
            return

        s = self.wheelMovementToScaleFactor(ev.delta())
        pos = ev.pos()
        self.scaleBy(s, s, pos.x(), pos.y())
        ev.accept()

    def translateXBy(self, dx: float) -> None:
        rect = self._graph_rect
        tr = self.invertedGraphTransform()
        l = tr.map(QLineF(0, 0, dx, 0))
        self.setTargetXRange(rect.left() + l.dx(), rect.right() + l.dx())

    def translateYBy(self, dy: float) -> None:
        rect = self._graph_rect
        tr = self.invertedGraphTransform()
        l = tr.map(QLineF(0, 0, 0, dy))
        self.setTargetYRange(rect.top() + l.dy(), rect.bottom() + l.dy())

    def translateBy(self, dx: float, dy: float) -> None:
        rect = self._graph_rect
        tr = self.invertedGraphTransform()
        l = tr.map(QLineF(0, 0, dx, dy))
        self.setTargetRange(rect.adjusted(l.dx(), l.dy(), l.dx(), l.dy()))

    def mouseDragEvent(self, ev: MouseDragEvent):
        if not self._draggable:
            return

        pos = ev.pos()
        delta = ev.lastPos() - pos

        # Scale or translate based on mouse button
        if ev.button() == Qt.MouseButton.LeftButton:
            if self._mouse_mode == self.MouseMode.Rect:
                if ev.exiting():
                    self._selection_rect.hide()
                    rect = self._proxy.mapRectFromParent(QRectF(
                        ev.buttonDownPos(ev.button()), pos))
                    self.setTargetRange(rect.normalized())
                else:
                    rect = self._proxy.mapRectFromParent(
                        QRectF(ev.buttonDownPos(), ev.pos()))
                    self._selection_rect.setPos(rect.topLeft())
                    self._selection_rect.resetTransform()
                    self._selection_rect.scale(rect.width(), rect.height())
                    if ev.entering():
                        self._selection_rect.show()
            else:
                self.translateBy(delta.x(), delta.y())

            ev.accept()

    def updateMatrix(self):
        """Update the proxy's transform matrix."""
        rect = self.rect()
        graph_rect = self._graph_rect

        # when?
        if graph_rect.height() == 0 or graph_rect.width() == 0:
            return

        x_scale = rect.width() / graph_rect.width()
        y_scale = rect.height() / graph_rect.height()

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

        center = graph_rect.center()
        m.translate(-center.x(), -center.y())

        self._proxy.setTransform(m)

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos().toPoint())

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent):
        """Override."""
        self._updateAll()
        self._proxy.prepareGeometryChange()

    def onCrossToggled(self, state: bool):
        if state:
            self._v_line.show()
            self._h_line.show()
        else:
            self._v_line.hide()
            self._h_line.hide()

    def close(self) -> None:
        """Override."""
        self._proxy.cleanUp()
        super().close()