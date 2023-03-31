"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from foamgraph.backend.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from foamgraph import (
    FColor, LiveWindow, ImageView, mkQApp, GraphView
)
from foamgraph.algorithm import extract_rect_roi

from consumer import Consumer

app = mkQApp()


class ImageAnalysis(ImageView):
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

        self._image = ImageAnalysis(parent=self)
        roi1 = self._image.addRectROI(0, 0, 100, 100)
        roi2 = self._image.addEllipseROI(10, 10, 100, 100)

        self._plots = [
            RoiProjectionMonitor(roi1, parent=self),
            RoiProjectionMonitor(roi2, parent=self)
        ]

        self.init()

    def initUI(self):
        """Override."""
        h_layout = QHBoxLayout()
        for mon in self._plots:
            h_layout.addWidget(mon)

        layout = QVBoxLayout()
        layout.addWidget(self._image, 5)
        layout.addLayout(h_layout, 2)

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

        w, h = 800, 800
        self.resize(w, h)
        self.setMinimumSize(int(0.6 * w), int(0.6 * h))

    def initConnections(self):
        """Override."""
        ...


if __name__ == "__main__":
    gui = ImageAnalysisWindow()
    consumer = Consumer(gui.queue)

    gui.start()
    consumer.start()

    app.exec()
