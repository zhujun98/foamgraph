"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import abstractmethod

import numpy as np

from foamgraph.backend.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QTabWidget, QVBoxLayout
)
from foamgraph import mkQApp, GraphView
from foamgraph.version import __version__

app = mkQApp()


class PlotControlBase(QFrame):
    def __init__(self, view, doc, parent=None):
        super().__init__(parent=parent)

        self._view = view
        self._doc = doc

        self._dataset = QComboBox()

        self._nan_x = QCheckBox("Add NaN to x data")
        self._nan_y = QCheckBox("Add NaN to y data")
        self._nan_x.toggled.connect(self._view.addNanToX)
        self._nan_y.toggled.connect(self._view.addNanToY)

        layout = QVBoxLayout(self)
        layout.addWidget(self._dataset)
        layout.addWidget(self._nan_x)
        layout.addWidget(self._nan_y)
        self._layout = layout

    def updateDataset(self):
        self._dataset.currentIndexChanged.emit(self._dataset.currentIndex())


class ViewBase(GraphView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setXYLabels("x", "y")

        self._data_idx = 0
        self._data = []

        self._nan_x = False
        self._nan_y = False

    def setDataset(self, idx: int):
        self._data_idx = idx
        self.setData()

    def addNanToX(self, checked):
        self._nan_x = checked
        self.setData()

    def addNanToY(self, checked):
        self._nan_y = checked
        self.setData()

    @abstractmethod
    def setData(self):
        raise NotImplementedError

    def getData(self):
        return [item.copy() for item in self._data[self._data_idx]]


class PlotTab(QFrame):
    def __init__(self, control_kls, view_kls, parent=None):
        super().__init__(parent=parent)

        self._doc = QLabel()
        self._view = view_kls()
        self._control = control_kls(self._view, self._doc)

        layout = QGridLayout(self)
        layout.addWidget(self._doc, 0, 0, 1, 2)
        layout.addWidget(self._control, 1, 0, 1, 1)
        layout.addWidget(self._view, 1, 1, 1, 1)
        self.setLayout(layout)


class CurvePlotControl(PlotControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._item_type = QComboBox()
        self._item_type.addItems(["SimpleCurvePlotItem", "CurvePlotItem"])
        self._item_type.currentTextChanged.connect(self.onItemTypeChanged)

        self._dataset.addItems(["Dataset 1"])
        self._dataset.currentIndexChanged.connect(self._view.setDataset)

        self._item_type.currentTextChanged.emit(self._item_type.currentText())

        self._layout.addWidget(self._item_type)

    def onItemTypeChanged(self, name: str):
        if name == "SimpleCurvePlotItem":
            self._doc.setText("SimpleCurvePlotItem")
            self._view.setSimplePlot()
        else:
            self._doc.setText("CurvePlotItem ")
            self._view.setPlot()

        self.updateDataset()


class CurvePlotView(ViewBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Curve Plot")

        self._curve = self.addCurvePlot()
        self._curve_simple = self.addCurvePlot(simple=True)
        self._plot = None

        x = np.linspace(-100, 100, 201, dtype=np.float32)
        self._data = [
            (x, np.sin(x * np.pi / 30))
        ]

    def setPlot(self):
        self._plot = self._curve
        self._curve_simple.hide()
        self._curve.show()

    def setSimplePlot(self):
        self._plot = self._curve_simple
        self._curve.hide()
        self._curve_simple.show()

    def setData(self):
        x, y = self.getData()
        if self._nan_x:
            x[:10] = np.nan
        if self._nan_y:
            y[:10] = np.nan
        self._plot.setData(x, y)


class ShadePlotControl(PlotControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._dataset.addItems(["Dataset 1"])
        self._dataset.currentIndexChanged.connect(self._view.setDataset)
        self.updateDataset()


class ShadePlotView(ViewBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Scatter Plot")
        self._plot = self.addShadedPlot()

        x = np.linspace(-100, 100, 201, dtype=np.float32)
        self._data = [
            (x, np.sin(x * np.pi / 40), np.sin(x * np.pi / 60))
        ]

    def setData(self):
        x, y1, y2 = self.getData()
        self._plot.setData(x, y1, y2)


class ScatterPlotControl(PlotControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._dataset.addItems(["Dataset 1"])
        self._dataset.currentIndexChanged.connect(self._view.setDataset)
        self.updateDataset()


class ScatterPlotView(ViewBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Scatter Plot")
        self._plot = self.addScatterPlot()

        self._data = [
            (np.random.normal(0, 1, 100), np.random.normal(0, 1, 100))
        ]

    def setData(self):
        x, y = self.getData()
        if self._nan_x:
            x[:10] = np.nan
        if self._nan_y:
            y[:10] = np.nan
        self._plot.setData(x, y)


class StemPlotControl(PlotControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._dataset.addItems(["Dataset 1"])
        self._dataset.currentIndexChanged.connect(self._view.setDataset)
        self.updateDataset()


class StemPlotView(ViewBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Stem Plot")
        self._plot = self.addStemPlot()

        x = np.linspace(-100, 100, 101, dtype=np.float32)
        self._data = [
            (x, np.sin(x * np.pi / 60))
        ]

    def setData(self):
        x, y = self.getData()
        if self._nan_x:
            x[:10] = np.nan
        if self._nan_y:
            y[:10] = np.nan
        self._plot.setData(x, y)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.statusBar().showMessage(f"foamgraph {__version__}")

        self._cw = QTabWidget(parent=self)

        self._cw.addTab(PlotTab(CurvePlotControl, CurvePlotView), "Curve Plot")
        self._cw.addTab(PlotTab(ShadePlotControl, ShadePlotView), "Shaded Plot")
        self._cw.addTab(PlotTab(ScatterPlotControl, ScatterPlotView), "Scatter Plot")
        self._cw.addTab(PlotTab(StemPlotControl, StemPlotView), "Stem Plot")

        self.setCentralWidget(self._cw)
        self.resize(800, 400)


if __name__ == "__main__":

    win = MainWindow()
    win.show()

    app.exec()
