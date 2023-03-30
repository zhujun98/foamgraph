"""
Distributed under the terms of the BSD 3-Clause License.
The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from collections import deque
from weakref import WeakKeyDictionary

from .version import __version__
from .backend.QtCore import QObject, Qt
from .backend.QtWidgets import QMainWindow, QWidget
from .graph_view import GraphicsView


class _LiveWindowMeta(type(QObject), abc.ABCMeta):
    ...


class LiveWindow(QMainWindow, metaclass=_LiveWindowMeta):
    """Base class for scenes."""

    _SPLITTER_HANDLE_WIDTH = 5
    _QUEUE_SIZE = 5

    def __init__(self, title: str = "", *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.setWindowTitle(title)
        self.statusBar().showMessage(f"foamgraph {__version__}")

        self._ctrl_widgets = WeakKeyDictionary()
        self._graphics_view = WeakKeyDictionary()  # book-keeping plot widgets

        self._cw = QWidget()
        self.setCentralWidget(self._cw)

        self.show()

        self._queue = deque(maxlen=self._QUEUE_SIZE)

    def init(self):
        self.initUI()
        self.initConnections()

    @abc.abstractmethod
    def initUI(self):
        """Initialization of UI."""
        ...

    @abc.abstractmethod
    def initConnections(self):
        """Initialization of signal-slot connections."""
        ...

    @property
    def queue(self):
        return self._queue

    def onStart(self):
        for widget in self._ctrl_widgets:
            widget.onStart()

    def onStop(self):
        for widget in self._ctrl_widgets:
            widget.onStop()

    def registerCtrlWidget(self, instance):
        self._ctrl_widgets[instance] = 1

    def unregisterCtrlWidget(self, instance):
        del self._ctrl_widgets[instance]

    def registerGraphicsView(self, instance: GraphicsView):
        self._graphics_view[instance] = 1

    def unregisterGraphicsView(self, instance: GraphicsView):
        del self._graphics_view[instance]

    def updateWidgetsF(self):
        """Update all the graphics widgets."""
        if len(self._queue) == 0:
            return

        data = self._queue.pop()
        for widget in self._graphics_view:
            widget.updateF(data)

    def reset(self):
        """Reset data in all the widgets."""
        for widget in self._graphics_view:
            widget.reset()

    def closeEvent(self, QCloseEvent):
        parent = self.parent()
        if parent is not None:
            parent.unregisterWindow(self)
        super().closeEvent(QCloseEvent)
