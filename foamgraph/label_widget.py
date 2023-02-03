"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from .backend.QtCore import QPointF, QSizeF, Qt
from .backend.QtWidgets import QGraphicsTextItem
from . import pyqtgraph_be as pg


class LabelWidget(pg.GraphicsAnchorWidget):
    """
    GraphicsWidget displaying text.
    Used mainly as axis labels, titles, etc.
    
    Note: To display text inside a scaled view (ViewBox, PlotWidget, etc) use TextItem
    """
    def __init__(self, text=' ', parent=None, angle=0):
        super().__init__(parent=parent)
        self.item = QGraphicsTextItem(self)
        self.opts = {
            'color': None,
            'justify': 'center'
        }
        self._sizeHint = {}
        self.setText(text)
        self.setAngle(angle)
        
    def setText(self, text, **args):
        """Set the text and text properties in the label. Accepts optional arguments for auto-generating
        a CSS style string:

        ==================== ==============================
        **Style Arguments:**
        color                (str) example: 'CCFF00'
        size                 (str) example: '8pt'
        bold                 (bool)
        italic               (bool)
        ==================== ==============================
        """
        self.text = text
        opts = self.opts
        for k in args:
            opts[k] = args[k]
        
        optlist = []
        
        color = self.opts['color']
        if color is None:
            color = getConfigOption('foreground')
        color = fn.mkColor(color)
        optlist.append('color: #' + fn.colorStr(color)[:6])
        if 'size' in opts:
            optlist.append('font-size: ' + opts['size'])
        if 'bold' in opts and opts['bold'] in [True, False]:
            optlist.append('font-weight: ' + {True:'bold', False:'normal'}[opts['bold']])
        if 'italic' in opts and opts['italic'] in [True, False]:
            optlist.append('font-style: ' + {True:'italic', False:'normal'}[opts['italic']])
        full = "<span style='%s'>%s</span>" % ('; '.join(optlist), text)
        self.item.setHtml(full)
        self.updateMin()
        self.resizeEvent(None)
        self.updateGeometry()
        
    def resizeEvent(self, ev):
        self.item.setPos(0,0)
        bounds = self.itemRect()
        left = self.mapFromItem(self.item, QPointF(0,0)) - self.mapFromItem(self.item, QPointF(1,0))
        rect = self.rect()
        
        if self.opts['justify'] == 'left':
            if left.x() != 0:
                bounds.moveLeft(rect.left())
            if left.y() < 0:
                bounds.moveTop(rect.top())
            elif left.y() > 0:
                bounds.moveBottom(rect.bottom())
                
        elif self.opts['justify'] == 'center':
            bounds.moveCenter(rect.center())

        elif self.opts['justify'] == 'right':
            if left.x() != 0:
                bounds.moveRight(rect.right())
            if left.y() < 0:
                bounds.moveBottom(rect.bottom())
            elif left.y() > 0:
                bounds.moveTop(rect.top())
            
        self.item.setPos(bounds.topLeft() - self.itemRect().topLeft())
        self.updateMin()
        
    def setAngle(self, angle):
        self.angle = angle
        self.item.resetTransform()
        self.item.rotate(angle)
        self.updateMin()

    def updateMin(self):
        bounds = self.itemRect()
        self.setMinimumWidth(bounds.width())
        self.setMinimumHeight(bounds.height())
        
        self._sizeHint = {
            Qt.SizeHint.MinimumSize: (bounds.width(), bounds.height()),
            Qt.SizeHint.PreferredSize: (bounds.width(), bounds.height()),
            Qt.SizeHint.MaximumSize: (-1, -1),  #bounds.width()*2, bounds.height()*2),
            Qt.SizeHint.MinimumDescent: (0, 0)  ##?? what is this?
        }
        self.updateGeometry()
        
    def sizeHint(self, hint, constraint):
        if hint not in self._sizeHint:
            return QSizeF(0, 0)
        return QSizeF(*self._sizeHint[hint])
        
    def itemRect(self):
        return self.item.mapRectToParent(self.item.boundingRect())
