"""
Distributed under the terms of the BSD 3-Clause License.
The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu <jun.zhu@xfel.eu>
Copyright (C) European X-Ray Free-Electron Laser Facility GmbH.
All rights reserved.
"""
import abc
from collections import deque
from weakref import WeakKeyDictionary

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget


class _SceneMixin:
    @abc.abstractmethod
    def initUI(self):
        """Initialization of UI."""
        raise NotImplementedError

    @abc.abstractmethod
    def initConnections(self):
        """Initialization of signal-slot connections."""
        ...

    @abc.abstractmethod
    def reset(self):
        """Reset data in all the widgets."""
        raise NotImplementedError

    @abc.abstractmethod
    def updateWidgetsF(self):
        """Update all the widgets."""
        raise NotImplementedError


class AbstractScene(QMainWindow, _SceneMixin):
    """Base class for scenes."""
    _title = ""

    _SPLITTER_HANDLE_WIDTH = 5

    def __init__(self, queue: deque, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if parent is not None:
            parent.registerWindow(self)

        self._ctrl_widgets = []
        self._plot_widgets = WeakKeyDictionary()  # book-keeping plot widgets

        try:
            title = parent.title + " - " + self._title
        except AttributeError:
            title = self._title  # for unit test where parent is None
        self.setWindowTitle(title)

        self._cw = QWidget()
        self.setCentralWidget(self._cw)

        self.show()

        self._queue = queue

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

    def createCtrlWidget(self, widget_class):
        widget = widget_class(parent=self)
        self._ctrl_widgets.append(widget)
        return widget

    def registerPlotWidget(self, instance):
        self._plot_widgets[instance] = 1

    def unregisterPlotWidget(self, instance):
        del self._plot_widgets[instance]

    def closeEvent(self, QCloseEvent):
        parent = self.parent()
        if parent is not None:
            parent.unregisterWindow(self)
        super().closeEvent(QCloseEvent)
