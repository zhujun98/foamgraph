"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from .backend import QtCore, QtGui, QtWidgets, mkQApp

from .live_window import LiveWindow
from .aesthetics import FColor, createIconButton
from .graph_view import (
    GraphView, ImageView, TimedGraphView, TimedImageView
)
from .ctrl_widgets import (
    SmartLineEdit, SmartStringLineEdit, SmartBoundaryLineEdit,
    SmartIdLineEdit, SmartSliceLineEdit
)
from .widgets import Section
from .version import __version__
