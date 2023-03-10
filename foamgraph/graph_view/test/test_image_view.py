import pytest
import unittest
from unittest.mock import MagicMock, patch

from foamgraph import ImageView, mkQApp, TimedImageView

from foamgraph.test import visualize

app = mkQApp()


@pytest.fixture
def image_view():
    view = ImageView()
    if visualize():
        view.show()
    return view


class TestImageView:
    def test_forwarded_methods(self, image_view):
        view = image_view
        cw = view._cw

        with patch.object(cw, "clearData") as mocked:
            view.clearData()
            mocked.assert_called_once()

        with patch.object(cw, "addROI") as mocked:
            roi = object()
            view.addROI(roi)
            mocked.assert_called_once_with(roi)

        with patch.object(cw, "setImage") as mocked:
            data = object()
            view.setImage(data)
            mocked.assert_called_once_with(data)

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
