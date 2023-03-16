import pytest

from foamgraph import mkQApp
from foamgraph.backend.QtCore import Qt
from foamgraph.graphics_widget import AxisWidget

app = mkQApp()


def test_context_menu():
    axis = AxisWidget(Qt.Edge.BottomEdge)

    auto_range_action = axis.getMenuAction("AutoRange")
    invert_axis_action = axis.getMenuAction("InvertAxis")
    show_grid_action = axis.getMenuAction("ShowGrid")
    log_scale_action = axis.getMenuAction("LogScale")
