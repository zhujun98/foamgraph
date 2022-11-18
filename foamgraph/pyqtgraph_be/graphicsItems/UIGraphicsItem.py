from ..Qt import QtGui, QtCore, QT_LIB
from .GraphicsObject import GraphicsObject
if QT_LIB in ['PyQt5']:
    import sip

from ..Point import Point

__all__ = ['UIGraphicsItem']


class UIGraphicsItem(GraphicsObject):
    """Base class for graphics items with boundaries relative to a GraphicsView or ViewBox.

    The purpose of this class is to allow the creation of GraphicsItems which live inside 
    a scalable view, but whose boundaries will always stay fixed relative to the view's boundaries.
    For example: GridItem, InfiniteLine
    
    The view can be specified on initialization or it can be automatically detected when the item is painted.
    
    NOTE: Only the item's boundingRect is affected; the item is not transformed in any way. Use viewRangeChanged
    to respond to changes in the view.
    """
    # TODO: make parent the first argument
    def __init__(self, bounds=None, parent=None):
        """
        ============== =============================================================================
        **Arguments:**
        bounds         QRectF with coordinates relative to view box. The default is QRectF(0,0,1,1),
                       which means the item will have the same bounds as the view.
        ============== =============================================================================
        """
        super().__init__(parent=parent)
        self.setFlag(self.GraphicsItemFlag.ItemSendsScenePositionChanges)
            
        if bounds is None:
            self._bounds = QtCore.QRectF(0, 0, 1, 1)
        else:
            self._bounds = bounds
            
        self._boundingRect = None
        self._updateView()
    
    def itemChange(self, change, value):
        ret = super().itemChange(change, value)

        # workaround for pyqt bug:
        # http://www.riverbankcomputing.com/pipermail/pyqt/2012-August/031818.html
        if QT_LIB in ['PyQt5'] and change == self.ItemParentChange and isinstance(ret, QtGui.QGraphicsItem):
            ret = sip.cast(ret, QtGui.QGraphicsItem)
        
        if change == self.GraphicsItemChange.ItemScenePositionHasChanged:
            self.setNewBounds()
        return ret

    def boundingRect(self):
        """Override."""
        if self._boundingRect is None:
            br = self.viewRect()
            if br is None:
                return QtCore.QRectF()
            self._boundingRect = br
        return QtCore.QRectF(self._boundingRect)
    
    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        """Called by ViewBox for determining the auto-range bounds.
        By default, UIGraphicsItems are excluded from autoRange."""
        return None

    def viewRangeChanged(self):
        """Called when the view widget/viewbox is resized/rescaled"""
        self.setNewBounds()
        self.update()
        
    def setNewBounds(self):
        """Update the item's bounding rect to match the viewport"""
        self._boundingRect = None  # invalidate bounding rect, regenerate later if needed.
        self.prepareGeometryChange()

    def setPos(self, pos: Point):
        """Override."""
        super().setPos(pos)
        self.setNewBounds()
