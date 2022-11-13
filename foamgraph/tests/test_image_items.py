import unittest

from foamgraph import mkQApp
from foamgraph import PlotWidgetF
from foamgraph.image_items import ImageItem, RingItem

from . import _display

app = mkQApp()


class TestImageItem(unittest.TestCase):
    def testSetImage(self):
        item = ImageItem()

        # TODO: check test in TestImageView


class TestGeometryItem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._widget = PlotWidgetF()
        if _display():
            cls._widget.show()

    def testRingItem(self):
        item = RingItem()
        self._widget.addItem(item)
        _display()

        item.setGeometry(100, 100, [50, 100])
        _display()

        item.clearGeometry()
        _display()
