foamgraph
=========

[![PyPi](https://img.shields.io/pypi/v/foamgraph.svg)](https://pypi.org/project/foamgraph/)
![Build status](https://github.com/zhujun98/foamgraph/actions/workflows/python-package.yml/badge.svg)

![Language](https://img.shields.io/badge/language-python-blue)
[![Qt 5](https://img.shields.io/badge/Qt-5-brightgreen)](https://doc.qt.io/qt-5/)

`foamgraph` was originally developed as part of the online analysis framework 
[EXtra-foam](https://github.com/European-XFEL/EXtra-foam.git)
to provide fast display (10 Hz) and interactive data analysis for photon science
experiments at the state-of-art free-electron laser (FEL) facility - European XFEL.
It was implemented on top of the famous Python graphics and GUI library
[PyQtGraph](https://github.com/pyqtgraph/pyqtgraph). The following features make 
`foamgraph` stand out:

- The widgets and graphics objects are dedicated for photon science experiments.
- The performance has been significantly improved.
- It trades flexibility for an easy-to-use and unified API.

It must be emphasized that `foamgraph` is only a GUI library. It does not provide
any interfaces for data and metadata exchange between the backend and the GUI because
it is facility and experiment specific.

Nevertheless, when integrating GUI into a real-time data analysis pipeline, 
there are a couple of things to be taken into account:
- The GUI in principle should not perform any number crunching jobs, otherwise it 
will be slowed down because it is written in Python.
- Light computation tasks can be performed in a Python thread and the communication 
between the GUI and the processor can still be fulfilled using Qt's signal-slot connections.

## Examples

* Open a terminal and start the producer:

```sh
python examples/producer.py
```

* Open another terminal and start the plot gallery example

```sh
python examples/plot_gallery.py
```

![](examples/plot_gallery.gif)

* Open another terminal and start the image analysis example

```sh
python examples/image_analysis.py
```

![](examples/image_analysis.gif)
