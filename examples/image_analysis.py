"""
Distributed under the terms of the MIT License.

The full license is in the file LICENSE, distributed with this software.

Copyright (C) Jun Zhu. All rights reserved.
"""
import numpy as np

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from foamgraph import (
    AbstractScene, ImageViewF, mkQApp, PlotWidgetF
)
from foamgraph.ctrl_widgets import RoiCtrlWidgetGroup

from consumer import Consumer

app = mkQApp()


class ImageAnalysis(ImageViewF):
    def updateF(self, data):
        """Override."""
        self.setImage(data['image']['data'])


# FIXME
class RoiProjectionMonitor(PlotWidgetF):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self._roi_geom = None

        self._plot = self.plotCurve()

    def onRoiGeometryChange(self, value: tuple):
        idx, activated, _, x, y, w, h = value
        if idx != 1:
            return

        if activated:
            self._roi_geom = (x, y, w, h)
        else:
            self._roi_geom = None

    def updateF(self, data):
        """override."""
        if self._roi_geom is None:
            self.reset()
            return

        x, y, w, h = self._roi_geom
        data = data['image']["data"][y:y+h, x:x+w]
        self._plot.setData(np.arange(w), np.mean(data, axis=0))


class ImageAnalysisScene(AbstractScene):
    _title = "Image Analysis"

    _TOTAL_W, _TOTAL_H = 900, 600

    def __init__(self, n_rois: int = 0, *args, **kwargs):
        """Initialization."""
        super().__init__(*args, **kwargs)

        self._image = ImageAnalysis(n_rois=n_rois, parent=self)
        self._roi_ctrl = RoiCtrlWidgetGroup(parent=self)
        self._image.addRoiController(self._roi_ctrl)
        self._roi_monitor = RoiProjectionMonitor(parent=self)

        self.initUI()
        self.initConnections()

        self.resize(self._TOTAL_W, self._TOTAL_H)
        self.setMinimumSize(int(0.6 * self._TOTAL_W), int(0.6 * self._TOTAL_H))

        self._timer = QTimer()
        self._timer.timeout.connect(self.updateWidgetsF)
        self._timer.start(100)

    def initUI(self):
        """Override."""
        layout = QVBoxLayout()
        layout.addWidget(self._image)
        layout.addWidget(self._roi_ctrl)
        layout.addWidget(self._roi_monitor)

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

    def initConnections(self):
        """Override."""
        self._roi_ctrl.roi_geometry_change_sgn.connect(
            self._roi_monitor.onRoiGeometryChange)


if __name__ == "__main__":
    scene = ImageAnalysisScene(n_rois=2)

    consumer = Consumer(scene.queue)
    consumer.start()

    app.exec_()
