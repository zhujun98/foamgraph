"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtCore import QPointF, QRectF, QSizeF, Qt
from ..backend.QtGui import QColor, QGraphicsSceneResizeEvent
from ..backend.QtWidgets import QGraphicsTextItem

from ..aesthetics import FColor
from .graphics_item import GraphicsWidget


class LabelItem(GraphicsWidget):
    """GraphicsWidget as axis labels, graph titles, etc."""
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self._item = QGraphicsTextItem(text, parent=self)

        self.setPlainText(text)

        self._color = FColor.mkColor('foreground')
        self.setColor(self._color)

    def setColor(self, color: QColor) -> None:
        self._item.setDefaultTextColor(color)

    def setPlainText(self, text: str):
        self._item.setPlainText(text)

    def toPlainText(self) -> str:
        return self._item.toPlainText()

    def boundingRect(self) ->QRectF:
        """Override."""
        return self._item.boundingRect()

    def sizeHint(self, which: Qt.SizeHint, constraint: QSizeF) -> QSizeF:
        """Override."""
        return self._item.boundingRect().size()
