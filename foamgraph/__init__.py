"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from .backend import QtCore, QtGui, QtWidgets
from .backend.QtWidgets import QApplication

from .pyqtgraph_be import setConfigOptions

from .config import config
from .scenes import AbstractScene
from .aesthetics import FColor, createIconButton
from .image_views import ImageViewF, TimedImageViewF
from .logger import GuiLoggingHandler
from .plot_widgets import PlotWidgetF, TimedPlotWidgetF, HistWidgetF
from .ctrl_widgets import (
    SmartLineEdit, SmartStringLineEdit, SmartBoundaryLineEdit,
    SmartIdLineEdit, SmartSliceLineEdit
)

setConfigOptions(
    imageAxisOrder="row-major",
    foreground=config["FOREGROUND_COLOR"],
    background=config["BACKGROUND_COLOR"],
)


def mkQApp(args=None):
    app = QApplication.instance()
    if app is None:
        if args is None:
            return QApplication([])
        return QApplication(args)

    return app
