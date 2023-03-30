"""
Distributed under the terms of the BSD 3-Clause License.
The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from collections import deque
from typing import Optional
from weakref import WeakKeyDictionary

from .version import __version__
from .backend.QtGui import QCloseEvent
from .backend.QtCore import QObject, Qt, QTimer
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
        self._graphics_views = WeakKeyDictionary()

        self._cw = QWidget()
        self.setCentralWidget(self._cw)

        self.show()

        self._queue = deque(maxlen=self._QUEUE_SIZE)

        self._timer: Optional[QTimer] = None

    def init(self):
        """Initialization of the window.

        Should be called by the __init__ method of the child class.
        """
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
        self._graphics_views[instance] = 1

    def unregisterGraphicsView(self, instance: GraphicsView):
        del self._graphics_views[instance]

    def updateGraphicsViews(self):
        """Update all the graphics views."""
        if len(self._queue) == 0:
            return

        data = self._queue.pop()
        for view in self._graphics_views:
            view.updateF(data)

    def start(self, update_interval: int = 10) -> None:
        """Start updating all the graphics views.

        :param update_interval: time interval in milliseconds for updating
            all the graphics views if there is new data received. The actual
            interval can be longer if updating takes time longer than the
            interval.
        """
        self._timer = QTimer()
        self._timer.timeout.connect(self.updateGraphicsViews)
        self._timer.start(update_interval)

    def reset(self) -> None:
        """Reset data in all the graphics views."""
        for view in self._graphics_views:
            view.reset()

    def closeEvent(self, ev: QCloseEvent):
        """Override."""
        parent = self.parent()
        if parent is not None:
            parent.unregisterWindow(self)
        super().closeEvent(ev)
