"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from foamgraph.backend.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout
)
from foamgraph import (
    FColor, LiveWindow, ImageView, mkQApp, GraphView, Section
)
from foamgraph.algorithm import extract_rect_roi

from consumer import Consumer

app = mkQApp()


class ImageViewWithROIs(ImageView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Image with ROIs")

    def updateF(self, data):
        """Override."""
        self.setImage(data['image']['data'])


class RoiProjectionMonitor(GraphView):
    def __init__(self, roi, *, parent=None):
        super().__init__(parent=parent)

        self._roi = roi
        self.setTitle(roi.name())

        self._plot = self.addCurvePlot(pen=FColor.mkPen(roi.color()))

    def updateF(self, data):
        """override."""
        if not self._roi.isVisible():
            self._plot.setData(None, None)
            return

        data = extract_rect_roi(data['image']['data'], self._roi.region())
        if data is None:
            self._plot.clearData()
        else:
            proj = np.mean(data, axis=0)
            self._plot.setData(np.arange(len(proj)), proj)


class ImageAnalysisWindow(LiveWindow):
    def __init__(self):
        super().__init__("Image Analysis")

        self._view = ImageViewWithROIs(parent=self)

        roi1 = self._view.addRectROI(0, 0, 100, 100)
        roi2 = self._view.addEllipseROI(10, 10, 100, 100)
        self._section = Section(parent=self)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for roi in [roi1, roi2]:
            layout.addWidget(RoiProjectionMonitor(roi, parent=self))
        self._section.setLayout(layout)

        self.init()

    def initUI(self):
        """Override."""
        layout = QVBoxLayout()
        layout.addWidget(self._view)
        layout.addWidget(self._section)
        layout.setSpacing(0)

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

        w, h = 800, 800
        self.resize(w, h)
        self.setMinimumSize(int(0.6 * w), int(0.6 * h))

    def initConnections(self):
        """Override."""
        self._section.collapse_toggled_sgn.connect(
            self._onSectionToggled)

    def _onSectionToggled(self, state: bool):
        layout = self._cw.layout()
        stretches = (0, 0) if state else (2, 1)
        for i, s in enumerate(stretches):
            layout.setStretch(i, s)


if __name__ == "__main__":
    gui = ImageAnalysisWindow()
    consumer = Consumer(gui.queue)

    gui.start()
    consumer.start()

    app.exec()
