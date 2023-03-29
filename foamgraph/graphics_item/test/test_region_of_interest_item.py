import pytest

from foamgraph.backend.QtCore import QRectF
from foamgraph.backend.QtWidgets import QAction, QWidgetAction
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


@pytest.fixture(params=[EllipseROI, RectROI])
def roi(iwidget, request):
    item = iwidget._addROI(request.param, 5, 10, 100, 200)
    processEvents()
    return item


@pytest.mark.parametrize("roi_type", [EllipseROI, RectROI])
def test_rect_roi(iwidget, roi_type):
    roi = iwidget._addROI(roi_type, 0, 0, 10, 10, name="ROI1")
    assert isinstance(roi, roi_type)
    assert roi._name == "ROI1"


def test_context_menu(roi):
    widget = roi._menu.findChild(QWidgetAction, "Geometry_Editor").defaultWidget()
    assert widget._width_le.value() == '100'
    assert widget._height_le.value() == '200'
    assert widget._px_le.value() == '5'
    assert widget._py_le.value() == '10'

    widget._width_le.setText("150")
    assert roi.rect() == (5, 10, 150, 200)
    widget._height_le.setText("100")
    assert roi.rect() == (5, 10, 150, 100)
    widget._px_le.setText("0")
    assert roi.rect() == (0, 10, 150, 100)
    widget._py_le.setText("-5")
    assert roi.rect() == (0, -5, 150, 100)
