from foamgraph import mkQApp
from foamgraph.image_colorbar_widget import ImageColorbarWidget
from foamgraph.image_items import ImageItem


app = mkQApp()


class TestImageColorbarWidget:
    def testGeneral(self):
        image_item = ImageItem()
        ImageColorbarWidget(image_item, parent=None)
