from .backend.QtCore import pyqtSignal, QPoint, QRectF, Qt
from .backend.QtGui import (
    QKeyEvent, QMouseEvent, QPalette, QPainter, QPaintEvent
)
from .backend.QtWidgets import (
    QFrame, QGraphicsGridLayout, QGraphicsView, QGraphicsWidget, QWidget
)
from .pyqtgraph_be.Point import Point

from .aesthetics import FColor
from .graphics_scene import GraphicsScene


class GraphicsView(QGraphicsView):
    """Re-implementation of QGraphicsView that allows unambiguous control of the
    viewed coordinate range. Also automatically creates a GraphicsScene and a central QGraphicsWidget
    that is automatically scaled to the full view geometry.

    By default, the view coordinate system matches the widget's pixel coordinates and 
    automatically updates when the view is resized. This can be overridden by setting 
    autoPixelRange=False. The exact visible range can be set with setRange().
    """
    
    device_range_changed_sgn = pyqtSignal(object, object)
    device_transform_changed_sgn = pyqtSignal(object)
    scale_changed_sgn = pyqtSignal(object)

    def __init__(self, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self.setScene(GraphicsScene(parent=self))

        self.setCacheMode(self.CacheModeFlag.CacheBackground)

        self.setBackgroundRole(QPalette.ColorRole.NoRole)
        self.setBackgroundBrush(FColor.mkBrush('background'))

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setFrameShape(QFrame.Shape.NoFrame)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        self.setMouseTracking(True)

        self._central_widget = None

        self._last_mouse_pos = None
        self.range = QRectF(0, 0, 1, 1)
        self.autoPixelRange = True  # the ImageColor bar disappears when it is False
        self.updateMatrix()

    def render(self, *args, **kwds):
        self.scene().prepareForPaint()
        return QGraphicsView.render(self, *args, **kwds)

    def setCentralWidget(self, widget: QGraphicsWidget) -> None:
        self._central_widget = widget
        self.scene().addItem(widget)
        # Otherwise ImageAnalysis will have TypeError
        self.resizeEvent(None)
    
    def resizeEvent(self, ev):
        if self.autoPixelRange:
            self.range = QRectF(0, 0, self.size().width(), self.size().height())
        GraphicsView.setRange(self, self.range, padding=0, disableAutoPixel=False)  # we do this because some subclasses like to redefine setRange in an incompatible way.
        self.updateMatrix()
    
    def updateMatrix(self):
        self.setSceneRect(self.range)
        if self.autoPixelRange:
            self.resetTransform()
        else:
            self.fitInView(self.range, Qt.IgnoreAspectRatio)

    def setRange(self, newRect, padding=0.05, disableAutoPixel=True):
        if disableAutoPixel:
            self.autoPixelRange=False

        padding = Point(padding)
        newRect = QRectF(newRect)
        pw = newRect.width() * padding[0]
        ph = newRect.height() * padding[1]
        newRect = newRect.adjusted(-pw, -ph, pw, ph)
        scaleChanged = False
        if self.range.width() != newRect.width() or self.range.height() != newRect.height():
            scaleChanged = True
        self.range = newRect

        self._central_widget.setGeometry(self.range)
        self.updateMatrix()
        if scaleChanged:
            self.scale_changed_sgn.emit(self)

    def paintEvent(self, ev: QPaintEvent) -> None:
        """Override."""
        self.scene().prepareForPaint()
        QGraphicsView.paintEvent(self, ev)
