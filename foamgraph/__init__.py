"""
Distributed under the terms of the MIT License.

The full license is in the file LICENSE, distributed with this software.

Copyright (C) Jun Zhu. All rights reserved.
"""
from PyQt5.QtWidgets import QApplication

from .pyqtgraph_be import setConfigOptions

from .config import config
from .scenes import AbstractScene
from .aesthetics import FColor
from .image_views import ImageViewF, TimedImageViewF
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
