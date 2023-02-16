import pytest

from foamgraph.backend.QtCore import Qt
from foamgraph.graphics_item.gradient_editor_item import GradientEditorItem


class TestGradientEditorItem:

    def test_construction_error(self):
        with pytest.raises(ValueError):
            GradientEditorItem('A')

    @pytest.mark.parametrize("orientation", [Qt.Orientation.Horizontal, Qt.Orientation.Vertical])
    def test_construction(self, orientation):
        widget = GradientEditorItem(orientation)
