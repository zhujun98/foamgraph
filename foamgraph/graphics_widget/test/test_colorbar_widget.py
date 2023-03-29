import pytest
from unittest.mock import patch

from foamgraph.backend.QtCore import Qt
from foamgraph.backend.QtWidgets import QWidgetAction
from foamgraph.graphics_widget import ColorbarWidget
from foamgraph.aesthetics import ColorMap
from foamgraph.test import processEvents


@pytest.mark.parametrize("orientation", [Qt.Orientation.Horizontal,
                                         Qt.Orientation.Vertical,
                                         'A'])
def test_construction(orientation):
    if orientation == 'A':
        with pytest.raises(ValueError, match="Unknown orientation"):
            ColorbarWidget(orientation)
    else:
        ColorbarWidget(orientation)


def test_context_menu():
    widget = ColorbarWidget()

    for name in ColorMap.gradients:
        action = widget._menu.findChild(QWidgetAction, name)
        with patch.object(widget, "setColorMap") as patched:
            action.triggered.emit()
            patched.assert_called_once_with(name)
