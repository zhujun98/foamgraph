import pytest
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from foamgraph import ImageViewF, mkQApp, TimedImageViewF
from foamgraph.image_items import ImageItem
from foamgraph.roi import RectROI

from . import _display

app = mkQApp()


class TestImageView:
    def testComponents(self):
        widget = ImageViewF(n_rois=4)
        items = widget._plot_widget._plot_area._vb._items
        assert isinstance(items[0], ImageItem)
        for i in range(1, 5):
            assert isinstance(items[i], RectROI)

        widget = ImageViewF()
        assert len(widget._plot_widget._plot_area._items) == 1

        with pytest.raises(TypeError, match="numpy array"):
            widget.setImage([[1, 2, 3], [4, 5, 6]])

        # test log X/Y menu is disabled
        menu = widget._plot_widget._plot_area.getContextMenus(None)
        assert len(menu) == 0

    def testForwardMethod(self):
        widget = ImageViewF(n_rois=4)

        for method in ["setAspectLocked", "setLabel", "setTitle", "addItem",
                       "removeItem", "invertX", "invertY", "autoRange"]:
            with patch.object(widget._plot_widget, method) as mocked:
                getattr(widget, method)()
                mocked.assert_called_once()

    @pytest.mark.parametrize("dtype", [np.uint8, int, np.float32])
    def testSetImage(self, dtype):
        widget = ImageViewF(n_rois=4)

        if _display():
            widget.show()

        _display()

        # test setImage
        img = np.arange(64).reshape(8, 8).astype(dtype)
        widget.setImage(img, auto_range=False, auto_levels=False)
        _display()

        widget.setImage(img, auto_range=True, auto_levels=True)
        _display()

        # test setting image to None
        widget.setImage(None)
        assert widget._image is None
        assert widget._image_item._image is None

        _display()


class TestTimedImageView(unittest.TestCase):
    def testUpdate(self):
        view = TimedImageViewF()
        view.refresh = MagicMock()

        self.assertIsNone(view._data)
        view._refresh_imp()
        view.refresh.assert_not_called()

        view.updateF(1)
        view._refresh_imp()
        view.refresh.assert_called_once()
