import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF, QRectF
from foamgraph.graphics_item.plot_item import AnnotationItem

from foamgraph.test import visualize


def test_annotation_item(view):
    item = AnnotationItem()
    view.addItem(item)
