import pytest

import numpy as np

from foamgraph import ImageView
from foamgraph.graphics_item import ImageItem

from foamgraph.test import processEvents


@pytest.fixture
def image_view():
    view = ImageView()
    view.show()
    processEvents()
    yield view
    view.close()


@pytest.fixture
def image_item(image_view):
    return image_view._cw._image_item


@pytest.mark.parametrize("dtype", [np.float64, np.float32, np.uint16])
def test_set_image(image_view, image_item, dtype):
    data = np.arange(24).reshape(6, 4).astype(dtype)
    image_view.setImage(data)
    processEvents()

    if dtype == np.float32:
        image_view.clearData()
        assert image_item._data is None
        assert image_item._qimage is None

        with pytest.raises(ValueError, match="empty array"):
            image_view.setImage(np.array([]))


@pytest.mark.parametrize("colormaps", [("thermal", "grey"), ("grey", "viridis")])
def test_colormap(image_view, colormaps):
    data = np.arange(42).reshape(6, 7).astype(float)
    image_view.setImage(data)
    for cm in colormaps:
        image_view.setColorMap(cm)
        processEvents()


def test_scale_for_display():
    data = np.arange(12).reshape(3, 4).astype(np.float32)

    scaled = ImageItem.scaleForLookUp(data, 2, 10, 16)
    np.testing.assert_array_equal(scaled, np.array([
        [0, 0, 0, 2], [4, 6, 8, 10], [12, 14, 15, 15]
    ]))
    assert scaled.dtype == np.uint8

    scaled = ImageItem.scaleForLookUp(data, 2, 10, 512)
    np.testing.assert_array_equal(scaled, np.array([
        [0, 0, 0, 64], [128, 192, 256, 320], [384, 448, 511, 511]
    ]))
    assert scaled.dtype == np.uint16


def test_regularize_levels():
    v_min, v_max = ImageItem.regularizeLevels(1.0, 2.0)
    assert v_min == 1.0
    assert v_max == 2.0

    v_min, v_max = ImageItem.regularizeLevels(-1.1, -1.0)
    assert v_min == -1.1
    assert v_max == -1.0

    v_min, v_max = ImageItem.regularizeLevels(0, 0)
    assert v_min == 0
    assert 0 < v_max < 1e-8

    v_min, v_max = ImageItem.regularizeLevels(-1.0, -1.0)
    assert v_min == -1.0
    assert -1.0 < v_max < -1.0 + 1e-8
