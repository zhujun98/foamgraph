import pytest

import numpy as np

from foamgraph.graphics_item import AnnotationItem

from foamgraph.test import processEvents


def test_input_data_parsing(view):
    x = y = annotations = np.arange(10)

    # x and y are lists
    item = AnnotationItem(x.tolist(), y.tolist(), annotations.tolist())
    view.addItem(item)
    view.addLegend()
    assert isinstance(item._x, np.ndarray)
    assert isinstance(item._y, np.ndarray)
    assert isinstance(item._annotations, np.ndarray)

    # test different lengths
    right, wrong = np.arange(2), np.arange(3)

    with pytest.raises(ValueError, match="different lengths"):
        AnnotationItem(right, right, wrong)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, wrong, right)

    with pytest.raises(ValueError, match="different lengths"):
        item.setData(right, right, wrong)


@pytest.fixture
def item(view):
    item = view.addAnnotation(label="annotation")
    view.addLegend()
    return item


def test_plot(item):
    x = np.arange(10).astype(float)
    y = np.arange(10).astype(float)
    annotations = ['text'] * 10

    item.setData(x, y, annotations)
    processEvents()

    item.clearData()
    processEvents()
