import pytest

import numpy as np

from foamgraph.backend.QtCore import QPointF
from foamgraph.backend.QtGui import QPolygonF
from foamgraph.graphics_item import PlotItem


@pytest.mark.parametrize("n", [1, 5])
def test_array_to_polygon(n):
    x = np.arange(n)
    y = 2 * np.arange(n)

    polygon = PlotItem.array2Polygon(x, y)
    assert isinstance(polygon, QPolygonF)
    assert polygon.size() == n

    for i in range(n):
        assert polygon[i] == QPointF(x[i], y[i])


def test_array_to_polygon_empty_input():
    x = np.array([])
    y = np.array([])

    polygon = PlotItem.array2Polygon(x, y)
    assert isinstance(polygon, QPolygonF)
    assert polygon.size() == 0
