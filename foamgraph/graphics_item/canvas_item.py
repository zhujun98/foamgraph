from enum import Enum, IntEnum
import weakref

import numpy as np

from foamgraph.backend.QtWidgets import (
    QGraphicsRectItem, QHBoxLayout, QLabel, QMenu, QWidget, QWidgetAction
)
from foamgraph.backend.QtCore import pyqtSignal, QLineF, QPointF, QRectF, Qt
from foamgraph.backend.QtGui import (
    QAction, QActionGroup, QDoubleValidator, QGraphicsSceneResizeEvent,
    QGraphicsSceneWheelEvent, QSizePolicy, QTransform
)

from foamgraph.aesthetics import FColor
from foamgraph.graphics_scene import MouseClickEvent, MouseDragEvent
from foamgraph.graphics_item.graphics_item import (
    GraphicsItem, GraphicsObject, QGraphicsWidget
)


class WeakList(object):

    def __init__(self):
        self._items = []

    def append(self, obj):
        # Add backwards to iterate backwards (to make iterating more efficient on removal).
        self._items.insert(0, weakref.ref(obj))

    def __iter__(self):
        i = len(self._items)-1
        while i >= 0:
            ref = self._items[i]
            d = ref()
            if d is None:
                del self._items[i]
            else:
                yield d
            i -= 1


class ChildGroup(GraphicsObject):

    def __init__(self, parent):
        super().__init__(parent)
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)

        # Used as callback to inform CanvasItem when items are added/removed from
        # the group.
        # Note 1: We would prefer to override itemChange directly on the
        #         CanvasItem, but this causes crashes on PySide.
        # Note 2: We might also like to use a signal rather than this callback
        #         mechanism, but this causes a different PySide crash.
        self._parent = parent

        # excempt from telling view when transform changes
        self._GraphicsObject__inform_view_on_change = False

    def addItem(self, item):
        item.setParentItem(self)

    def itemChange(self, change, value):
        ret = super().itemChange(change, value)
        if change in [
            self.GraphicsItemChange.ItemChildAddedChange,
            self.GraphicsItemChange.ItemChildRemovedChange,
        ]:
            self._parent.updateAutoRange()
        return ret

    def boundingRect(self) -> QRectF:
        """Override."""
        return self.mapRectFromParent(self.parentItem().boundingRect())

    def paint(self, p, *args):
        """Override."""
        ...


class CanvasItem(QGraphicsWidget):
    """Box that allows internal scaling/panning of children by mouse drag.

    Features:

    * Scaling contents by mouse or auto-scale when contents change
    * View linking--multiple views display the same data ranges
    * Configurable by context menu
    * Item coordinate mapping methods

    """
    # Change the range of the AxisItem
    # Change the range of the linked CanvasItem
    x_range_changed_sgn = pyqtSignal()
    y_range_changed_sgn = pyqtSignal()
    # Change the check state of the QAction in AxisItem
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

    def __init__(self, parent=None, *, image: bool = False, debug: bool = True):
        """Initialization."""
        super().__init__(parent)

        self._items = []

        self._x_inverted = False
        self._y_inverted = False

        self._auto_range_x = True
        self._auto_range_y = True

        self._graph_rect = QRectF(0, 0, 1, 1)
        self._linked_x = None
        self._linked_y = None
        self._mouse_mode = self.MouseMode.Pan

        # clips the painting of all its descendants to its own shape
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)

        # childGroup is required so that CanvasItem has local coordinates similar to device coordinates.
        # this is a workaround for a Qt + OpenGL bug that causes improper clipping
        # https://bugreports.qt.nokia.com/browse/QTBUG-23723
        self.childGroup = ChildGroup(self)

        # region shown in MouseMode.Rect
        self._selected_rect = QGraphicsRectItem(0, 0, 1, 1)
        self._selected_rect.setPen(FColor.mkPen('Gold'))
        self._selected_rect.setBrush(FColor.mkBrush('Gold', alpha=100))
        self._selected_rect.setZValue(1e9)
        self._selected_rect.hide()
        self.addItem(self._selected_rect, ignore_bounds=True)

        if debug:
            self._border = QGraphicsRectItem(0, 0, 1, 1, parent=self)
            self._border.setPen(FColor.mkPen('r', width=2))
        else:
            self._border = None

        self.setZValue(-100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Expanding))

        self._menu = self.createContextMenu(image=image)

    def createContextMenu(self, image: bool):
        root = QMenu()

        action = root.addAction("View All")
        action.triggered.connect(lambda: self.setTargetRange(
            self.childrenBoundingRect(), disable_auto_range=True))

        # ---
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

        if not image:
            # ---
            action = root.addAction("Cross Cursor")
            action.setCheckable(True)
            action.triggered.connect(self.cross_cursor_toggled_sgn)

        return root

    def setMouseMode(self, mode: "CanvasItem.MouseMode"):
        self._mouse_mode = mode

    def addItem(self, item, ignore_bounds: bool = False):
        """Add a QGraphicsItem to this view.

        :param ignore_bounds:
        """
        if item.zValue() < self.zValue():
            item.setZValue(self.zValue() + 1)

        if not ignore_bounds:
            item.setParentItem(self.childGroup)
            self._items.append(item)
        else:
            item.setParentItem(self)

        if isinstance(item, GraphicsItem):
            item.setCanvasItem(self)

    def removeItem(self, item):
        """Remove an item from this view."""
        if item in self._items:
            self._items.remove(item)

        scene = self.scene()
        if scene is not None:
            scene.removeItem(item)
        item.setParentItem(None)

        self.updateAutoRange()

    def graphRect(self) -> QRectF:
        return self._graph_rect

    def _regularizeRange(self, vmin, vmax, axis: "CanvasItem.Axis"):
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
            # for debugging
            self._border.setRect(
                self.mapRectFromItem(self.childGroup, self._graph_rect))

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

    def linkXTo(self, canvas: "CanvasItem"):
        """Make X-axis change as X-axis of the given canvas changes."""
        if self._linked_x is not None:
            self._linked_x.x_range_changed_sgn.disconnect(self.xLinkChanged)
        canvas.x_range_changed_sgn.connect(self.linkedXChanged)
        self._linked_x = canvas

        self.enableAutoRangeX(False)
        canvas.x_range_changed_sgn.emit()

    def linkYTo(self, canvas: "CanvasItem"):
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
        rect = self.childrenBoundingRect()

        if self._auto_range_x:
            self.setTargetXRange(rect.left(), rect.right(),
                                 disable_auto_range=False,
                                 update=False)

        if self._auto_range_y:
            self.setTargetYRange(rect.top(), rect.bottom(),
                                 disable_auto_range=False,
                                 update=False)

        self._updateAll()

    def invertX(self, state: bool = True):
        self._x_inverted = state
        self.x_range_changed_sgn.emit()

    def invertY(self, state: bool = True):
        self._y_inverted = state
        self.y_range_changed_sgn.emit()

    def graphTransform(self) -> QTransform:
        return self.childGroup.transform()

    def invertedGraphTransform(self) -> QTransform:
        return self.itemTransform(self.childGroup)[0]

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
        """Maps from scene coordinates to coordinates displayed inside CanvasItem."""
        return self.invertedGraphTransform().map(self.mapFromScene(obj))

    def mapFromViewToItem(self, item, obj):
        """Maps *obj* from view coordinates to the local coordinate system of *item*."""
        return self.childGroup.mapToItem(item, obj)

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
        pos = ev.pos()
        delta = ev.lastPos() - pos

        # Scale or translate based on mouse button
        if ev.button() == Qt.MouseButton.LeftButton:
            if self._mouse_mode == self.MouseMode.Rect:
                if ev.exiting():
                    self._selected_rect.hide()
                    rect = self.childGroup.mapRectFromParent(QRectF(
                        ev.buttonDownPos(ev.button()), pos))
                    self.setTargetRange(rect.normalized())
                    self.update()
                else:
                    rect = self.childGroup.mapRectFromParent(
                        QRectF(ev.buttonDownPos(), ev.pos()))
                    self._selected_rect.setPos(rect.topLeft())
                    self._selected_rect.resetTransform()
                    self._selected_rect.scale(rect.width(), rect.height())
                    if ev.entering():
                        self._selected_rect.show()
            else:
                self.translateBy(delta.x(), delta.y())

            ev.accept()

    def childrenBoundingRect(self) -> QRectF:
        """Return the bounding rectangle of all children."""
        items = self._items

        bounding_rect = QRectF()
        for item in items:
            if not item.isVisible():
                continue

            bounding_rect = bounding_rect.united(
                self.childGroup.mapRectFromItem(item, item.boundingRect()))

        return bounding_rect

    def updateMatrix(self):
        """Update the childGroup's transform matrix."""
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

        self.childGroup.setTransform(m)

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos().toPoint())

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent):
        """Override."""
        self._updateAll()
        self.childGroup.prepareGeometryChange()

    def close(self) -> None:
        """Override."""
        for i in self._items:
            self.removeItem(i)
        for ch in self.childGroup.childItems():
            ch.setParentItem(None)
        super().close()

    def onCrossToggled(self, state: bool):
        if state:
            self._v_line.show()
            self._h_line.show()
        else:
            self._v_line.hide()
            self._h_line.hide()
