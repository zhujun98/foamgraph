from foamgraph.graphics_widget import LabelWidget


class TestLabelItem:
    def test_initialization(self):
        item = LabelWidget("x")

        item.setPlainText("xyz")

