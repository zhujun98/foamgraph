import itertools
import operator
from typing import Any, Optional
import weakref

from ..backend import sip
from ..backend.QtCore import QRectF
from ..backend.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsWidget
)


class LRUCache:
    """
    This LRU cache should be reasonable for short collections (until around 100 items), as it does a
    sort on the items if the collection would become too big (so, it is very fast for getting and
    setting but when its size would become higher than the max size it does one sort based on the
    internal time to decide which items should be removed -- which should be Ok if the resizeTo
    isn't too close to the maxSize so that it becomes an operation that doesn't happen all the
    time).
    """

    def __init__(self, maxSize=100, resizeTo=70):
        '''
        ============== =========================================================
        **Arguments:**
        maxSize        (int) This is the maximum size of the cache. When some
                       item is added and the cache would become bigger than
                       this, it's resized to the value passed on resizeTo.
        resizeTo       (int) When a resize operation happens, this is the size
                       of the final cache.
        ============== =========================================================
        '''
        assert resizeTo < maxSize
        self.maxSize = maxSize
        self.resizeTo = resizeTo
        self._counter = 0
        self._dict = {}
        self._nextTime = itertools.count(0).__next__

    def __getitem__(self, key):
        item = self._dict[key]
        item[2] = self._nextTime()
        return item[1]

    def __len__(self):
        return len(self._dict)

    def __setitem__(self, key, value):
        item = self._dict.get(key)
        if item is None:
            if len(self._dict) + 1 > self.maxSize:
                self._resizeTo()

            item = [key, value, self._nextTime()]
            self._dict[key] = item
        else:
            item[1] = value
            item[2] = self._nextTime()

    def __delitem__(self, key):
        del self._dict[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        self._dict.clear()

    def values(self):
        return [i[1] for i in self._dict.values()]

    def keys(self):
        return [x[0] for x in self._dict.values()]

    def _resizeTo(self):
        ordered = sorted(self._dict.values(), key=operator.itemgetter(2))[:self.resizeTo]
        for i in ordered:
            del self._dict[i[0]]

    def items(self, accessTime=False):
        '''
        :param bool accessTime:
            If True sorts the returned items by the internal access time.
        '''
        if accessTime:
            for x in sorted(self._dict.values(), key=operator.itemgetter(2)):
                yield x[0], x[1]
        else:
            for x in self._dict.items():
                yield x[0], x[1]


class GraphicsItem:
    """Abstract class providing useful methods to GraphicsObject and GraphicsWidget.

    (This is required because we cannot have multiple inheritance with QObject subclasses.)

    A note about Qt's GraphicsView framework:

    The GraphicsView system places a lot of emphasis on the notion that the graphics within
    the scene should be device independent--you should be able to take the same graphics and
    display them on screens of different resolutions, printers, export to SVG, etc.

    This is nice in principle, but causes me a lot of headache in practice. It means that
    I have to circumvent all the device-independent expectations any time I want to operate
    in pixel coordinates rather than arbitrary scene coordinates.

    A lot of the code in GraphicsItem is devoted to this task--keeping track of view widgets
    and device transforms, computing the size and shape of a pixel in local item coordinates,
    etc. Note that in item coordinates, a pixel does not have to be square or even rectangular,
    so just asking how to increase a bounding rect by 2px can be a rather complex task.
    """
    _mapRectFromViewGlobalCache = LRUCache(100, 70)

    def __init__(self):
        if not hasattr(self, '_qtBaseClass'):
            for b in self.__class__.__bases__:
                if issubclass(b, QGraphicsItem):
                    self.__class__._qtBaseClass = b
                    break
        if not hasattr(self, '_qtBaseClass'):
            raise Exception('Could not determine Qt base class for GraphicsItem: %s' % str(self))

        self._pixelVectorCache = [None, None]
        self._viewWidget = None
        self._vb = None
        self._connectedView = None
        self._cachedView = None

    def getViewWidget(self):
        """
        Return the view widget for this item.

        If the scene has multiple views, only the first view is returned.
        The return value is cached; clear the cached value with forgetViewWidget().
        If the view has been deleted by Qt, return None.
        """
        if self._viewWidget is None:
            scene = self.scene()
            if scene is None:
                return
            views = scene.views()
            if len(views) < 1:
                return
            self._viewWidget = weakref.ref(self.scene().views()[0])

        v = self._viewWidget()
        if v is not None and sip.isdeleted(v):
            return

        return v

    def canvas(self):
        from ..graphics_widget import Canvas

        if self._vb is None:
            parent = self
            while parent is not None:
                parent = parent.parentItem()
                if isinstance(parent, Canvas):
                    self._vb = parent
                    break

        return self._vb

    def deviceTransform(self):
        """
        Return the transform that converts local item coordinates to device coordinates (usually pixels).
        Extends deviceTransform to automatically determine the viewportTransform.
        """
        view = self.getViewWidget()
        if view is None:
            return
        viewportTransform = view.viewportTransform()
        dt = self._qtBaseClass.deviceTransform(self, viewportTransform)

        if dt.determinant() == 0:  # occurs when deviceTransform is invalid because widget has not been displayed
            return None
        return dt

    def viewTransform(self):
        """Return the transform that maps from local coordinates to the item's Canvas coordinates
        If there is no Canvas, return the scene transform.
        Returns None if the item does not have a view."""
        canvas = self.canvas()
        if canvas is None:
            return

        tr = self.itemTransform(canvas._proxy)
        if isinstance(tr, tuple):
            tr = tr[0]   # difference between pyside and pyqt
        return tr
    
    def viewRect(self) -> Optional[QRectF]:
        """Return the visible bounds of this item's Canvas.

        in the local coordinate system of the item."""
        canvas = self.canvas()
        if canvas is None:
            return QRectF()

        rect = self.mapRectFromView(canvas.viewRect())
        return rect.normalized()

    def mapToDevice(self, obj):
        """
        Return *obj* mapped from local coordinates to device coordinates (pixels).
        If there is no device mapping available, return None.
        """
        vt = self.deviceTransform()
        if vt is None:
            return None
        return vt.map(obj)

    def mapRectFromView(self, obj) -> QRectF:
        vt = self.viewTransform()
        if vt is None:
            return QRectF

        cache = self._mapRectFromViewGlobalCache
        k = (
            vt.m11(), vt.m12(), vt.m13(),
            vt.m21(), vt.m22(), vt.m23(),
            vt.m31(), vt.m32(), vt.m33(),
        )

        try:
            inv_vt = cache[k]
        except KeyError:
            inv_vt = vt.inverted()[0]
            cache[k] = inv_vt

        return inv_vt.mapRect(obj)

    def pos(self):
        return self._qtBaseClass.pos(self)
        
    def informViewBoundsChanged(self):
        """
        Inform this item's container Canvas that the bounds of this item have changed.
        This is used by Canvas to react if auto-range is enabled.
        """
        canvas = self.canvas()
        if canvas is not None:
            canvas.updateAutoRange()

    def itemChange(self, change, value) -> Any:
        """Override."""
        ret = super().itemChange(change, value)

        if change in [self.GraphicsItemChange.ItemPositionHasChanged,
                      self.GraphicsItemChange.ItemTransformHasChanged]:
            self.informViewBoundsChanged()

        return ret


class GraphicsObject(GraphicsItem, QGraphicsObject):
    """Extension of QGraphicsObject with some useful methods.

    """
    _qtBaseClass = QGraphicsObject

    def __init__(self, *args, **kwargs):
        QGraphicsObject.__init__(self, *args, **kwargs)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges)
        GraphicsItem.__init__(self)
