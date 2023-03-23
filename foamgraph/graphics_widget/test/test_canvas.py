import pytest
from unittest.mock import patch

import numpy as np

from foamgraph.backend.QtCore import QRectF
from foamgraph.graph_view import GraphView, ImageView
from foamgraph.graphics_widget import Canvas
from foamgraph.test import processEvents


class TestGraphViewCanvas:
    @pytest.fixture(scope="class")
    def view(self):
        view = GraphView()
        processEvents()
        return view

    @pytest.fixture(scope="class")
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

        assert canvas.targetRect() == QRectF(-0.5, -0.5, 1.0, 1.0)
        assert canvas.viewRect() == QRectF(-0.5, -0.5, 1.0, 1.0)

        plot1 = view.addCurvePlot()
        plot1.setData(np.arange(11), 0.1 * np.arange(11))
        assert canvas.viewRect() == QRectF(-0.1, -0.1, 10.2, 1.2)  # including padding
        assert canvas.targetRect() == canvas.viewRect()

        plot2 = view.addCurvePlot()
        plot2.setData(np.arange(-5, 6), 0.1 * np.arange(-5, 6))
        assert canvas.viewRect() == QRectF(-5.1, -0.6, 15.2, 1.7)  # including padding
        assert canvas.targetRect() == canvas.viewRect()

    def test_bouding_rect_with_aspect_ratio_locked(self, view, canvas):
        ...


class TestImageViewCanvas:
    @pytest.fixture(scope="class")
    def view(self):
        view = ImageView()
        processEvents()
        return view

    @pytest.fixture(scope="class")
    def canvas(self, view):
        return view._cw._canvas

    def test_mouse_mode(self, canvas):
        assert canvas._mouse_mode == canvas.MouseMode.Off

    def test_bounding_rect(self, view, canvas):
        img = np.arange(12).reshape(3, 4)
        view.setImage(img)
