import pytest

from foamgraph.backend.QtGui import QFont

from foamgraph.aesthetics import FColor
from foamgraph.graphics_item import AnnotationItem


class TestAnnotationItem:
    def test_initialization(self):
        item = AnnotationItem()
        item.setColor(FColor.mkColor('b'))
        item.setFont(QFont())

    def test_offset(self):
        # TODO:
        ...
