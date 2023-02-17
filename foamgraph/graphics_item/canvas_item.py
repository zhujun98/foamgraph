from enum import Enum
import weakref

import numpy as np

from foamgraph.backend.QtWidgets import (
    QGraphicsRectItem, QHBoxLayout, QLabel, QMenu, QWidget, QWidgetAction
)
from foamgraph.backend.QtCore import pyqtSignal, QRectF, Qt
from foamgraph.backend.QtGui import (
    QAction, QActionGroup, QDoubleValidator, QGraphicsSceneWheelEvent,
    QSizePolicy, QTransform
)

from foamgraph.pyqtgraph_be import functions as fn
from foamgraph.pyqtgraph_be.Point import Point

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
    transform_changed_sgn = pyqtSignal(object)
    resized_sgn = pyqtSignal(object)

    cross_cursor_toggled_sgn = pyqtSignal(bool)

    class MouseMode(Enum):
        Pan = 3
        Rect = 1

    class Axis:
        X = 0
        Y = 1
        XY = 2

    # for linking views together
    NamedViews = weakref.WeakValueDictionary()   # name: ViewBox

    WHEEL_SCALE_FACTOR = 0.00125

    def __init__(self, parent=None, *, image: bool = False, debug: bool = True):
        """Initialization."""
        super().__init__(parent)

        self._block_links = False

        self._items = []
        self._matrixNeedsUpdate = True  # indicates that range has changed, but matrix update was deferred
        self._autoRangeNeedsUpdate = True # indicates auto-range needs to be recomputed.

        self._axis_inverted = [False, False]
        self._auto_range = [True, True]

        # separating targetRange and viewRange allows the view to be resized
        # while keeping all previously viewed contents visible
        self._view_range = [[0, 1], [0, 1]]  # actual range viewed
        self._target_range = [[0, 1], [0, 1]]
        self.state = {
            'linkedViews': [None, None],  # may be None, "viewName", or weakref.ref(view)
                                          # a name string indicates that the view *should* link to another, but no view with that name exists yet.

            # Limits
            'limits': {
                'xLimits': [None, None],   # Maximum and minimum visible X values
                'yLimits': [None, None],   # Maximum and minimum visible Y values
                'xRange': [None, None],   # Maximum and minimum X range
                'yRange': [None, None],   # Maximum and minimum Y range
                }

        }

        self._mouse_mode = self.MouseMode.Pan

        self._updatingRange = False  # Used to break recursive loops. See updateAutoRange.
        self._itemBoundsCache = weakref.WeakKeyDictionary()

        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)
        self.setFlag(self.GraphicsItemFlag.ItemIsFocusable, True)  ## so we can receive key presses

        # childGroup is required so that ViewBox has local coordinates similar to device coordinates.
        # this is a workaround for a Qt + OpenGL bug that causes improper clipping
        # https://bugreports.qt.nokia.com/browse/QTBUG-23723
        self.childGroup = ChildGroup(self)
        self.childGroup.itemsChangedListeners.append(self)

        # Make scale box that is shown when dragging on the view
        self.rbScaleBox = QGraphicsRectItem(0, 0, 1, 1)
        self.rbScaleBox.setPen(FColor.mkPen('Gold'))
        self.rbScaleBox.setBrush(FColor.mkBrush('Gold', alpha=100))
        self.rbScaleBox.setZValue(1e9)
        self.rbScaleBox.hide()
        self.addItem(self.rbScaleBox, ignore_bounds=True)

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
        action.triggered.connect(self.autoRange)

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

    def update(self, *args, **kwargs):
        self.prepareForPaint()
        GraphicsWidget.update(self, *args, **kwargs)

    def prepareForPaint(self):
        # don't check whether auto range is enabled here--only check when setting dirty flag.
        if self._autoRangeNeedsUpdate: # and autoRangeEnabled:
            self.updateAutoRange()
        self.updateMatrix()

    def setMouseMode(self, mode: "ViewBox.MouseMode"):
        self._mouse_mode = mode

    def addItem(self, item, ignore_bounds: bool = False):
        """Add a QGraphicsItem to this view.

        The view will include this item when determining how to set its range
        automatically unless *ignoreBounds* is True.
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
        try:
            self._items.remove(item)
        except:
            pass

        scene = self.scene()
        if scene is not None:
            scene.removeItem(item)
        item.setParentItem(None)

        self.updateAutoRange()

    def resizeEvent(self, ev):
        self._matrixNeedsUpdate = True
        self.updateMatrix()

        self.linkedXChanged()
        self.linkedYChanged()

        self.updateAutoRange()
        self.updateViewRange()

        self._matrixNeedsUpdate = True
        self.updateMatrix()

        self.resized_sgn.emit(self)
        self.childGroup.prepareGeometryChange()

    def viewRange(self):
        """Return a the view's visible range as a list: [[xmin, xmax], [ymin, ymax]]"""
        return [x[:] for x in self._view_range]  # return copy

    def viewRect(self):
        """Return a QRectF bounding the region visible within the ViewBox"""
        vr0 = self._view_range[0]
        vr1 = self._view_range[1]
        return QRectF(vr0[0], vr1[0], vr0[1]-vr0[0], vr1[1] - vr1[0])

    def targetRect(self):
        """
        Return the region which has been requested to be visible.
        (this is not necessarily the same as the region that is *actually* visible--
        resizing and aspect ratio constraints can cause targetRect() and viewRect() to differ)
        """
        tr0, tr1 = self._target_range
        return QRectF(tr0[0], tr1[0], tr0[1]-tr0[0], tr1[1] - tr1[0])

    def _resetTarget(self):
        # Reset target range to exactly match current view range.
        # This is used during mouse interaction to prevent unpredictable
        # behavior (because the user is unaware of targetRange).
        self._target_range = [self._view_range[0][:], self._view_range[1][:]]

    def setRange(self, rect=None, xRange=None, yRange=None, update=True, padding=None, disableAutoRange=True):
        """
        Set the visible range of the ViewBox.
        Must specify at least one of *rect*, *xRange*, or *yRange*.

        ================== =====================================================================
        **Arguments:**
        *rect*             (QRectF) The full range that should be visible in the view box.
        *xRange*           (min,max) The range that should be visible along the x-axis.
        *yRange*           (min,max) The range that should be visible along the y-axis.
        *disableAutoRange* (bool) If True, auto-ranging is diabled. Otherwise, it is left
                           unchanged.
        ================== =====================================================================

        """
        changes = {}   # axes
        setRequested = [False, False]

        if rect is not None:
            changes = {0: [rect.left(), rect.right()], 1: [rect.top(), rect.bottom()]}
            setRequested = [True, True]
        if xRange is not None:
            changes[0] = xRange
            setRequested[0] = True
        if yRange is not None:
            changes[1] = yRange
            setRequested[1] = True

        if len(changes) == 0:
            raise Exception("Must specify at least one of rect, xRange, or yRange. (gave rect=%s)" % str(type(rect)))

        # Update axes one at a time
        changed = [False, False]

        # Disable auto-range for each axis that was requested to be set
        if disableAutoRange:
            xOff = False if setRequested[0] else None
            yOff = False if setRequested[1] else None
            self.enableAutoRange(x=xOff, y=yOff)
            changed.append(True)

        limits = (self.state['limits']['xLimits'], self.state['limits']['yLimits'])
        minRng = [self.state['limits']['xRange'][0], self.state['limits']['yRange'][0]]
        maxRng = [self.state['limits']['xRange'][1], self.state['limits']['yRange'][1]]

        for ax, range in changes.items():
            mn = min(range)
            mx = max(range)

            # If we requested 0 range, try to preserve previous scale.
            # Otherwise just pick an arbitrary scale.
            if mn == mx:
                dy = self._view_range[ax][1] - self._view_range[ax][0]
                if dy == 0:
                    dy = 1
                mn -= dy*0.5
                mx += dy*0.5

            # Make sure no nan/inf get through
            if not all(np.isfinite([mn, mx])):
                raise Exception("Cannot set range [%s, %s]" % (str(mn), str(mx)))

            # Apply padding
            if padding is None:
                xpad = self.suggestPadding(ax)
            else:
                xpad = padding
            p = (mx-mn) * xpad
            mn -= p
            mx += p

            # max range cannot be larger than bounds, if they are given
            if limits[ax][0] is not None and limits[ax][1] is not None:
                if maxRng[ax] is not None:
                    maxRng[ax] = min(maxRng[ax], limits[ax][1] - limits[ax][0])
                else:
                    maxRng[ax] = limits[ax][1] - limits[ax][0]

            # If we have limits, we will have at least a max range as well
            if maxRng[ax] is not None or minRng[ax] is not None:
                diff = mx - mn
                if maxRng[ax] is not None and diff > maxRng[ax]:
                    delta = maxRng[ax] - diff
                elif minRng[ax] is not None and diff < minRng[ax]:
                    delta = minRng[ax] - diff
                else:
                    delta = 0

                mn -= delta / 2.
                mx += delta / 2.

            # Make sure our requested area is within limits, if any
            if limits[ax][0] is not None or limits[ax][1] is not None:
                lmn, lmx = limits[ax]
                if lmn is not None and mn < lmn:
                    delta = lmn - mn  # Shift the requested view to match our lower limit
                    mn = lmn
                    mx += delta
                elif lmx is not None and mx > lmx:
                    delta = lmx - mx
                    mx = lmx
                    mn += delta

            # Set target range
            if self._target_range[ax] != [mn, mx]:
                self._target_range[ax] = [mn, mx]
                changed[ax] = True

        # Update viewRange to match targetRange as closely as possible while
        # accounting for aspect ratio constraint
        lockX, lockY = setRequested
        if lockX and lockY:
            lockX = False
            lockY = False
        self.updateViewRange(lockX, lockY)

        # If nothing has changed, we are done.
        if any(changed):
            # Update target rect for debugging
            if self._border is not None:
                self._border.setRect(self.mapRectFromItem(self.childGroup, self.targetRect()))

            # If ortho axes have auto-visible-only, update them now
            # Note that aspect ratio constraints and auto-visible probably do not work together..
            if changed[0] and self._auto_range[0]:
                self._autoRangeNeedsUpdate = True
            elif changed[1] and self._auto_range[1]:
                self._autoRangeNeedsUpdate = True

    def setYRange(self, min, max, padding=None, update=True):
        """
        Set the visible Y range of the view to [*min*, *max*].
        The *padding* argument causes the range to be set larger by the fraction specified.
        (by default, this value is between 0.02 and 0.1 depending on the size of the ViewBox)
        """
        self.setRange(yRange=[min, max], update=update, padding=padding)

    def setXRange(self, min, max, padding=None, update=True):
        """
        Set the visible X range of the view to [*min*, *max*].
        The *padding* argument causes the range to be set larger by the fraction specified.
        (by default, this value is between 0.02 and 0.1 depending on the size of the ViewBox)
        """
        self.setRange(xRange=[min, max], update=update, padding=padding)

    def autoRange(self, disableAutoRange=True):
        """
        Set the range of the view box to make all children visible.
        Note that this is not the same as enableAutoRange, which causes the view to
        automatically auto-range whenever its contents are changed.
        """
        range = self.childrenBounds()
        bounds = QRectF(range[0][0], range[1][0], range[0][1]-range[0][0], range[1][1]-range[1][0])
        self.setRange(bounds, disableAutoRange=disableAutoRange)

    def suggestPadding(self, axis):
        l = self.geometry().width() if axis == 0 else self.geometry().height()
        if l > 0:
            return np.clip(1./(l**0.5), 0.02, 0.1)
        return 0.02

    def scaleBy(self, s, center):
        """
        Scale by *s* around given center point (or center of view).
        *s* may be a Point or tuple (x, y).
        """
        scale = Point(s)

        vr = self.targetRect()
        center = Point(center)

        tl = center + (vr.topLeft() - center) * scale
        br = center + (vr.bottomRight() - center) * scale

        # if not affect[0]:
        #     self.setYRange(tl.y(), br.y(), padding=0)
        # elif not affect[1]:
        #     self.setXRange(tl.x(), br.x(), padding=0)
        # else:
        self.setRange(QRectF(tl, br), padding=0)

    def translateBy(self, t=None, x=None, y=None):
        """
        Translate the view by *t*, which may be a Point or tuple (x, y).

        Alternately, x or y may be specified independently, leaving the other
        axis unchanged (note that using a translation of 0 may still cause
        small changes due to floating-point error).
        """
        vr = self.targetRect()
        if t is not None:
            t = Point(t)
            self.setRange(vr.translated(t), padding=0)
        else:
            if x is not None:
                x = vr.left()+x, vr.right()+x
            if y is not None:
                y = vr.top()+y, vr.bottom()+y
            if x is not None or y is not None:
                self.setRange(xRange=x, yRange=y, padding=0)

    def enableAutoRange(self, axis=None, enable=True, x=None, y=None):
        """
        Enable (or disable) auto-range for *axis*, which may be ViewBox.XAxis, ViewBox.YAxis, or ViewBox.XYAxes for both
        (if *axis* is omitted, both axes will be changed).
        When enabled, the axis will automatically rescale when items are added/removed or change their shape.
        The argument *enable* may optionally be a float (0.0-1.0) which indicates the fraction of the data that should
        be visible (this only works with items implementing a dataRange method, such as PlotDataItem).
        """
        # support simpler interface:
        if x is not None or y is not None:
            if x is not None:
                self.enableAutoRange(self.Axis.X, x)
            if y is not None:
                self.enableAutoRange(self.Axis.Y, y)
            return

        if axis == self.Axis.X or axis == 'x':
            axes = [0]
        elif axis == self.Axis.Y or axis == 'y':
            axes = [1]
        else:
            axes = [0, 1]

        for ax in axes:
            if self._auto_range[ax] != enable:
                # If we are disabling, do one last auto-range to make sure that
                # previously scheduled auto-range changes are enacted
                if not enable and self._autoRangeNeedsUpdate:
                    self.updateAutoRange()

                self._auto_range[ax] = enable
                self._autoRangeNeedsUpdate |= enable
                self.update()

    def disableAutoRange(self, axis=None):
        """Disables auto-range. (See enableAutoRange)"""
        self.enableAutoRange(axis, enable=False)

    def updateAutoRange(self):
        # Break recursive loops when auto-ranging.
        # This is needed because some items change their size in response
        # to a view change.
        if self._updatingRange:
            return

        self._updatingRange = True
        try:
            targetRect = self.viewRange()
            if not self._auto_range[0] and not self._auto_range[1]:
                return

            order = [1,0]

            args = {}
            for ax in order:
                if not self._auto_range[ax]:
                    continue

                oRange = [None, None]
                oRange[ax] = targetRect[1-ax]
                childRange = self.childrenBounds(orthoRange=oRange)

                # Make corrections to range
                xr = childRange[ax]
                if xr is not None:
                    padding = self.suggestPadding(ax)
                    wp = (xr[1] - xr[0]) * padding
                    childRange[ax][0] -= wp
                    childRange[ax][1] += wp
                    targetRect[ax] = childRange[ax]
                    args['xRange' if ax == 0 else 'yRange'] = targetRect[ax]

            # check for and ignore bad ranges
            for k in ['xRange', 'yRange']:
                if k in args:
                    if not np.all(np.isfinite(args[k])):
                        args.pop(k)

            if len(args) == 0:
                return
            args['padding'] = 0
            args['disableAutoRange'] = False

            self.setRange(**args)
        finally:
            self._autoRangeNeedsUpdate = False
            self._updatingRange = False

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

        self.state['linkedViews'][axis] = weakref.ref(view)
        getattr(view, signal).connect(slot)
        view.resized_sgn.connect(slot)
        if view._auto_range[axis]:
            self.enableAutoRange(axis, False)
            slot()
        else:
            if not self._auto_range[axis]:
                slot()

    def linkedXChanged(self):
        # called when x range of linked view has changed
        view = self.linkedView(0)
        self.linkedViewChanged(view, self.Axis.X)

    def linkedYChanged(self):
        # called when y range of linked view has changed
        view = self.linkedView(1)
        self.linkedViewChanged(view, self.Axis.Y)

    def linkedView(self, ax):
        # Return the linked view for axis *ax*.
        # this method _always_ returns either a ViewBox or None.
        v = self.state['linkedViews'][ax]
        if v is None or isinstance(v, str):
            return None
        else:
            return v()  # dereference weakref pointer. If the reference is dead, this returns None

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
                self.enableAutoRange(self.Axis.X, False)
                self.setXRange(x1, x2, padding=0)
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
                self.enableAutoRange(self.Axis.Y, False)
                self.setYRange(y1, y2, padding=0)
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
        wr.adjust(pos.x(), pos.y(), pos.x() , pos.y())
        return wr

    def itemBoundsChanged(self, item):
        self._itemBoundsCache.pop(item, None)
        if self._auto_range[0] or self._auto_range[1]:
            self._autoRangeNeedsUpdate = True
            self.update()

    def _invertAxis(self, ax, inv):
        self._axis_inverted[ax] = inv
        self._matrixNeedsUpdate = True  # updateViewRange won't detect this for us
        self.updateViewRange()
        self.update()
        if ax:
            self.y_range_changed_sgn.emit()
        else:
            self.x_range_changed_sgn.emit()

    def invertY(self, b=True):
        self._invertAxis(1, b)

    def invertX(self, b=True):
        self._invertAxis(0, b)

    def childTransform(self):
        """
        Return the transform that maps from child(item in the childGroup) coordinates to local coordinates.
        (This maps from inside the viewbox to outside)
        """
        self.updateMatrix()
        m = self.childGroup.transform()
        return m

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
        center = Point(fn.invertQTransform(self.childGroup.transform()).map(ev.pos()))

        self._resetTarget()
        self.scaleBy((s, s), center)
        ev.accept()

    def mouseDragEvent(self, ev: MouseDragEvent):
        ev.accept()  # we accept all buttons

        pos = ev.pos()
        delta = ev.lastPos() - pos

        # Scale or translate based on mouse button
        if ev.button() & Qt.MouseButton.LeftButton:
            if self._mouse_mode == self.MouseMode.Rect:
                if ev.exiting():  # This is the final move in the drag; change the view scale now
                    self.rbScaleBox.hide()
                    ax = QRectF(Point(ev.buttonDownPos(ev.button())), Point(pos))
                    ax = self.childGroup.mapRectFromParent(ax)
                    self.setRange(ax.normalized())
                else:
                    # update shape of scale box
                    self.updateScaleBox(ev.buttonDownPos(), ev.pos())
            else:
                tr = fn.invertQTransform(self.childGroup.transform())
                tr = tr.map(delta) - tr.map(Point(0, 0))

                x = tr.x()
                y = tr.y()

                self._resetTarget()
                if x is not None or y is not None:
                    self.translateBy(x=x, y=y)

    def updateScaleBox(self, p1, p2):
        r = QRectF(p1, p2)
        r = self.childGroup.mapRectFromParent(r)
        self.rbScaleBox.setPos(r.topLeft())
        self.rbScaleBox.resetTransform()
        self.rbScaleBox.scale(r.width(), r.height())
        self.rbScaleBox.show()

    def childrenBounds(self, orthoRange=(None,None)):
        """Return the bounding range of all children.
        [[xmin, xmax], [ymin, ymax]]
        Values may be None if there are no specific bounds for an axis.
        """
        items = self._items

        # First collect all boundary information
        itemBounds = []
        for item in items:
            if not item.isVisible() or not item.scene() is self.scene():
                continue

            # FIXME: EXtra-foam patch start
            if item.boundingRect().isEmpty():
                continue
            # FIXME: EXtra-foam patch end

            if item.flags() & item.GraphicsItemFlag.ItemHasNoContents:
                continue
            else:
                bounds = item.boundingRect()
            bounds = self.mapFromItemToView(item, bounds).boundingRect()
            itemBounds.append((bounds, True, True, 0))

        # determine tentative new range
        range = [None, None]
        for bounds, useX, useY, px in itemBounds:
            if useY:
                if range[1] is not None:
                    range[1] = [min(bounds.top(), range[1][0]), max(bounds.bottom(), range[1][1])]
                else:
                    range[1] = [bounds.top(), bounds.bottom()]
            if useX:
                if range[0] is not None:
                    range[0] = [min(bounds.left(), range[0][0]), max(bounds.right(), range[0][1])]
                else:
                    range[0] = [bounds.left(), bounds.right()]

        # Now expand any bounds that have a pixel margin
        # This must be done _after_ we have a good estimate of the new range
        # to ensure that the pixel size is roughly accurate.
        w, h = self.geometry().width(), self.geometry().height()
        if w > 0 and range[0] is not None:
            pxSize = (range[0][1] - range[0][0]) / w
            for bounds, useX, useY, px in itemBounds:
                if px == 0 or not useX:
                    continue
                range[0][0] = min(range[0][0], bounds.left() - px*pxSize)
                range[0][1] = max(range[0][1], bounds.right() + px*pxSize)
        if h > 0 and range[1] is not None:
            pxSize = (range[1][1] - range[1][0]) / h
            for bounds, useX, useY, px in itemBounds:
                if px == 0 or not useY:
                    continue
                range[1][0] = min(range[1][0], bounds.top() - px*pxSize)
                range[1][1] = max(range[1][1], bounds.bottom() + px*pxSize)

        return range

    def updateViewRange(self, forceX=False, forceY=False):
        # Update viewRange to match targetRange as closely as possible, given
        # aspect ratio constraints. The *force* arguments are used to indicate
        # which axis (if any) should be unchanged when applying constraints.
        viewRange = [self._target_range[0][:], self._target_range[1][:]]

        limits = (self.state['limits']['xLimits'], self.state['limits']['yLimits'])
        minRng = [self.state['limits']['xRange'][0], self.state['limits']['yRange'][0]]
        maxRng = [self.state['limits']['xRange'][1], self.state['limits']['yRange'][1]]

        for axis in [0, 1]:
            if limits[axis][0] is None and limits[axis][1] is None and minRng[axis] is None and maxRng[axis] is None:
                continue

            # max range cannot be larger than bounds, if they are given
            if limits[axis][0] is not None and limits[axis][1] is not None:
                if maxRng[axis] is not None:
                    maxRng[axis] = min(maxRng[axis], limits[axis][1] - limits[axis][0])
                else:
                    maxRng[axis] = limits[axis][1] - limits[axis][0]

        changed = [
            (viewRange[i][0] != self._view_range[i][0])
            or (viewRange[i][1] != self._view_range[i][1])
            for i in (0, 1)]
        self._view_range = viewRange

        if any(changed):
            self._matrixNeedsUpdate = True
            self.update()

            # Inform linked views that the range has changed
            for ax in [0, 1]:
                if not changed[ax]:
                    continue
                link = self.linkedView(ax)
                if link is not None:
                    link.linkedViewChanged(self, ax)

            # emit range change signals
            if changed[0]:
                self.x_range_changed_sgn.emit()
            if changed[1]:
                self.y_range_changed_sgn.emit()
            self.range_changed_sgn.emit(self, self._view_range)

    def updateMatrix(self, changed=None):
        if not self._matrixNeedsUpdate:
            return
        # Make the childGroup's transform match the requested viewRange.
        bounds = self.rect()

        vr = self.viewRect()
        if vr.height() == 0 or vr.width() == 0:
            return
        scale = Point(bounds.width() / vr.width(), bounds.height() / vr.height())
        if not self._axis_inverted[1]:
            scale = scale * Point(1, -1)
        if self._axis_inverted[0]:
            scale = scale * Point(-1, 1)
        m = QTransform()

        # First center the viewport at 0
        center = bounds.center()
        m.translate(center.x(), center.y())

        # Now scale and translate properly
        m.scale(scale[0], scale[1])
        st = Point(vr.center())
        m.translate(-st[0], -st[1])

        self.childGroup.setTransform(m)
        self._matrixNeedsUpdate = False

        self.transform_changed_sgn.emit(self)  # segfaults here: 1

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos().toPoint())

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
