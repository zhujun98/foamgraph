"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc
from typing import final

from ..backend.QtCore import Qt, QTimer
from ..backend.QtWidgets import QHBoxLayout, QSizePolicy, QWidget

from ..aesthetics import ColorMap
from ..graphics_view import GraphicsView
from ..graphics_item import (
    ImageColorbarWidget, ImageItem, ImageWidget
)
from .graph_view import GraphViewBase


class ColorbarView(GraphicsView):
    def __init__(self, image_item: ImageItem, *, parent=None):
        super().__init__(parent=parent)

        self._item = ImageColorbarWidget(image_item)
        self.setCentralWidget(self._item)
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(95)

    def setColorMap(self, cm: ColorMap):
        self._item.setColorMap(cm)

    def updateImage(self, *args, **kwargs):
        self._cw.updateImage(*args, **kwargs)


class ImageView(GraphViewBase):
    """QGraphicsView for displaying images.

    This is normally used as a base class.
    """
    def __init__(self, *, parent=None):
        """Initialization."""
        super().__init__(parent=parent)

        self._cw = ImageWidget()
        self.setCentralWidget(self._cw)

    def addROI(self, *args, **kwargs):
        self._cw.addROI(*args, **kwargs)

    def setImage(self, *args, **kwargs):
        self._cw.setImage(*args, **kwargs)


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
