foamgraph
=========

[![PyPi](https://img.shields.io/pypi/v/foamgraph.svg)](https://pypi.org/project/foamgraph/)
![Build status](https://github.com/zhujun98/foamgraph/actions/workflows/python-package.yml/badge.svg)
![Build status](https://github.com/zhujun98/foamgraph/actions/workflows/codeql.yml/badge.svg)

![Language](https://img.shields.io/badge/language-python-blue)
[![Qt 5](https://img.shields.io/badge/Qt-5-brightgreen)](https://doc.qt.io/qt-5/)
[![Qt 6](https://img.shields.io/badge/Qt-6-brightgreen)](https://doc.qt.io/qt-6/)

`foamgraph` was originally developed as part of the online analysis framework 
[EXtra-foam](https://github.com/European-XFEL/EXtra-foam.git)
to provide fast display (10 Hz) and interactive data analysis for data-intensive 
photon science experiments at the state-of-art free-electron laser (FEL) facility - 
European XFEL. It was originally implemented on top of the famous Python graphics 
and GUI library [PyQtGraph](https://github.com/pyqtgraph/pyqtgraph). The following 
features made `foamgraph` stand out:

- The widgets are dedicated for photon science experiments.
- The performance has been significantly improved.

As of now, `foamgraph` has almost evolved into its own implementation completely. 
It's time to decide the direction for future development. Since there are already
many excellent GUI libraries around, `foamgraph` should and will do something different.

...

Nevertheless, when integrating GUI into a real-time data analysis pipeline, 
there are a couple of things to be taken into account:
- The GUI in principle should not perform any number crunching jobs, otherwise it 
will be slowed down because it is written in Python.
- Light computation tasks can be performed in a Python thread and the communication 
between the GUI and the processor can still be fulfilled using Qt's signal-slot connections.

## Getting started

Every plot widget should inherit from `GraphView`. The following code snippet
shows how to create a double-y plot with a title, axis labels and a legend:

```py
from foamgraph import FColor, GraphView


class DoubleYPlot(GraphView):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

        self.setTitle('Double-y plot')
        self.setXYLabels("x (arb. u.)", "y (arb. u.)", y2="y2 (arg. u.)")

        self._plot = self.addCurvePlot(label="Data", pen=FColor.mkPen('w'))
        self._plot2 = self.addBarPlot(
            label="Count", y2=True, brush=FColor.mkBrush('i', alpha=150))
        self.addLegend()

    def updateF(self, data):
        """Override."""
        self._plot.setData(data['x'], data['y'])
        self._plot2.setData(data['x'], data['y2'])
```

Every widget for image analysis should inherit from `ImageView`. The following
code snippet shows how to create a simple widget for displaying an image:

```py
from foamgraph import ImageView


class ImageAnalysis(ImageView):
    def updateF(self, data):
        """Override."""
        self.setImage(data['image']['data'])
```

## Examples

* Open a terminal and start the producer:

```sh
python examples/producer.py
```

* Open another terminal and start the plot gallery example

```sh
python examples/plot_gallery.py
```

![](https://github.com/zhujun98/foam-demo/blob/main/foamgraph/plot_galary.gif)

* Open another terminal and start the image analysis example

```sh
python examples/image_analysis.py
```

![](https://github.com/zhujun98/foam-demo/blob/main/foamgraph/image_analysis.gif)
