"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from foamgraph.backend.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout
)
from foamgraph import LiveWindow, ImageView, mkQApp, SmartView, Section

from consumer import Consumer

app = mkQApp()


class ImageViewWithROIs(ImageView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Image with ROIs")

    def updateF(self, data):
        """Override."""
        self.setImage(data['image']['data'])


class ImageAnalysisWindow(LiveWindow):
    def __init__(self):
        super().__init__("Image Analysis")

        self._view = ImageViewWithROIs(parent=self)

        self._view.addRectROI(100, 100, name="ROI1")
        self._view.addEllipseROI(100, 100, name="ROI2")
        self._section = Section(parent=self)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(SmartView(parent=self))
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
