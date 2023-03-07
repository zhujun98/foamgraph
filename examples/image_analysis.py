"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import numpy as np

from foamgraph.backend.QtCore import QTimer
from foamgraph.backend.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from foamgraph import (
    AbstractScene, ImageView, mkQApp, GraphView
)
from foamgraph.algorithm import extract_rect_roi
from foamgraph.ctrl_widgets import RoiCtrlWidgetGroup

from consumer import Consumer

app = mkQApp()


class ImageAnalysis(ImageView):
    def updateF(self, data):
        """Override."""
        self.setImage(data['image']['data'])


# TODO: improve ROI geometry handling
class RoiProjectionMonitor(GraphView):
    def __init__(self, id_: str, *, parent=None):
        super().__init__(parent=parent)

        self._id = id_
        self.setTitle(id_)

        self._roi_geom = None

        self._plot = self.addCurvePlot()

    def onRoiGeometryChange(self, id_: str, value: tuple):
        if id_ != self._id:
            return

        activated, _, x, y, w, h = value
        if activated:
            self._roi_geom = (x, y, w, h)
        else:
            self._roi_geom = None

    def updateF(self, data):
        """override."""
        if self._roi_geom is None:
            self.clearData()
            return

        roi = extract_rect_roi(data['image']['data'], self._roi_geom)
        if roi is None:
            self._plot.setData(None, None)
        else:
            proj = np.mean(roi, axis=0)
            self._plot.setData(np.arange(len(proj)), proj)


class ImageAnalysisScene(AbstractScene):
    _title = "Image Analysis"

    def __init__(self, *args, **kwargs):
        """Initialization."""
        super().__init__(*args, **kwargs)

        num_rois = 2
        self._image = ImageAnalysis(parent=self)
        self._roi_ctrl = RoiCtrlWidgetGroup(parent=self)
        self._roi_monitors = []

        for i in range(num_rois):
            roi = self._image.addROI()
            id_ = f"ROI{i+1}"
            self._roi_ctrl.addROI(id_, roi)
            self._roi_monitors.append(RoiProjectionMonitor(id_, parent=self))

        self.initUI()
        self.initConnections()

        self._timer = QTimer()
        self._timer.timeout.connect(self.updateWidgetsF)
        self._timer.start(100)

    def initUI(self):
        """Override."""
        h_layout = QHBoxLayout()
        for mon in self._roi_monitors:
            h_layout.addWidget(mon)

        layout = QVBoxLayout()
        layout.addWidget(self._image)
        layout.addWidget(self._roi_ctrl)
        layout.addLayout(h_layout)

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

        w, h = 640, 800
        self.resize(w, h)
        self.setMinimumSize(int(0.6 * w), int(0.6 * h))

    def initConnections(self):
        """Override."""
        for mon in self._roi_monitors:
            self._roi_ctrl.roi_geometry_change_sgn.connect(
                mon.onRoiGeometryChange)


if __name__ == "__main__":
    scene = ImageAnalysisScene()

    consumer = Consumer(scene.queue)
    consumer.start()

    app.exec()
