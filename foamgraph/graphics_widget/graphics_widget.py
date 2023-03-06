from ..backend.QtWidgets import QGraphicsItem, QGraphicsWidget
from ..graphics_item import GraphicsItem


class GraphicsWidget(GraphicsItem, QGraphicsWidget):
    _qtBaseClass = QGraphicsWidget

    CONTENT_MARGIN = (5, 5, 5, 5)

    def __init__(self, parent: QGraphicsItem = None, **kwargs):
        QGraphicsWidget.__init__(self, parent=parent, **kwargs)
        GraphicsItem.__init__(self)