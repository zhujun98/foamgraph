import pytest

from foamgraph.backend.QtCore import Qt
from foamgraph.gradient_editor_widget import GradientEditorWidget


class TestGradientEditorWidget:

    def test_construction_error(self):
        with pytest.raises(ValueError):
            GradientEditorWidget('A')

    @pytest.mark.parametrize("orientation", [Qt.Orientation.Horizontal, Qt.Orientation.Vertical])
    def test_construction(self, orientation):
        widget = GradientEditorWidget(orientation)
