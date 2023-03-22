"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc

from ..backend.QtCore import pyqtSignal, QPointF, QRectF, Qt
from ..backend.QtGui import QCloseEvent, QPalette, QResizeEvent
from ..backend.QtWidgets import (
    QFrame, QGraphicsView, QGraphicsWidget, QSizePolicy
)

from ..aesthetics import FColor
from ..graphics_scene import GraphicsScene


class GraphicsView(QGraphicsView):

    device_range_changed_sgn = pyqtSignal(object, object)
    device_transform_changed_sgn = pyqtSignal(object)

    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self.setScene(GraphicsScene(parent=self))

        self.setCacheMode(self.CacheModeFlag.CacheBackground)

        self.setBackgroundRole(QPalette.ColorRole.NoRole)
        self.setBackgroundBrush(FColor.mkBrush('background'))

        # turn off scroll bars
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setFrameShape(QFrame.Shape.NoFrame)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        self.setMouseTracking(True)

        self._cw = None

        self._range = QRectF(0, 0, 1, 1)
        self.updateMatrix()

        if parent is not None and hasattr(parent, 'registerGraphicsView'):
            parent.registerGraphicsView(self)

    def setCentralWidget(self, widget: QGraphicsWidget) -> None:
        self._cw = widget
        self.scene().addItem(widget)
        self.resizeEvent(None)

    def updateMatrix(self):
        self.setSceneRect(self._range)
        self.resetTransform()

    def addItem(self, *args, **kwargs):
        self._cw.addItem(*args, **kwargs)

    def removeItem(self, *args, **kwargs):
        self._cw.removeItem(*args, **kwargs)

    def setTitle(self, *args, **kwargs):
        self._cw.setTitle(*args, **kwargs)

    def showXAxis(self, *args, **kwargs):
        self._cw.showAxis('bottom', *args, **kwargs)

    def showYAxis(self, *args, **kwargs):
        self._cw.showAxis('left', *args, **kwargs)

    def setXLabel(self, *args, **kwargs):
        self._cw.setLabel("bottom", *args, **kwargs)

    def setYLabel(self, *args, **kwargs):
        self._cw.setLabel("left", *args, **kwargs)

    def clearData(self):
        self._cw.clearData()

    @abc.abstractmethod
    def updateF(self, data):
        """This method is called by the parent window."""
        raise NotImplementedError

    def setAspectLocked(self, state: bool) -> None:
        self._cw.setAspectLocked(state)

    def resizeEvent(self, ev: QResizeEvent) -> None:
        """Override."""
        self._range = QRectF(0, 0, self.size().width(), self.size().height())
        self._cw.setGeometry(self._range)
        self.updateMatrix()

    def close(self) -> None:
        """Override."""
        self._cw.close()
        self.setParent(None)
        super().close()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Override."""
        parent = self.parent()
        if parent is not None and hasattr(parent, 'unregisterGraphicsView'):
            parent.unregisterGraphicsView(self)
        super().closeEvent(event)
