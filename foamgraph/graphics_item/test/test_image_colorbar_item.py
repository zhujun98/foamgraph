from foamgraph import mkQApp
from foamgraph.graphics_item import ImageItem
from foamgraph.graphics_widget import ColorbarWidget


app = mkQApp()


class TestColorbarWidget:
    def testGeneral(self):
        image_item = ImageItem()
        # ColorbarWidget(image_item, parent=None)
