from foamgraph import mkQApp
from foamgraph.graphics_item.image_colorbar_item import ImageColorbarItem
from foamgraph.graphics_item.image_item import ImageItem


app = mkQApp()


class TestImageColorbarItem:
    def testGeneral(self):
        image_item = ImageItem()
        ImageColorbarItem(image_item, parent=None)
