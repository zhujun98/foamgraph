foamgraph
=========

[![Build Status](https://travis-ci.com/zhujun98/foamgraph.svg?branch=master)](https://travis-ci.com/zhujun98/foamgraph)

**Motivations** 

* Fast display (> 10 Hz) for XFEL experiments (https://github.com/European-XFEL/EXtra-foam/pull/422#issue-1130537145).
* Customized plots and interactive analysis for photon experiments.
* Reduce the redundant functionalities (for photon experiments) from pyqtgraph and simplify API.

**Architecture**

* Qt's GraphicsView framework

**Challenges**

* When integrating GUI into a real-time data analysis pipeline, there are a couple of things to be taken into account:
    - The GUI in principle should not perform any number crunching jobs, otherwise it will be slowed down because it is written in Python.
    - Light computation tasks can be performed in a Python thread and the communication between the GUI and the processor can still be fulfilled using Qt's signal-slot connections.
    - Heavy computation tasks must be carried out in other processes (servers) and one needs to think about how to synchronize the parameters.

## Examples

* Open a terminal and start the producer:

```sh
python examples/producer.py
```

* Open another terminal and start the galleries

```sh
python examples/plot_gallery.py &
python examples/image_analysis.py
```
