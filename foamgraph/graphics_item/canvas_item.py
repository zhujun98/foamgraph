from enum import Enum, IntEnum
import weakref

import numpy as np

from foamgraph.backend.QtWidgets import (
    QGraphicsRectItem, QHBoxLayout, QLabel, QMenu, QWidget, QWidgetAction
)
from foamgraph.backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from foamgraph.backend.QtGui import (
    QAction, QActionGroup, QDoubleValidator, QGraphicsSceneResizeEvent,
    QGraphicsSceneWheelEvent, QSizePolicy, QTransform
)

from foamgraph.pyqtgraph_be import functions as fn

from foamgraph.aesthetics import FColor
from foamgraph.graphics_scene import MouseClickEvent, MouseDragEvent
from foamgraph.graphics_item.graphics_item import GraphicsObject, GraphicsWidget


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

        # Used as callback to inform ViewBox when items are added/removed from
        # the group.
        # Note 1: We would prefer to override itemChange directly on the
        #         ViewBox, but this causes crashes on PySide.
        # Note 2: We might also like to use a signal rather than this callback
        #         mechanism, but this causes a different PySide crash.
        self.itemsChangedListeners = WeakList()

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
            try:
                itemsChangedListeners = self.itemsChangedListeners
            except AttributeError:
                # It's possible that the attribute was already collected when the itemChange happened
                # (if it was triggered during the gc of the object).
                pass
            else:
                for listener in itemsChangedListeners:
                    listener.updateAutoRange()
        return ret

    def shape(self):
        return self.mapFromParent(self.parentItem().shape())

    def boundingRect(self) -> QRectF:
        """Override."""
        return self.mapRectFromParent(self.parentItem().boundingRect())

    def paint(self, p, *args):
        """Override."""
        ...


class ViewBox(GraphicsWidget):
    """Box that allows internal scaling/panning of children by mouse drag.

    Features:

    * Scaling contents by mouse or auto-scale when contents change
    * View linking--multiple views display the same data ranges
    * Configurable by context menu
    * Item coordinate mapping methods

    """
    y_range_changed_sgn = pyqtSignal()
    x_range_changed_sgn = pyqtSignal()
    range_changed_sgn = pyqtSignal(object, object)
    auto_range_x_toggled_sgn = pyqtSignal(bool)
    auto_range_y_toggled_sgn = pyqtSignal(bool)
    transform_changed_sgn = pyqtSignal(object)
    resized_sgn = pyqtSignal(object)

    cross_cursor_toggled_sgn = pyqtSignal(bool)

    class MouseMode(Enum):
        Pan = 3
        Rect = 1

    class Axis(IntEnum):
        X = 0
        Y = 1
        XY = 2

    WHEEL_SCALE_FACTOR = 0.00125

    def __init__(self, parent=None, *, image: bool = False, debug: bool = True):
        """Initialization."""
        super().__init__(parent)

        self._block_links = False

        self._items = []
        self._updating_range = False  # Used to break recursive loops. See updateAutoRange.

        self._axis_inverted = [False, False]
        self._auto_range = [False, False]

        self._view_rect = QRectF(0, 0, 1, 1)  # actual range viewed
        self._target_rect = QRectF(0, 0, 1, 1)
        self._linked_views = [None, None]
        self._mouse_mode = self.MouseMode.Pan

        # clips the painting of all its descendants to its own shape
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)

        # childGroup is required so that ViewBox has local coordinates similar to device coordinates.
        # this is a workaround for a Qt + OpenGL bug that causes improper clipping
        # https://bugreports.qt.nokia.com/browse/QTBUG-23723
        self.childGroup = ChildGroup(self)
        self.childGroup.itemsChangedListeners.append(self)

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
        action.triggered.connect(
            lambda: self.viewAll(disable_auto_range=True))

        # ---
        menu = root.addMenu("Mouse Mode")
        group = QActionGroup(menu)

        action = menu.addAction("Pan")
        action.setActionGroup(group)
        action.setCheckable(True)
        action.triggered.connect(lambda: self.setMouseMode(self.MouseMode.Pan))
        action.setChecked(True)

        action = menu.addAction("Zoom")
        action.setActionGroup(group)
        action.setCheckable(True)
        action.triggered.connect(lambda: self.setMouseMode(self.MouseMode.Rect))

        if not image:
            # ---
            action = root.addAction("Cross Cursor")
            action.setCheckable(True)
            action.triggered.connect(self.cross_cursor_toggled_sgn)

        return root

    def setMouseMode(self, mode: "ViewBox.MouseMode"):
        self._mouse_mode = mode

    def addItem(self, item, ignore_bounds: bool = False):
        """Add a QGraphicsItem to this view.

        :param ignore_bounds:
        """
        if item.zValue() < self.zValue():
            item.setZValue(self.zValue() + 1)

        scene = self.scene()
        if scene is not None and scene is not item.scene():
            scene.addItem(item)  # Necessary due to Qt bug: https://bugreports.qt-project.org/browse/QTBUG-18616
        item.setParentItem(self.childGroup)

        if not ignore_bounds:
            self._items.append(item)
        self.updateAutoRange()

    def removeItem(self, item):
        """Remove an item from this view."""
        if item in self._items:
            self._items.remove(item)

        scene = self.scene()
        if scene is not None:
            scene.removeItem(item)
        item.setParentItem(None)

        self.updateAutoRange()

    def viewRect(self) -> QRectF:
        return self._view_rect

    def targetRect(self) -> QRectF:
        return self._target_rect

    def _regularizeRange(self, vmin, vmax, axis: "ViewBox.Axis", padding):
        # If we requested 0 range, try to preserve previous scale.
        # Otherwise just pick an arbitrary scale.
        if vmin == vmax:
            if axis == self.Axis.X:
                dy = self._view_rect.width()
            else:
                dy = self._view_rect.height()

            if dy == 0:
                dy = 1
            vmin -= 0.5 * dy
            vmax += 0.5 * dy

        if padding is None:
            padding = self.suggestPadding(axis)

        p = (vmax - vmin) * padding
        vmin -= p
        vmax += p
        return vmin, vmax

    def setXRange(self, vmin: float, vmax: float, *,
                  padding=None,
                  disable_auto_range: bool = True,
                  update: bool = True):
        if disable_auto_range:
            self.enableAutoRange(self.Axis.X, False)

        vmin, vmax = self._regularizeRange(vmin, vmax, self.Axis.X, padding)
        self._target_rect.setLeft(vmin)
        self._target_rect.setRight(vmax)

        self.updateViewRange()
        if update:
            self.updateAutoRange()
            self.updateMatrix()
            self.update()

        if self._border is not None:
            # Update target rect for debugging
            self._border.setRect(
                self.mapRectFromItem(self.childGroup, self.targetRect()))

    def setYRange(self, vmin: float, vmax: float, *,
                  padding=None,
                  disable_auto_range: bool = True,
                  update: bool = True):
        if disable_auto_range:
            self.enableAutoRange(self.Axis.Y, False)

        vmin, vmax = self._regularizeRange(vmin, vmax, self.Axis.Y, padding)
        self._target_rect.setTop(vmin)
        self._target_rect.setBottom(vmax)

        self.updateViewRange()
        if update:
            self.updateAutoRange()
            self.updateMatrix()
            self.update()

        if self._border is not None:
            # Update target rect for debugging
            self._border.setRect(
                self.mapRectFromItem(self.childGroup, self.targetRect()))

    def setRange(self, *args, padding=None, disable_auto_range: bool = True):
        if len(args) == 1:
            rect = args[0]
            xrange = (rect.left(), rect.right())
            # Caveat: y-axis pointing to the opposite direction of the
            #         y axis of a QRect
            yrange = (rect.top(), rect.bottom())
        else:
            xrange, yrange = args

        if disable_auto_range:
            self.enableAutoRange(self.Axis.XY, False)

        self.setXRange(xrange[0], xrange[1],
                       padding=padding, disable_auto_range=False, update=False)
        self.setYRange(yrange[0], yrange[1],
                       padding=padding, disable_auto_range=False, update=False)

        self.updateAutoRange()
        self.updateMatrix()
        self.update()

    def viewAll(self, disable_auto_range: bool = False) -> None:
        self.setRange(self.childrenBoundingRect(),
                      disable_auto_range=disable_auto_range)

    def suggestPadding(self, axis):
        l = self.geometry().width() if axis == self.Axis.X else self.geometry().height()
        if l > 0:
            return np.clip(1./(l**0.5), 0.02, 0.1)
        return 0.02

    def scaleBy(self, sx, sy, xc, yc):
        vr = self.targetRect()

        x0 = xc + (vr.left() - xc) * sx
        x1 = xc + (vr.right() - xc) * sx
        y0 = yc + (vr.top() - yc) * sy
        y1 = yc + (vr.bottom() - yc) * sy
        self.setRange((x0, x1), (y0, y1), padding=0)

    def enableAutoRange(self, axis: "ViewBox.Axis", enable: bool = True) -> None:
        if axis == self.Axis.X:
            axes = [0]
        elif axis == self.Axis.Y:
            axes = [1]
        else:
            axes = [0, 1]

        for ax in axes:
            if self._auto_range[ax] ^ enable:
                # If disabling, finish the previously scheduled autoRange.
                if not enable:
                    self.updateAutoRange()

                self._auto_range[ax] = enable

                if ax == 0:
                    self.auto_range_x_toggled_sgn.emit(enable)
                else:
                    self.auto_range_y_toggled_sgn.emit(enable)

    def updateAutoRange(self):
        if self._updating_range:
            return

        self._updating_range = True

        if self._auto_range[0] or self._auto_range[1]:
            self.setRange(
                self.childrenBoundingRect(), disable_auto_range=False)

        self._updating_range = False

    def setXLink(self, view: "ViewBox"):
        """Link this view's X axis to another view. (see LinkView)"""
        self.linkView(self.Axis.X, view)

    def setYLink(self, view: "ViewBox"):
        """Link this view's Y axis to another view. (see LinkView)"""
        self.linkView(self.Axis.Y, view)

    def linkView(self, axis, view):
        """
        Link X or Y axes of two views and unlink any previously connected axes. *axis* must be ViewBox.XAxis or ViewBox.YAxis.
        If view is None, the axis is left unlinked.
        """
        if axis == self.Axis.X:
            signal = 'x_range_changed_sgn'
            slot = self.linkedXChanged
        else:
            signal = 'y_range_changed_sgn'
            slot = self.linkedYChanged

        oldLink = self.linkedView(axis)
        if oldLink is not None:
            try:
                getattr(oldLink, signal).disconnect(slot)
                oldLink.resized_sgn.disconnect(slot)
            except (TypeError, RuntimeError):
                # This can occur if the view has been deleted already
                pass

        self._linked_views[axis] = weakref.ref(view)
        getattr(view, signal).connect(slot)
        view.resized_sgn.connect(slot)
        if view._auto_range[axis]:
            self.enableAutoRange(axis, False)
            slot()
        else:
            if not self._auto_range[axis]:
                slot()

    def linkedXChanged(self):
        view = self.linkedView(0)
        self.linkedViewChanged(view, self.Axis.X)

    def linkedYChanged(self):
        view = self.linkedView(1)
        self.linkedViewChanged(view, self.Axis.Y)

    def linkedView(self, ax):
        v = self._linked_views[ax]
        if v is None or isinstance(v, str):
            return
        return v()

    def linkedViewChanged(self, view, axis):
        if self._block_links or view is None:
            return

        vr = view.viewRect()
        vg = view.screenGeometry()
        sg = self.screenGeometry()
        if vg is None or sg is None:
            return

        view._block_links = True
        try:
            if axis == self.Axis.X:
                overlap = min(sg.right(), vg.right()) - max(sg.left(), vg.left())
                if overlap < min(vg.width()/3, sg.width()/3):  # if less than 1/3 of views overlap,
                                                               # then just replicate the view
                    x1 = vr.left()
                    x2 = vr.right()
                else:  # views overlap; line them up
                    upp = float(vr.width()) / vg.width()
                    if self._axis_inverted[0]:
                        x1 = vr.left() + (sg.right()-vg.right()) * upp
                    else:
                        x1 = vr.left() + (sg.x()-vg.x()) * upp
                    x2 = x1 + sg.width() * upp
                self.setXRange(x1, x2, padding=0, disable_auto_range=True)
            else:
                overlap = min(sg.bottom(), vg.bottom()) - max(sg.top(), vg.top())
                if overlap < min(vg.height()/3, sg.height()/3):  # if less than 1/3 of views overlap,
                                                                 # then just replicate the view
                    y1 = vr.top()
                    y2 = vr.bottom()
                else:  # views overlap; line them up
                    upp = float(vr.height()) / vg.height()
                    if self._axis_inverted[1]:
                        y2 = vr.bottom() + (sg.bottom()-vg.bottom()) * upp
                    else:
                        y2 = vr.bottom() + (sg.top()-vg.top()) * upp
                    y1 = y2 - sg.height() * upp
                self.setYRange(y1, y2, padding=0, disable_auto_range=True)
        finally:
            view._block_links = False

    def screenGeometry(self):
        """return the screen geometry of the viewbox"""
        v = self.getViewWidget()
        if v is None:
            return

        b = self.sceneBoundingRect()
        wr = v.mapFromScene(b).boundingRect()
        pos = v.mapToGlobal(v.pos())
        wr.adjust(pos.x(), pos.y(), pos.x(), pos.y())
        return wr

    def itemBoundsChanged(self):
        if self._auto_range[0] or self._auto_range[1]:
            self.updateAutoRange()
            self.updateMatrix()
            self.update()

    def _invertAxis(self, ax, inv):
        self._axis_inverted[ax] = inv
        self.updateViewRange()

        if ax:
            self.y_range_changed_sgn.emit()
        else:
            self.x_range_changed_sgn.emit()

    def invertY(self, b=True):
        self._invertAxis(1, b)

    def invertX(self, b=True):
        self._invertAxis(0, b)

    def childTransform(self) -> QTransform:
        self.updateMatrix()
        return self.childGroup.transform()

    def mapToView(self, obj):
        """Maps from the local coordinates of the ViewBox to the coordinate system displayed inside the ViewBox"""
        self.updateMatrix()
        m = fn.invertQTransform(self.childTransform())
        return m.map(obj)

    def mapFromView(self, obj):
        """Maps from the coordinate system displayed inside the ViewBox to the local coordinates of the ViewBox"""
        self.updateMatrix()
        m = self.childTransform()
        return m.map(obj)

    def mapSceneToView(self, obj):
        """Maps from scene coordinates to the coordinate system displayed inside the ViewBox"""
        self.updateMatrix()
        return self.mapToView(self.mapFromScene(obj))

    def mapViewToScene(self, obj):
        """Maps from the coordinate system displayed inside the ViewBox to scene coordinates"""
        self.updateMatrix()
        return self.mapToScene(self.mapFromView(obj))

    def mapFromItemToView(self, item, obj):
        """Maps *obj* from the local coordinate system of *item* to the view coordinates"""
        self.updateMatrix()
        return self.childGroup.mapFromItem(item, obj)

    def mapFromViewToItem(self, item, obj):
        """Maps *obj* from view coordinates to the local coordinate system of *item*."""
        self.updateMatrix()
        return self.childGroup.mapToItem(item, obj)

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent) -> None:
        """Override."""
        s = 1. + ev.delta() * self.WHEEL_SCALE_FACTOR
        # center = self.mapSceneToView(ev.pos())
        center = fn.invertQTransform(self.childGroup.transform()).map(ev.pos())

        self._target_rect = self._view_rect
        self.scaleBy(s, s, center.x(), center.y())
        ev.accept()

    def translateXBy(self, dx):
        vr = self.targetRect()
        self.setXRange(vr.left() + dx, vr.right() + dx)

    def translateYBy(self, dy):
        vr = self.targetRect()
        self.setYRange(vr.top() + dy, vr.bottom() + dy)

    def translateBy(self, dx, dy):
        vr = self.targetRect()
        xrange = (vr.left() + dx, vr.right() + dx)
        yrange = (vr.top() + dy, vr.bottom() + dy)
        self.setRange(xrange, yrange, padding=0)

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
                    self.setRange(rect.normalized())
                else:
                    rect = self.childGroup.mapRectFromParent(
                        QRectF(ev.buttonDownPos(), ev.pos()))
                    self._selected_rect.setPos(rect.topLeft())
                    self._selected_rect.resetTransform()
                    self._selected_rect.scale(rect.width(), rect.height())
                    if ev.entering():
                        self._selected_rect.show()
            else:
                tr = fn.invertQTransform(self.childGroup.transform())
                tr = tr.map(delta) - tr.map(QPointF(0, 0))

                self._target_rect = self._view_rect
                self.translateBy(tr.x(), tr.y())

            ev.accept()

    def childrenBoundingRect(self) -> QRectF:
        """Return the bounding rectangle of all children."""
        items = self._items

        bounding_rect = QRectF()
        for item in items:
            if not item.isVisible():
                continue

            rect = item.boundingRect()
            if rect.isNull():
                continue

            bounding_rect = bounding_rect.united(
                self.mapFromItemToView(item, rect).boundingRect())

        return bounding_rect

    def updateViewRange(self):
        self._view_rect = self._target_rect
        self.updateAutoRange()
        self.updateMatrix()
        self.update()

        # Inform linked views that the range has changed
        for ax in [0, 1]:
            link = self.linkedView(ax)
            if link is not None:
                link.linkedViewChanged(self, ax)

        # emit range change signals
        self.x_range_changed_sgn.emit()
        self.y_range_changed_sgn.emit()
        self.range_changed_sgn.emit(self, self._view_rect)

    def updateMatrix(self):
        """Update the childGroup's transform matrix."""
        bounds = self.rect()

        vr = self.viewRect()
        if vr.height() == 0 or vr.width() == 0:
            return

        x_scale, y_scale = bounds.width() / vr.width(), bounds.height() / vr.height()
        if not self._axis_inverted[1]:
            y_scale = -y_scale
        if self._axis_inverted[0]:
            x_scale = -x_scale

        m = QTransform()

        # First center the viewport at 0
        center = bounds.center()
        m.translate(center.x(), center.y())

        # Now scale and translate properly
        m.scale(x_scale, y_scale)
        st = vr.center()
        m.translate(-st.x(), -st.y())

        self.childGroup.setTransform(m)

        self.transform_changed_sgn.emit(self)

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos().toPoint())

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent):
        """Override."""
        self.linkedXChanged()
        self.linkedYChanged()

        self.updateViewRange()
        self.viewAll(disable_auto_range=False)
        self.updateMatrix()
        self.update()

        self.resized_sgn.emit(self)
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
