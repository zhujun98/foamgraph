"""
Distributed under the terms of the BSD 3-Clause License.
The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from collections import deque
from weakref import WeakKeyDictionary

from .backend.QtCore import QObject, Qt
from .backend.QtWidgets import QMainWindow, QWidget


class _SceneMeta(type(QObject), abc.ABCMeta):
    ...


class _SceneMixin(metaclass=_SceneMeta):
    @abc.abstractmethod
    def initUI(self):
        """Initialization of UI."""
        ...

    @abc.abstractmethod
    def initConnections(self):
        """Initialization of signal-slot connections."""
        ...

    @abc.abstractmethod
    def reset(self):
        """Reset data in all the widgets."""
        ...

    @abc.abstractmethod
    def updateWidgetsF(self):
        """Update all the widgets."""
        ...


class AbstractScene(QMainWindow, _SceneMixin):
    """Base class for scenes."""
    _title = ""

    _SPLITTER_HANDLE_WIDTH = 5
    _QUEUE_SIZE = 5

    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if parent is not None:
            parent.registerWindow(self)

        self._ctrl_widgets = WeakKeyDictionary()
        self._plot_widgets = WeakKeyDictionary()  # book-keeping plot widgets

        try:
            title = parent.title + " - " + self._title
        except AttributeError:
            title = self._title  # for unit test where parent is None
        self.setWindowTitle(title)

        self._cw = QWidget()
        self.setCentralWidget(self._cw)

        self.show()

        self._queue = deque(maxlen=self._QUEUE_SIZE)

    @property
    def queue(self):
        return self._queue

    def reset(self):
        """Override."""
        for widget in self._plot_widgets:
            widget.reset()

    def updateWidgetsF(self):
        """Override."""
        if len(self._queue) == 0:
            return

        data = self._queue[0]
        for widget in self._plot_widgets:
            widget.updateF(data)

    def onStart(self):
        for widget in self._ctrl_widgets:
            widget.onStart()

    def onStop(self):
        for widget in self._ctrl_widgets:
            widget.onStop()

    def updateMetaData(self):
        """Update metadata from all the ctrl widgets.

        :returns bool: True if all metadata successfully parsed
            and emitted, otherwise False.
        """
        for widget in self._ctrl_widgets:
            if not widget.updateMetaData():
                return False
        return True

    def loadMetaData(self):
        """Load metadata from Redis and set child control widgets."""
        for widget in self._ctrl_widgets:
            widget.loadMetaData()

    def registerCtrlWidget(self, instance):
        self._ctrl_widgets[instance] = 1

    def unregisterCtrlWidget(self, instance):
        del self._ctrl_widgets[instance]

    def registerPlotWidget(self, instance):
        self._plot_widgets[instance] = 1

    def unregisterPlotWidget(self, instance):
        del self._plot_widgets[instance]

    def closeEvent(self, QCloseEvent):
        parent = self.parent()
        if parent is not None:
            parent.unregisterWindow(self)
        super().closeEvent(QCloseEvent)
