"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from typing import final

from ..backend.QtCore import Qt, QTimer

from ..graphics_widget import ImageWidget
from .graph_view import GraphicsView


class ImageView(GraphicsView):
    """QGraphicsView for displaying images.

    This is normally used as a base class.
    """
    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self._cw = ImageWidget()
        self.setCentralWidget(self._cw)

    def addRectROI(self, *args, **kwargs):
        return self._cw.addRectROI(*args, **kwargs)

    def addEllipseROI(self, *args, **kwargs):
        return self._cw.addEllipseROI(*args, **kwargs)

    def setImage(self, *args, **kwargs):
        self._cw.setImage(*args, **kwargs)

    def setColorMap(self, *args, **kwargs):
        self._cw.setColorMap(*args, **kwargs)


class TimedImageView(ImageView):
    def __init__(self, interval: int = 1000, *args, **kwargs):
        """Initialization.

        :param interval: Image updating interval in milliseconds.
        """
        super().__init__(*args, **kwargs)

        self._data = None

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_imp)
        self._timer.start(interval)

    @abc.abstractmethod
    def refresh(self):
        raise NotImplementedError

    def _refresh_imp(self):
        if self._data is not None:
            self.refresh()

    @final
    def updateF(self, data):
        """Override."""
        self._data = data
