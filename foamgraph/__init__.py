"""
Distributed under the terms of the MIT License.

The full license is in the file LICENSE, distributed with this software.

Copyright (C) Jun Zhu. All rights reserved.
"""
from PyQt5.QtWidgets import QApplication

from .aesthetics import *
from .image_views import *
from .plot_widgets import *
from .smart_widgets import *

__all__ = []
__all__ += aesthetics.__all__
__all__ += image_views.__all__
__all__ += plot_widgets.__all__
__all__ += smart_widgets.__all__

__version__ = "0.0.1"


def mkQApp(args=None):
    app = QApplication.instance()
    if app is None:
        if args is None:
            return QApplication([])
        return QApplication(args)

    return app
