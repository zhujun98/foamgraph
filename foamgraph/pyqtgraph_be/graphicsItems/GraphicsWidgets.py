from ...backend.QtWidgets import QGraphicsItem, QGraphicsWidget

from .GraphicsItem import GraphicsItem


class GraphicsWidget(GraphicsItem, QGraphicsWidget):
    
    _qtBaseClass = QGraphicsWidget

    def __init__(self, parent: QGraphicsItem = None, **kwargs):
        QGraphicsWidget.__init__(self, parent=parent, **kwargs)
        GraphicsItem.__init__(self)
