import pytest
from unittest.mock import patch

from foamgraph import mkQApp
from foamgraph.graphics_widget import Canvas


app = mkQApp()


def test_context_menu():
    canvas = Canvas()

    action = canvas.getMenuAction("ViewAll")
    with patch.object(canvas, "setTargetRange") as mocked:
        action.trigger()
        mocked.assert_called_once()
