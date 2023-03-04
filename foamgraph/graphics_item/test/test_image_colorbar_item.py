from foamgraph import mkQApp
from foamgraph.graphics_item.image_colorbar_widget import ImageColorbarWidget
from foamgraph.graphics_item.image_item import ImageItem


app = mkQApp()


class TestImageColorbarItem:
    def testGeneral(self):
        image_item = ImageItem()
        ImageColorbarWidget(image_item, parent=None)
