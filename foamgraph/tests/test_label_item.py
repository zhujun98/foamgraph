import pytest

from foamgraph.label_item import LabelItem


class TestLabelItem:
    def test_initialization(self):
        item = LabelItem("x")

        item.setPlainText("xyz")

