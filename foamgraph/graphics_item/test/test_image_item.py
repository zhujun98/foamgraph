import unittest

import numpy as np

from foamgraph import mkQApp
from foamgraph import GraphView
from foamgraph.graphics_item import ImageItem

from foamgraph.test import visualize

app = mkQApp()


class TestImageItem(unittest.TestCase):
    def test_setimage(self):
        item = ImageItem()

        # TODO: check test in TestImageView

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
