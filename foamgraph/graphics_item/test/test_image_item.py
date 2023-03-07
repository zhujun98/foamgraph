import unittest

from foamgraph import mkQApp
from foamgraph import GraphView
from foamgraph.graphics_item import ImageItem

from foamgraph.test import visualize

app = mkQApp()


class TestImageItem(unittest.TestCase):
    def testSetImage(self):
        item = ImageItem()

        # TODO: check test in TestImageView
