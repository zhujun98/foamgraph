from ...backend.QtWidgets import QGraphicsWidget

from .GraphicsItem import GraphicsItem

__all__ = ['GraphicsWidget']


class GraphicsWidget(GraphicsItem, QGraphicsWidget):
    
    _qtBaseClass = QGraphicsWidget

    def __init__(self, *args, **kargs):
        QGraphicsWidget.__init__(self, *args, **kargs)
        GraphicsItem.__init__(self)
