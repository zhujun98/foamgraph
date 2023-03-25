import pytest
from unittest.mock import patch

import numpy as np

from foamgraph.backend.QtCore import QRectF
from foamgraph.graph_view import GraphView, ImageView
from foamgraph.graphics_widget import Canvas
from foamgraph.test import processEvents


class TestGraphViewCanvas:
    @pytest.fixture(scope="function")
    def view(self):
        view = GraphView()
        view.show()
        processEvents()
        return view

    @pytest.fixture(scope="function")
    def canvas(self, view):
        return view._cw._canvas

    def test_mouse_mode(self, canvas):
        assert canvas._mouse_mode == canvas.MouseMode.Pan

    def test_context_menu(self, canvas):
        canvas = Canvas()

        action = canvas.getMenuAction("ViewAll")
        with patch.object(canvas, "setTargetRange") as mocked:
            action.trigger()
            mocked.assert_called_once()

        action = canvas.getMenuAction("MouseMode_Zoom")
        action.trigger()
        assert canvas._mouse_mode == canvas.MouseMode.Zoom

        action = canvas.getMenuAction("MouseMode_Off")
        action.trigger()
        assert canvas._mouse_mode == canvas.MouseMode.Off

    def test_item_change(self, view, canvas):
        with patch.object(canvas, "updateAutoRange") as patched:
            plot = view.addCurvePlot()
            # item added
            patched.assert_called_once()
            patched.reset_mock()

            plot.setData([1], [1])
            # informBoundsChanged
            patched.assert_called_once()
            patched.reset_mock()

            view.removeItem(plot)
            # item removed
            patched.assert_called_once()

    def test_bounding_rect(self, view, canvas):
        assert canvas._auto_range_x
        assert canvas._auto_range_y

        assert canvas.targetRect() == QRectF(-0.02, -0.02, 0.04, 0.04)
        assert canvas.viewRect() == QRectF(-0.02, -0.02, 0.04, 0.04)

        plot1 = view.addCurvePlot()
        plot1.setData(np.arange(11), 0.1 * np.arange(11))
        assert canvas.viewRect() == QRectF(-0.1, -0.1, 10.2, 1.2)  # including padding
        assert canvas.targetRect() == canvas.viewRect()

        plot2 = view.addCurvePlot()
        plot2.setData(np.arange(-5, 6), 0.1 * np.arange(-5, 6))
        assert canvas.viewRect() == QRectF(-5.1, -0.6, 15.2, 1.7)  # including padding
        assert canvas.targetRect() == canvas.viewRect()

    def test_bounding_rect_with_aspect_ratio_locked(self, view, canvas):
        canvas.resize(100, 200)
        processEvents()

        plot = view.addCurvePlot()
        plot.setData(np.arange(11), 0.1 * np.arange(11))
        processEvents()
        assert canvas.viewRect() == QRectF(-0.1, -0.1, 10.2, 1.2)

        canvas.setAspectRatioLocked(True)
        processEvents()
        # y-center unchanged -9.7 + 20.4 / 2 == -0.1 + 1.2 / 2
        # y-size / x-size == 2
        assert canvas.viewRect() == QRectF(-0.1, -9.7, 10.2, 20.4)
        assert canvas.targetRect() == QRectF(-0.1, -0.1, 10.2, 1.2)

        # resizeEvent triggers the change of view rect
        canvas.resize(100, 100)
        processEvents()
        assert canvas.viewRect() == QRectF(-0.1, -4.6, 10.2, 10.2)
        assert canvas.targetRect() == QRectF(-0.1, -0.1, 10.2, 1.2)

        canvas.getMenuAction("ViewAll").trigger()
        processEvents()
        assert canvas.viewRect() == QRectF(-0.1, -4.6, 10.2, 10.2)
        # target rect does not change until setTargetRange is called
        assert canvas.targetRect() == QRectF(-0.1, -4.6, 10.2, 10.2)

    def test_close(self, view, canvas):
        view.addCurvePlot()
        view.addAnnotation()
        canvas.close()
        assert not canvas._proxy.childItems()


class TestImageViewCanvas:
    @pytest.fixture(scope="function")
    def view(self):
        view = ImageView()
        view.show()
        processEvents()
        return view

    @pytest.fixture(scope="function")
    def canvas(self, view):
        return view._cw._canvas

    def test_mouse_mode(self, canvas):
        assert canvas._mouse_mode == canvas.MouseMode.Off

    def test_bounding_rect(self, view, canvas):
        canvas.resize(100, 200)
        processEvents()

        img = np.arange(12).reshape(3, 4)
        view.setImage(img)
        processEvents()

        assert canvas.viewRect() == QRectF(-0.1, -2.7, 4.2, 8.4)
        assert canvas.targetRect() == QRectF(-0.1, -2.7, 4.2, 8.4)

        canvas.resize(100, 100)
        processEvents()
        assert canvas.viewRect() == QRectF(-2.2, -2.7, 8.4, 8.4)
        assert canvas.targetRect() == QRectF(-0.1, -2.7, 4.2, 8.4)

        canvas.getMenuAction("ViewAll").trigger()
        processEvents()
        assert canvas.viewRect() == QRectF(-0.1, -0.6, 4.2, 4.2)
