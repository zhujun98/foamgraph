"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""

from .graph_widget import GraphWidget


class SmartGraphWidget(GraphWidget):
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)

    def _extendCanvasContextMenu(self):
        """Override."""
        super()._extendCanvasContextMenu()

        menu = self._canvas.extendContextMenu("Analysis type")
        menu = self._canvas.extendContextMenu("Plot type")
