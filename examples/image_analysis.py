from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from foamgraph import (
    AbstractScene, mkQApp, ImageViewF
)
from foamgraph.ctrl_widgets import RoiCtrlWidgetGroup

from consumer import Consumer

app = mkQApp()


class ImageAnalysis(ImageViewF):
    def updateF(self, data):
        """Override."""
        try:
            data = data["image"]
        except KeyError:
            return

        self.setImage(data['data'])


class ImageAnalysisScene(AbstractScene):
    _title = "Image Analysis"

    _TOTAL_W, _TOTAL_H = 900, 600

    def __init__(self, n_rois: int = 0, *args, **kwargs):
        """Initialization."""
        super().__init__(*args, **kwargs)

        self._image = ImageAnalysis(n_rois=n_rois, parent=self)
        self._roi_ctrl = RoiCtrlWidgetGroup(parent=self)
        for roi in self._image.rois:
            self._roi_ctrl.addRoi(roi)

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

        self._cw = QFrame()
        self._cw.setLayout(layout)
        self.setCentralWidget(self._cw)

    def initConnections(self):
        """Override."""
        ...


if __name__ == "__main__":
    scene = ImageAnalysisScene(n_rois=2)

    consumer = Consumer(scene.queue)
    consumer.start()

    app.exec_()
