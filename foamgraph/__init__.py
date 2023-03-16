"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from .backend import QtCore, QtGui, QtWidgets

from .scenes import AbstractScene
from .aesthetics import FColor, createIconButton
from .graph_view import (
    GraphView, ImageView, TimedGraphView, TimedImageView
)
from .ctrl_widgets import (
    SmartLineEdit, SmartStringLineEdit, SmartBoundaryLineEdit,
    SmartIdLineEdit, SmartSliceLineEdit
)


def mkQApp(args=None):
    app = QtGui.QApplication.instance()
    if app is None:
        if args is None:
            return QtGui.QApplication([])
        return QtGui.QApplication(args)

    return app
