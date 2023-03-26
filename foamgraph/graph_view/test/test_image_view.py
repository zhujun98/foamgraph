import pytest
import unittest
from unittest.mock import MagicMock, patch

from foamgraph import ImageView, TimedImageView

from foamgraph.test import processEvents


@pytest.fixture
def image_view():
    view = ImageView()
    view.show()
    processEvents()
    return view


class TestImageView:
    def test_forwarded_methods(self, image_view):
        view = image_view
        cw = view._cw

        with patch.object(cw, "clearData") as mocked:
            view.clearData()
            mocked.assert_called_once()

        with patch.object(cw, "addRectROI") as mocked:
            roi = object()
            view.addRectROI(roi)
            mocked.assert_called_once_with(roi)

        with patch.object(cw, "addEllipseROI") as mocked:
            roi = object()
            view.addEllipseROI(roi)
            mocked.assert_called_once_with(roi)

        with patch.object(cw, "setImage") as mocked:
            data = object()
            view.setImage(data)
            mocked.assert_called_once_with(data)

        with patch.object(cw, "setColorMap") as mocked:
            cmap = "plasma"
            view.setColorMap(cmap)
            mocked.assert_called_once_with(cmap)

        with patch.object(cw, "addItem") as mocked:
            item = object()
            view.addItem(item)
            mocked.assert_called_once_with(item)

        with patch.object(cw, "removeItem") as mocked:
            item = object()
            view.removeItem(item)
            mocked.assert_called_once_with(item)


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
