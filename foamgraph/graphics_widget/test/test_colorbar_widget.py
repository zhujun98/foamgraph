import pytest

from foamgraph.backend.QtCore import Qt
from foamgraph.graphics_widget import ColorbarWidget


class TestColorbarWidget:

    def test_construction_error(self):
        with pytest.raises(ValueError):
            ColorbarWidget('A')

    @pytest.mark.parametrize("orientation", [Qt.Orientation.Horizontal, Qt.Orientation.Vertical])
    def test_construction(self, orientation):
        widget = ColorbarWidget(orientation)
