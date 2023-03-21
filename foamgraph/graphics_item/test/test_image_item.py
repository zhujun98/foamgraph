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


class TestImageItem:
    @pytest.mark.parametrize("dtype", [np.float64, np.float32, np.uint16])
    def test_set_image(self, image_view, dtype):
        data = np.arange(24).reshape(6, 4).astype(dtype)
        image_view.setImage(data)
        image_view.update()
        processEvents()

    @pytest.mark.parametrize("colormaps", [("thermal", "grey"), ("grey", "viridis")])
    def test_colormap(self, image_view, colormaps):
        data = np.arange(42).reshape(6, 7).astype(float)
        image_view.setImage(data)
        for cm in colormaps:
            image_view.setColorMap(cm)
            processEvents()

    def test_scale_for_display(self):
        data = np.arange(12).reshape(3, 4).astype(np.float32)

        scaled = ImageItem.scaleForDisplay(data, 2, 10, 16)
        np.testing.assert_array_equal(scaled, np.array([
            [0, 0, 0, 2], [4, 6, 8, 10], [12, 14, 15, 15]
        ]))
        assert scaled.dtype == np.uint8

        scaled = ImageItem.scaleForDisplay(data, 2, 10, 512)
        np.testing.assert_array_equal(scaled, np.array([
            [0, 0, 0, 64], [128, 192, 256, 320], [384, 448, 511, 511]
        ]))
        assert scaled.dtype == np.uint16
