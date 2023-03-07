from ..backend.QtGui import QPainter, QTransform
from ..backend.QtWidgets import QGraphicsPathItem

from ..aesthetics import FColor


class ArrowItem(QGraphicsPathItem):
    """
    For displaying scale-invariant arrows.
    For arrows pointing to a location on a curve, see CurveArrow
    
    """
    def __init__(self, **opts):
        """
        Arrows can be initialized with any keyword arguments accepted by 
        the setStyle() method.
        """
        self.opts = {}
        QGraphicsPathItem.__init__(self, opts.get('parent', None))

        if 'size' in opts:
            opts['headLen'] = opts['size']
        if 'width' in opts:
            opts['headWidth'] = opts['width']
        defaultOpts = {
            'pxMode': True,
            'angle': -150,   ## If the angle is 0, the arrow points left
            'pos': (0,0),
            'headLen': 20,
            'headWidth': None,
            'tipAngle': 25,
            'baseAngle': 0,
            'tailLen': None,
            'tailWidth': 3,
            'pen': (200,200,200),
            'brush': (50,50,200),
        }
        defaultOpts.update(opts)
        
        self.setStyle(**defaultOpts)
        
        self.moveBy(*self.opts['pos'])
    
    def setStyle(self, **opts):
        """
        Changes the appearance of the arrow.
        All arguments are optional:
        
        ======================  =================================================
        **Keyword Arguments:**
        angle                   Orientation of the arrow in degrees. Default is
                                0; arrow pointing to the left.
        headLen                 Length of the arrow head, from tip to base.
                                default=20
        headWidth               Width of the arrow head at its base. If
                                headWidth is specified, it overrides tipAngle.
        tipAngle                Angle of the tip of the arrow in degrees. Smaller
                                values make a 'sharper' arrow. default=25
        baseAngle               Angle of the base of the arrow head. Default is
                                0, which means that the base of the arrow head
                                is perpendicular to the arrow tail.
        tailLen                 Length of the arrow tail, measured from the base
                                of the arrow head to the end of the tail. If
                                this value is None, no tail will be drawn.
                                default=None
        tailWidth               Width of the tail. default=3
        pen                     The pen used to draw the outline of the arrow.
        brush                   The brush used to fill the arrow.
        ======================  =================================================
        """
        self.opts.update(opts)
        
        opt = dict([(k,self.opts[k]) for k in ['headLen', 'headWidth', 'tipAngle', 'baseAngle', 'tailLen', 'tailWidth']])
        tr = QTransform()
        tr.rotate(self.opts['angle'])
        self.path = tr.map(self._makeArrowPath(**opt))

        self.setPath(self.path)
        
        self.setPen(FColor.mkPen())
        self.setBrush(FColor.mkBrush())
        
        if self.opts['pxMode']:
            self.setFlags(self.flags() | self.ItemIgnoresTransformations)
        else:
            self.setFlags(self.flags() & ~self.ItemIgnoresTransformations)

    def makeArrowPath(headLen=20, headWidth=None, tipAngle=20, tailLen=20, tailWidth=3, baseAngle=0):
        """
        Construct a path outlining an arrow with the given dimensions.
        The arrow points in the -x direction with tip positioned at 0,0.
        If *headWidth* is supplied, it overrides *tipAngle* (in degrees).
        If *tailLen* is None, no tail will be drawn.
        """
        if headWidth is None:
            headWidth = headLen * np.tan(tipAngle * 0.5 * np.pi / 180.)
        path = QtGui.QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(headLen, -headWidth)
        if tailLen is None:
            innerY = headLen - headWidth * np.tan(baseAngle * np.pi / 180.)
            path.lineTo(innerY, 0)
        else:
            tailWidth *= 0.5
            innerY = headLen - (headWidth - tailWidth) * np.tan(baseAngle * np.pi / 180.)
            path.lineTo(innerY, -tailWidth)
            path.lineTo(headLen + tailLen, -tailWidth)
            path.lineTo(headLen + tailLen, tailWidth)
            path.lineTo(innerY, tailWidth)
        path.lineTo(headLen, headWidth)
        path.lineTo(0, 0)
        return path

    def paint(self, p, *args):
        """Override."""
        p.setRenderHint(QPainter.Antialiasing)
        QGraphicsPathItem.paint(self, p, *args)

    def shape(self):
        return self.path
    
    # # dataBounds and pixelPadding methods are provided to ensure Canvas can
    # # properly auto-range
    # def dataBounds(self, ax, orthoRange=None):
    #     pw = 0
    #     pen = self.pen()
    #     if not pen.isCosmetic():
    #         pw = pen.width() * 0.7072
    #     if self.opts['pxMode']:
    #         return [0,0]
    #     else:
    #         br = self.boundingRect()
    #         if ax == 0:
    #             return [br.left()-pw, br.right()+pw]
    #         else:
    #             return [br.top()-pw, br.bottom()+pw]
        
    def pixelPadding(self):
        pad = 0
        if self.opts['pxMode']:
            br = self.boundingRect()
            pad += (br.width()**2 + br.height()**2) ** 0.5
        pen = self.pen()
        if pen.isCosmetic():
            pad += max(1, pen.width()) * 0.7072
        return pad
