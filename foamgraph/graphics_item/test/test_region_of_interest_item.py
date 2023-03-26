import pytest


from foamgraph import ImageView
from foamgraph.graphics_item import EllipseROI, RectROI

from foamgraph.test import processEvents


@pytest.fixture
def iwidget():
    view = ImageView()
    view.show()
    processEvents()
    yield view._cw
    view.close()


def test_rect_roi(iwidget):
    roi = iwidget.addRectROI()
    assert isinstance(roi, RectROI)


def test_ellipse_roi(iwidget):
    roi = iwidget.addEllipseROI()
    assert isinstance(roi, EllipseROI)
