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
from foamgraph import FColor, mkQApp, GraphView, ImageView
from foamgraph.version import __version__

app = mkQApp()


class GraphControlBase(QFrame):
    def __init__(self, view, doc, parent=None):
        super().__init__(parent=parent)

        self._view = view
        self._doc = doc

        self._dataset = QComboBox()
        self._dataset.addItems(["Dataset 1"])
        self._dataset.currentIndexChanged.connect(self._view.setDataset)

        self._nan_x = QCheckBox("Add NaN to x data")
        self._nan_y = QCheckBox("Add NaN to y data")
        self._nan_x.toggled.connect(self._view.addNanToX)
        self._nan_y.toggled.connect(self._view.addNanToY)

        layout = QVBoxLayout(self)
        layout.addWidget(self._dataset)
        layout.addWidget(self._nan_x)
        layout.addWidget(self._nan_y)
        self._layout = layout

    def init(self):
        self._dataset.currentIndexChanged.emit(self._dataset.currentIndex())


class GraphViewDemoBase(GraphView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setXYLabels("x", "y")

        self._data_idx = 0
        self._data = []

        self._nan_x = False
        self._nan_y = False

        self.addLegend()

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


class CurvePlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._item_type = QComboBox()
        self._item_type.addItems(["SimpleCurvePlotItem", "CurvePlotItem"])
        self._item_type.currentTextChanged.connect(self.onItemTypeChanged)

        self._add_uncertainty = QCheckBox("Add uncertainty")
        self._add_uncertainty.toggled.connect(self._view.addUncertainty)

        self._layout.addWidget(self._item_type)
        self._layout.addWidget(self._add_uncertainty)

        self._item_type.currentTextChanged.emit(self._item_type.currentText())

    def onItemTypeChanged(self, name: str):
        if name == "SimpleCurvePlotItem":
            self._doc.setText("SimpleCurvePlotItem")
            self._add_uncertainty.setEnabled(False)
            self._add_uncertainty.setChecked(False)
            self._view.setSimplePlot()
        else:
            self._doc.setText("CurvePlotItem ")
            self._add_uncertainty.setEnabled(True)
            self._view.setPlot()

        self.init()


class CurvePlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Curve Plot")

        self._curve = self.addCurvePlot(label="curve")
        self._curve_simple = self.addCurvePlot(simple=True, label="curve")
        self._plot = None

        x = np.linspace(-100, 100, 201, dtype=np.float32)
        self._data = [
            (x, np.sin(x * np.pi / 30), np.random.random(201))
        ]

        self._add_uncertainty = False

    def addUncertainty(self, state: bool):
        self._add_uncertainty = state
        self.setData()

    def setPlot(self):
        self._plot = self._curve
        self._curve_simple.hide()
        self._curve.show()

    def setSimplePlot(self):
        self._plot = self._curve_simple
        self._curve.hide()
        self._curve_simple.show()

    def setData(self):
        x, y, y_err = self.getData()
        if self._nan_x:
            x[:10] = np.nan
        if self._nan_y:
            y[:10] = np.nan

        if self._add_uncertainty:
            self._plot.setData(x, y, y_err)
        else:
            self._plot.setData(x, y)


class ShadePlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()


class ShadePlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Scatter Plot")
        self._plot = self.addShadedPlot(label="shaded")

        x = np.linspace(-100, 100, 201, dtype=np.float32)
        self._data = [
            (x, np.sin(x * np.pi / 40), np.sin(x * np.pi / 60))
        ]

    def setData(self):
        x, y1, y2 = self.getData()
        self._plot.setData(x, y1, y2)


class ScatterPlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()


class ScatterPlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Scatter Plot")
        self._plot = self.addScatterPlot(label="scatter")

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


class BarPlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_bars = QComboBox()
        self._num_bars.currentTextChanged.connect(self._view.setNumDatasets)
        self._num_bars.addItems(["1", "2", "3"])

        self._stack_orientation = QComboBox()
        self._stack_orientation.currentTextChanged.connect(self._view.setStackOrientation)
        self._stack_orientation.addItems(["Vertical", "Horizontal"])

        self._layout.addWidget(QLabel("Number of datasets: "))
        self._layout.addWidget(self._num_bars)
        self._layout.addWidget(QLabel("Stack orientation: "))
        self._layout.addWidget(self._stack_orientation)

        self.init()


class BarPlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Bar Plot")
        self._plots = []

        self._num_datasets = 1

        self._data = []
        for _ in range(3):
            data = np.random.normal(size=1000)
            hist, _ = np.histogram(data, bins=40)
            self._data.append(
                (np.arange(40).astype(np.float64), hist.astype(np.float64))
            )

    def setNumDatasets(self, num: str):
        self._num_datasets = int(num)

        for plot in self._plots:
            self.removeItem(plot)
        self._plots.clear()

        pens = [FColor.mkPen('b'),
                FColor.mkPen('FireBrick'),
                FColor.mkPen('ForestGreen')]
        brushes = [FColor.mkBrush('b', alpha=100),
                   FColor.mkBrush('FireBrick', alpha=100),
                   FColor.mkBrush('ForestGreen', alpha=100)]
        for i in range(self._num_datasets):
            self._plots.append(self.addBarPlot(
                label=f"bar{i+1}", width=0.9, pen=pens[i], brush=brushes[i]))

        self.setData()

    def setStackOrientation(self, orientation: str):
        self.setBarPlotStackOrientation(orientation)
        self.setData()

    def setData(self):
        for i, plot in enumerate(self._plots):
            x, y = [d.copy() for d in self._data[i]]
            if self._nan_x:
                x[:10] = np.nan
            if self._nan_y:
                y[:10] = np.nan
            plot.setData(x, y)


class ErrorbarPlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()


class ErrorbarPlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Errorbar Plot")
        self._plot = self.addErrorbarPlot(beam=1, label="errorbar")

        data = np.random.normal(size=1000)
        hist, _ = np.histogram(data, bins=40)
        self._data = [
            (np.arange(40).astype(np.float64), hist.astype(np.float64))
        ]

    def setData(self):
        x, y = self.getData()
        if self._nan_x:
            x[:10] = np.nan
        if self._nan_y:
            y[:10] = np.nan
        self._plot.setData(x, y, y-1., y+1.)


class CandlestickPlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()


class CandlestickPlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Candlestick Plot")
        self._plot = self.addCandlestickPlot(label="candlestick")

        n = 40
        x = np.arange(n).astype(np.float64)
        y_start = np.random.normal(0, 10., n) + 20.
        y_end = y_start + 20 * (np.random.random(n) - 0.5)
        y_min = np.minimum(y_start, y_end) - 10 * np.random.random(n)
        y_max = np.maximum(y_start, y_end) + 10 * np.random.random(n)
        self._data = [
            (x, y_start, y_end, y_min, y_max)
        ]

    def setData(self):
        x, y_start, y_end, y_min, y_max = self.getData()
        if self._nan_x:
            x[:10] = np.nan
        if self._nan_y:
            y_start[:10] = np.nan
        self._plot.setData(x, y_start, y_end, y_min, y_max)


class StemPlotControl(GraphControlBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()


class StemPlot(GraphViewDemoBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Stem Plot")
        self._plot = self.addStemPlot(label="stem")

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


class ImageControl(QFrame):
    def __init__(self, view, doc, parent=None):
        super().__init__(parent=parent)

        self._view = view
        self._doc = doc

        self._dataset = QComboBox()
        self._dataset.addItems(["Dataset 1"])
        self._dataset.currentIndexChanged.connect(self._view.setDataset)

        self._add_nan = QCheckBox("Add NaN to data")
        self._add_nan.toggled.connect(self._view.addNan)

        layout = QVBoxLayout(self)
        layout.addWidget(self._dataset)
        layout.addWidget(self._add_nan)
        self._layout = layout

        self.init()

    def init(self):
        self._dataset.currentIndexChanged.emit(self._dataset.currentIndex())


class Image(ImageView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._data_idx = 0
        self._data = []

        self._add_nan = False

        self.setTitle("Image")

        self._data = [
            np.random.random((100, 200))
        ]

    def setDataset(self, idx: int):
        self._data_idx = idx
        self.setData()

    def addNan(self, checked):
        self._add_nan = checked
        self.setData()

    def setData(self):
        data = self.getData()
        self.setImage(data)

    def getData(self):
        return self._data[self._data_idx]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.statusBar().showMessage(f"foamgraph {__version__}")

        self._cw = QTabWidget(parent=self)

        self._cw.addTab(PlotTab(CurvePlotControl, CurvePlot), "Curve Plot")
        self._cw.addTab(PlotTab(ShadePlotControl, ShadePlot), "Shaded Plot")
        self._cw.addTab(PlotTab(ScatterPlotControl, ScatterPlot), "Scatter Plot")
        self._cw.addTab(PlotTab(BarPlotControl, BarPlot), "Bar Plot")
        self._cw.addTab(PlotTab(ErrorbarPlotControl, ErrorbarPlot), "Errorbar Plot")
        self._cw.addTab(PlotTab(CandlestickPlotControl, CandlestickPlot), "Candlestick Plot")
        self._cw.addTab(PlotTab(StemPlotControl, StemPlot), "Stem Plot")
        self._cw.addTab(PlotTab(ImageControl, Image), "Image")

        self.setCentralWidget(self._cw)
        self.resize(1200, 600)


if __name__ == "__main__":

    win = MainWindow()
    win.show()

    app.exec()
