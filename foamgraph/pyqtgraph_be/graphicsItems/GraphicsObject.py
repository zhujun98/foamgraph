from ..Qt import QT_LIB
from ...backend.QtWidgets import QGraphicsItem, QGraphicsObject
if QT_LIB in ['PyQt5']:
    import sip
from .GraphicsItem import GraphicsItem

__all__ = ['GraphicsObject']


class GraphicsObject(GraphicsItem, QGraphicsObject):
    """Extension of QGraphicsObject with some useful methods.

    """
    _qtBaseClass = QGraphicsObject

    def __init__(self, *args, **kwargs):
        self.__inform_view_on_changes = True
        QGraphicsObject.__init__(self, *args, **kwargs)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges)
        GraphicsItem.__init__(self)
        
    def itemChange(self, change, value):
        ret = QGraphicsObject.itemChange(self, change, value)
        if change in [self.GraphicsItemChange.ItemParentHasChanged,
                      self.GraphicsItemChange.ItemSceneHasChanged]:
            self.parentChanged()
        try:
            inform_view_on_change = self.__inform_view_on_changes
        except AttributeError:
            # It's possible that the attribute was already collected when the itemChange happened
            # (if it was triggered during the gc of the object).
            pass
        else:
            if inform_view_on_change and change in [self.GraphicsItemChange.ItemPositionHasChanged,
                                                    self.GraphicsItemChange.ItemTransformHasChanged]:
                self.informViewBoundsChanged()
            
        # workaround for pyqt bug:
        # http://www.riverbankcomputing.com/pipermail/pyqt/2012-August/031818.html
        if QT_LIB in ['PyQt5'] and change == self.ItemParentChange and isinstance(ret, QGraphicsItem):
            ret = sip.cast(ret, QGraphicsItem)

        return ret
