import pytest
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from foamgraph import ImageView, mkQApp, TimedImageView
from foamgraph.graphics_item.image_item import ImageItem
from foamgraph.graphics_item.roi import RectROI

from . import _display

app = mkQApp()


class TestImageView:
    def testComponents(self):
        widget = ImageView(n_rois=4)
        items = widget._graph_view._cw._vb._proxy._items
        assert isinstance(items[0], ImageItem)
        for i in range(1, 5):
            assert isinstance(items[i], RectROI)

        widget = ImageView()
        assert len(widget._graph_view._cw._items) == 1

        with pytest.raises(TypeError, match="numpy array"):
            widget.setImage([[1, 2, 3], [4, 5, 6]])

    def testForwardMethod(self):
        widget = ImageView(n_rois=4)

        for method in ["setLabel", "setTitle", "addItem",
                       "removeItem", "invertX", "invertY"]:
            with patch.object(widget._graph_view, method) as mocked:
                getattr(widget, method)()
                mocked.assert_called_once()

    @pytest.mark.parametrize("dtype", [np.uint8, int, np.float32])
    def testSetImage(self, dtype):
        widget = ImageView(n_rois=4)

        if _display():
            widget.show()

        _display()

        # test setImage
        img = np.arange(64).reshape(8, 8).astype(dtype)
        widget.setImage(img, auto_levels=False)
        _display()

        widget.setImage(img, auto_levels=True)
        _display()

        # test setting image to None
        widget.setImage(None)
        assert widget._image is None
        assert widget._image_item._image is None

        _display()


class TestTimedImageView(unittest.TestCase):
    def testUpdate(self):
        view = TimedImageView()
        view.refresh = MagicMock()

        self.assertIsNone(view._data)
        view._refresh_imp()
        view.refresh.assert_not_called()

        view.updateF(1)
        view._refresh_imp()
        view.refresh.assert_called_once()
