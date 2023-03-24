import numpy as np

from ..backend.QtCore import pyqtSignal, QLineF, QPointF, QRectF, Qt
from ..backend.QtGui import QAction, QPen, QPicture, QPainter
from ..backend.QtWidgets import (
    QCheckBox, QGraphicsSceneResizeEvent, QGraphicsSceneWheelEvent,
    QGridLayout, QMenu, QGraphicsTextItem, QWidget, QWidgetAction
)

from ..aesthetics import FColor
from ..graphics_scene import MouseClickEvent, MouseDragEvent
from .graphics_widget import GraphicsWidget


class AxisWidget(GraphicsWidget):
    """A single plot axis with ticks, values, and label."""

    log_Scale_toggled_sgn = pyqtSignal(bool)

    def __init__(self, edge: Qt.Edge, *, parent=None, debug=False):
        """Initialization.

        :param edge: location of the axis.
        """
        super().__init__(parent=parent)

        self._range = [0, 1]

        self._label = QGraphicsTextItem(self)
        self._picture = None

        self._edge = edge
        if edge in [Qt.Edge.TopEdge, Qt.Edge.BottomEdge]:
            self._orientation = Qt.Orientation.Horizontal
        else:
            self._orientation = Qt.Orientation.Vertical
            self._label.setRotation(-90)

        # Negative values draw into the plot, positive values draw outward.
        self._tick_length = -5
        self._tick_text_offset = (5, 2)  # reserved spacing between text and axis in px
        self._tick_text_width = 30  # Horizontal space reserved for tick text in px
        self._tick_text_height = 10  # Vertical space reserved for tick text in px
        # Automatically expand text space if the tick strings become too long.
        self._auto_expand_text_space = True
        self._tick_font = None  # the font used for tick values. Use None for the default font.
        self._show_values = True  # indicates whether text is displayed adjacent to ticks.
        self._max_tick_level = 2
        self._max_text_level = 2
        # (list of (tick #, % fill) tuples). This structure
        #                             determines how the AxisWidget decides how many ticks
        #                             should have text appear next to them. Each tuple in
        #                             the list specifies what fraction of the axis length
        #                             may be occupied by text, given the number of ticks
        #                             that already have text displayed.
        self._text_fill_limits =  [  # how much of the axis to fill up with tick text, maximally.
                (0, 0.8),    # never fill more than 80% of the axis
                (2, 0.6),    # If we already have 2 ticks with text, fill no more than 60% of the axis
                (4, 0.4),    # If we already have 4 ticks with text, fill no more than 40% of the axis
                (6, 0.2),    # If we already have 6 ticks with text, fill no more than 20% of the axis
                ]

        self.textWidth = 30  # Keeps track of maximum width / height of tick text
        self.textHeight = 18

        # If the user specifies a width / height, remember that setting
        # indefinitely.
        self.fixedWidth = None
        self.fixedHeight = None

        self.labelText = ""
        self._log_scale = False

        self._tickLevels = None  # used to override the automatic ticking system with explicit ticks
        self._tickSpacing = None  # used to override default tickSpacing method
        self.scale = 1.0

        self.showLabel(False)

        self._tick_pen = None
        self.setTickPen(FColor.mkPen('foreground'))

        self._tick_label_pen = None
        self.setTickLabelPen(FColor.mkPen('foreground'))

        self._vb = None

        self._menu = self.initMenu()
        self._auto_range_act = self.getMenuAction("AutoRange")
        self._invert_axis_act = self.getMenuAction("InvertAxis")
        self._show_grid_act = self.getMenuAction("ShowGrid")
        self._log_scale_act = self.getMenuAction("LogScale")

    def initMenu(self):
        menu = QMenu()
        action = menu.addAction("Auto Range")
        action.setObjectName("AutoRange")
        action.setCheckable(True)

        action = menu.addAction("Invert Axis")
        action.setObjectName("InvertAxis")
        action.setCheckable(True)

        action = menu.addAction("Show Grid")
        action.setObjectName("ShowGrid")
        action.setCheckable(True)
        action.toggled.connect(self.onShowGridToggled)

        action = menu.addAction("Log Scale")
        action.setObjectName("LogScale")
        action.setCheckable(True)
        action.toggled.connect(self.onLogScaleToggled)

        return menu

    def getMenuAction(self, name: str) -> QAction:
        return self._menu.findChild(QAction, name)

    def logScale(self) -> bool:
        return self._log_scale

    def onShowGridToggled(self):
        self._picture = None
        self.prepareGeometryChange()
        self.update()

    def onLogScaleToggled(self, state: bool):
        self._log_scale = state
        self.log_Scale_toggled_sgn.emit(state)
        self._picture = None
        self.update()

    def setTickFont(self, font):
        """
        (QFont or None) Determines the font used for tick values.
        Use None for the default font.
        """
        self._tick_font = font
        self._picture = None
        self.prepareGeometryChange()

        self.update()

    def resizeEvent(self, ev: QGraphicsSceneResizeEvent) -> None:
        """Override."""
        nudge = 5
        br = self._label.boundingRect()
        p = QPointF(0, 0)
        if self._edge == Qt.Edge.LeftEdge:
            p.setY(int(self.size().height()/2 + br.width()/2))
            p.setX(-nudge)
        elif self._edge == Qt.Edge.RightEdge:
            p.setY(int(self.size().height()/2 + br.width()/2))
            p.setX(int(self.size().width()-br.height()+nudge))
        elif self._edge == Qt.Edge.TopEdge:
            p.setY(-nudge)
            p.setX(int(self.size().width()/2. - br.width()/2.))
        elif self._edge == Qt.Edge.BottomEdge:
            p.setX(int(self.size().width()/2. - br.width()/2.))
            p.setY(int(self.size().height()-br.height()+nudge))
        else:
            raise RuntimeError

        self._label.setPos(p)
        self._picture = None

    def showLabel(self, visible: bool = True):
        """Show/hide the label text for this axis."""
        self._label.setVisible(visible)
        if self._orientation == Qt.Orientation.Vertical:
            self._updateWidth()
        else:
            self._updateHeight()

    def setLabel(self, text=None):
        """Set the text displayed adjacent to the axis."""
        show_label = False
        if text is not None:
            self.labelText = text
            show_label = True
        if show_label:
            self.showLabel()
        self._label.setPlainText(text)
        self._adjustSize()
        self._picture = None
        # self.resizeEvent()

    def _updateMaxTextSize(self, x):
        # Informs that the maximum tick size orthogonal to the axis has
        # changed; we use this to decide whether the item needs to be resized
        # to accomodate.
        if self._orientation == Qt.Orientation.Vertical:
            mx = max(self.textWidth, x)
            if mx > self.textWidth or mx < self.textWidth-10:
                self.textWidth = mx
                if self._auto_expand_text_space:
                    self._updateWidth()
        else:
            mx = max(self.textHeight, x)
            if mx > self.textHeight or mx < self.textHeight-10:
                self.textHeight = mx
                if self._auto_expand_text_space:
                    self._updateHeight()

    def _adjustSize(self):
        if self._orientation == Qt.Orientation.Vertical:
            self._updateWidth()
        else:
            self._updateHeight()

    def setHeight(self, h=None):
        """Set the height of this axis reserved for ticks and tick labels.
        The height of the axis label is automatically added.

        If *height* is None, then the value will be determined automatically
        based on the size of the tick text."""
        self.fixedHeight = h
        self._updateHeight()

    def _updateHeight(self):
        if not self.isVisible():
            h = 0
        else:
            if self.fixedHeight is None:
                if not self._show_values:
                    h = 0
                elif self._auto_expand_text_space is True:
                    h = self.textHeight
                else:
                    h = self._tick_text_height
                h += self._tick_text_offset[1] if self._show_values else 0
                h += max(0, self._tick_length)
                if self._label.isVisible():
                    h += self._label.boundingRect().height() * 0.8
            else:
                h = self.fixedHeight

        self.setMaximumHeight(h)
        self.setMinimumHeight(h)
        self._picture = None

    def setWidth(self, w=None):
        """Set the width of this axis reserved for ticks and tick labels.
        The width of the axis label is automatically added.

        If *width* is None, then the value will be determined automatically
        based on the size of the tick text."""
        self.fixedWidth = w
        self._updateWidth()

    def _updateWidth(self):
        if not self.isVisible():
            w = 0
        else:
            if self.fixedWidth is None:
                if not self._show_values:
                    w = 0
                elif self._auto_expand_text_space is True:
                    w = self.textWidth
                else:
                    w = self._tick_text_width
                w += self._tick_text_offset[0] if self._show_values else 0
                w += max(0, self._tick_length)
                if self._label.isVisible():
                    w += self._label.boundingRect().height() * 0.8  # bounding rect is usually an overestimate
            else:
                w = self.fixedWidth

        self.setMaximumWidth(w)
        self.setMinimumWidth(w)
        self._picture = None

    def setTickPen(self, pen: QPen) -> None:
        """Set the pen used to draw the ticks."""
        # self._picture = None
        self._tick_pen = pen
        self.update()

    def setTickLabelPen(self, pen: QPen) -> None:
        """Set the pen used to draw the tick labels."""
        # self._picture = None
        self._tick_label_pen = pen
        self.update()

    def setRange(self, vmin: float, vmax: float) -> None:
        """Set the range of values displayed by the axis."""
        self._range = [vmin, vmax]
        self._picture = None
        self.update()

    def linkToCanvas(self, canvas: "Canvas"):
        """Link the axis to a Canvas."""
        if self._vb is not None:
            raise RuntimeError(
                "The axis has already been linked to a Canvas.")

        self._vb = canvas
        if self._orientation == Qt.Orientation.Vertical:
            self._auto_range_act.triggered.connect(
                lambda s: canvas.enableAutoRangeY(s))
            self._invert_axis_act.triggered.connect(canvas.invertY)

            canvas.auto_range_y_toggled_sgn.connect(
                self._auto_range_act.setChecked)
            canvas.y_link_state_toggled_sgn.connect(
                self._auto_range_act.setEnabled)
            canvas.y_range_changed_sgn.connect(self.onCanvasChanged)

        else:
            self._auto_range_act.triggered.connect(
                lambda s: canvas.enableAutoRangeX(s))
            self._invert_axis_act.triggered.connect(canvas.invertX)

            canvas.auto_range_x_toggled_sgn.connect(self._auto_range_act.setChecked)
            canvas.x_link_state_toggled_sgn.connect(self._auto_range_act.setEnabled)
            canvas.x_range_changed_sgn.connect(self.onCanvasChanged)

        self._auto_range_act.setChecked(True)
        self._auto_range_act.triggered.emit(True)

    def onCanvasChanged(self) -> None:
        rect = self._vb.viewRect()
        if self._orientation == Qt.Orientation.Vertical:
            vmin, vmax = rect.top(), rect.bottom()
        else:
            vmin, vmax = rect.left(), rect.right()

        if self._invert_axis_act.isChecked():
            self.setRange(vmax, vmin)
        else:
            self.setRange(vmin, vmax)

    def boundingRect(self) -> QRectF:
        """Override."""
        canvas = self._vb
        if canvas is None or not self._show_grid_act.isChecked():
            rect = self.mapRectFromParent(self.geometry())
            # extend rect if ticks go in negative direction
            # also extend to account for text that flows past the edges
            tl = self._tick_length
            if self._edge == Qt.Edge.LeftEdge:
                return rect.adjusted(0, -15, -min(0, tl), 15)
            if self._edge == Qt.Edge.RightEdge:
                return rect.adjusted(min(0, tl), -15, 0, 15)
            if self._edge == Qt.Edge.TopEdge:
                return rect.adjusted(-15, 0, 15, -min(0, tl))
            if self._edge == Qt.Edge.BottomEdge:
                return rect.adjusted(-15, min(0, tl), 15, 0)
            return rect

        return self.mapRectFromParent(
            self.geometry()) | canvas.mapRectToItem(self, canvas.boundingRect())

    def paint(self, p, *args) -> None:
        """Override."""
        if self._picture is None:
            try:
                picture = QPicture()
                painter = QPainter(picture)
                if self._tick_font:
                    painter.setFont(self._tick_font)
                specs = self.generateDrawSpecs(painter)
                if specs is not None:
                    self.drawPicture(painter, *specs)
            finally:
                painter.end()
            self._picture = picture

        self._picture.play(p)

    def tickSpacing(self, minVal, maxVal, size):
        """Return values describing the desired spacing and offset of ticks.

        This method is called whenever the axis needs to be redrawn and is a
        good method to override in subclasses that require control over tick locations.

        The return value must be a list of tuples, one for each set of ticks::

            [
                (major tick spacing, offset),
                (minor tick spacing, offset),
                (sub-minor tick spacing, offset),
                ...
            ]
        """
        # First check for override tick spacing
        if self._tickSpacing is not None:
            return self._tickSpacing

        dif = abs(maxVal - minVal)
        if dif == 0:
            return []

        # decide optimal minor tick spacing in pixels (this is just aesthetics)
        optimalTickCount = max(2., np.log(size))

        # optimal minor tick spacing
        optimalSpacing = dif / optimalTickCount

        # the largest power-of-10 spacing which is smaller than optimal
        p10unit = 10 ** np.floor(np.log10(optimalSpacing))

        # Determine major/minor tick spacings which flank the optimal spacing.
        intervals = np.array([1., 2., 10., 20., 100.]) * p10unit
        minorIndex = 0
        while intervals[minorIndex+1] <= optimalSpacing:
            minorIndex += 1

        levels = [
            (intervals[minorIndex+2], 0),
            (intervals[minorIndex+1], 0),
        ]

        if self._max_tick_level >= 2:
            # decide whether to include the last level of ticks
            minSpacing = min(size / 20., 30.)
            maxTickCount = size / minSpacing
            if dif / intervals[minorIndex] <= maxTickCount:
                levels.append((intervals[minorIndex], 0))

        return levels

    def tickValues(self, minVal, maxVal, size):
        """
        Return the values and spacing of ticks to draw::

            [
                (spacing, [major ticks]),
                (spacing, [minor ticks]),
                ...
            ]

        By default, this method calls tickSpacing to determine the correct tick locations.
        This is a good method to override in subclasses.
        """
        minVal, maxVal = sorted((minVal, maxVal))

        minVal *= self.scale
        maxVal *= self.scale

        ticks = []
        tickLevels = self.tickSpacing(minVal, maxVal, size)
        allValues = np.array([])
        for i in range(len(tickLevels)):
            spacing, offset = tickLevels[i]

            # determine starting tick
            start = (np.ceil((minVal-offset) / spacing) * spacing) + offset
            # determine number of ticks
            num = int((maxVal-start) / spacing) + 1
            values = (np.arange(num) * spacing + start) / self.scale
            # remove any ticks that were present in higher levels
            # we assume here that if the difference between a tick value and a previously seen tick value
            # is less than spacing/100, then they are 'equal' and we can ignore the new tick.
            values = list(filter(lambda x: all(np.abs(allValues-x) > spacing/self.scale*0.01), values))
            allValues = np.concatenate([allValues, values])
            ticks.append((spacing/self.scale, values))

        if self._log_scale:
            return self.logTickValues(minVal, maxVal, size, ticks)

        return ticks

    def logTickValues(self, minVal, maxVal, size, stdTicks):

        # start with the tick spacing given by tickValues().
        # Any level whose spacing is < 1 needs to be converted to log scale

        ticks = []
        for (spacing, t) in stdTicks:
            if spacing >= 1.0:
                ticks.append((spacing, t))

        if len(ticks) < 3:
            v1 = int(np.floor(minVal))
            v2 = int(np.ceil(maxVal))

            minor = []
            for v in range(v1, v2):
                minor.extend(v + np.log10(np.arange(1, 10)))
            minor = [x for x in minor if x>minVal and x<maxVal]
            ticks.append((None, minor))
        return ticks

    def tickStrings(self, values, scale, spacing):
        """Return the strings that should be placed next to ticks. This method is called
        when redrawing the axis and is a good method to override in subclasses.
        The method is called with a list of tick values, a scaling factor (see below), and the
        spacing between ticks (this is required since, in some instances, there may be only
        one tick and thus no other way to determine the tick spacing)

        The scale argument is used when the axis label is displaying units which may have an SI scaling prefix.
        When determining the text to display, use value*scale to correctly account for this prefix.
        For example, if the axis label's units are set to 'V', then a tick value of 0.001 might
        be accompanied by a scale value of 1000. This indicates that the label is displaying 'mV', and
        thus the tick should display 0.001 * 1000 = 1.
        """
        if self._log_scale:
            return self.logTickStrings(values, scale, spacing)

        places = max(0, np.ceil(-np.log10(spacing*scale)))
        strings = []
        for v in values:
            vs = v * scale
            if abs(vs) < .001 or abs(vs) >= 10000:
                vstr = "%g" % vs
            else:
                vstr = ("%%0.%df" % places) % vs
            strings.append(vstr)
        return strings

    def logTickStrings(self, values, scale, spacing):
        estrings = ["%0.1g"%x for x in 10 ** np.array(values).astype(float) * np.array(scale)]

        convdict = {"0": "⁰",
                    "1": "¹",
                    "2": "²",
                    "3": "³",
                    "4": "⁴",
                    "5": "⁵",
                    "6": "⁶",
                    "7": "⁷",
                    "8": "⁸",
                    "9": "⁹",
                    }
        dstrings = []
        for e in estrings:
            if e.count("e"):
                v, p = e.split("e")
                sign = "⁻" if p[0] == "-" else ""
                pot = "".join([convdict[pp] for pp in p[1:].lstrip("0")])
                if v == "1":
                    v = ""
                else:
                    v = v + "·"
                dstrings.append(v + "10" + sign + pot)
            else:
                dstrings.append(e)
        return dstrings

    def generateDrawSpecs(self, p):
        """
        Calls tickValues() and tickStrings() to determine where and how ticks should
        be drawn, then generates from this a set of drawing commands to be
        interpreted by drawPicture().
        """
        if self._tick_font is not None:
            p.setFont(self._tick_font)
        bounds = self.mapRectFromParent(self.geometry())

        canvas = self._vb
        if canvas is None or not self._show_grid_act.isChecked():
            tickBounds = bounds
        else:
            tickBounds = canvas.mapRectToItem(self, canvas.boundingRect())

        if self._edge == Qt.Edge.LeftEdge:
            span = (bounds.topRight(), bounds.bottomRight())
            tickStart = tickBounds.right()
            tickStop = bounds.right()
            tickDir = -1
            axis = 0
        elif self._edge == Qt.Edge.RightEdge:
            span = (bounds.topLeft(), bounds.bottomLeft())
            tickStart = tickBounds.left()
            tickStop = bounds.left()
            tickDir = 1
            axis = 0
        elif self._edge == Qt.Edge.TopEdge:
            span = (bounds.bottomLeft(), bounds.bottomRight())
            tickStart = tickBounds.bottom()
            tickStop = bounds.bottom()
            tickDir = -1
            axis = 1
        elif self._edge == Qt.Edge.BottomEdge:
            span = (bounds.topLeft(), bounds.topRight())
            tickStart = tickBounds.top()
            tickStop = bounds.top()
            tickDir = 1
            axis = 1

        # determine size of this item in pixels
        points = list(map(self.mapToDevice, span))
        if None in points:
            return
        lengthInPixels = QLineF(points[1], points[0]).length()
        if lengthInPixels == 0:
            return

        # Determine major / minor / subminor axis ticks
        if self._tickLevels is None:
            tickLevels = self.tickValues(self._range[0], self._range[1], lengthInPixels)
            tickStrings = None
        else:
            # parse self.tickLevels into the formats returned by tickLevels() and tickStrings()
            tickLevels = []
            tickStrings = []
            for level in self._tickLevels:
                values = []
                strings = []
                tickLevels.append((None, values))
                tickStrings.append(strings)
                for val, strn in level:
                    values.append(val)
                    strings.append(strn)

        # determine mapping between tick values and local coordinates
        dif = self._range[1] - self._range[0]
        if dif == 0:
            xScale = 1
            offset = 0
        else:
            if axis == 0:
                xScale = -bounds.height() / dif
                offset = self._range[0] * xScale - bounds.height()
            else:
                xScale = bounds.width() / dif
                offset = self._range[0] * xScale

        xRange = [x * xScale - offset for x in self._range]
        xMin = min(xRange)
        xMax = max(xRange)

        tickPositions = [] # remembers positions of previously drawn ticks

        # compute coordinates to draw ticks
        # draw three different intervals, long ticks first
        tickSpecs = []
        for i in range(len(tickLevels)):
            tickPositions.append([])
            ticks = tickLevels[i][1]

            tickLength = self._tick_length / ((i*0.5)+1.0)

            lineAlpha = 255 / (i+1)
            if self._show_grid_act.isChecked():
                lineAlpha *= 160 / 255. * np.clip((0.05 * lengthInPixels / (len(ticks)+1)), 0., 1.)

            for v in ticks:
                # determine actual position to draw this tick
                x = (v * xScale) - offset
                if x < xMin or x > xMax:  ## last check to make sure no out-of-bounds ticks are drawn
                    tickPositions[i].append(None)
                    continue
                tickPositions[i].append(x)

                p1 = [x, x]
                p2 = [x, x]
                p1[axis] = tickStart
                p2[axis] = tickStop
                if not self._show_grid_act.isChecked():
                    p2[axis] += tickLength * tickDir
                tickPen = self._tick_pen
                color = tickPen.color()
                color.setAlpha(int(lineAlpha))
                tickPen.setColor(color)
                tickSpecs.append((tickPen, QPointF(*p1), QPointF(*p2)))

        axisSpec = (self._tick_pen, span[0], span[1])

        textOffset = self._tick_text_offset[axis]  # spacing between axis and text

        textSize2 = 0
        textRects = []
        textSpecs = []  # list of draw

        # If values are hidden, return early
        if not self._show_values:
            return axisSpec, tickSpecs, textSpecs

        for i in range(min(len(tickLevels), self._max_text_level + 1)):
            # Get the list of strings to display for this level
            if tickStrings is None:
                spacing, values = tickLevels[i]
                strings = self.tickStrings(values, self.scale, spacing)
            else:
                strings = tickStrings[i]

            if len(strings) == 0:
                continue

            # ignore strings belonging to ticks that were previously ignored
            for j in range(len(strings)):
                if tickPositions[i][j] is None:
                    strings[j] = None

            # Measure density of text; decide whether to draw this level
            rects = []
            for s in strings:
                if s is None:
                    rects.append(None)
                else:
                    br = p.boundingRect(QRectF(0, 0, 100, 100), Qt.AlignmentFlag.AlignCenter, s)
                    # boundingRect is usually just a bit too large
                    # (but this probably depends on per-font metrics?)
                    br.setHeight(br.height() * 0.8)

                    rects.append(br)
                    textRects.append(rects[-1])

            if len(textRects) > 0:
                # measure all text, make sure there's enough room
                if axis == 0:
                    textSize = np.sum([r.height() for r in textRects])
                    textSize2 = np.max([r.width() for r in textRects])
                else:
                    textSize = np.sum([r.width() for r in textRects])
                    textSize2 = np.max([r.height() for r in textRects])
            else:
                textSize = 0
                textSize2 = 0

            if i > 0:  # always draw top level
                # If the strings are too crowded, stop drawing text now.
                # We use three different crowding limits based on the number
                # of texts drawn so far.
                textFillRatio = float(textSize) / lengthInPixels
                finished = False
                for nTexts, limit in self._text_fill_limits:
                    if len(textSpecs) >= nTexts and textFillRatio >= limit:
                        finished = True
                        break
                if finished:
                    break

            # Determine exactly where tick text should be drawn
            for j in range(len(strings)):
                vstr = strings[j]
                if vstr is None:  # this tick was ignored because it is out of bounds
                    continue
                x = tickPositions[i][j]
                textRect = rects[j]
                height = textRect.height()
                width = textRect.width()
                offset = max(0, self._tick_length) + textOffset

                if self._edge == Qt.Edge.LeftEdge:
                    textFlags = Qt.TextFlag.TextDontClip|Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    rect = QRectF(tickStop-offset-width, x-(height/2), width, height)
                elif self._edge == Qt.Edge.RightEdge:
                    textFlags = Qt.TextFlag.TextDontClip | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    rect = QRectF(tickStop+offset, x-(height/2), width, height)
                elif self._edge == Qt.Edge.TopEdge:
                    textFlags = Qt.TextFlag.TextDontClip | Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom
                    rect = QRectF(x-width/2., tickStop-offset-height, width, height)
                elif self._edge == Qt.Edge.BottomEdge:
                    textFlags = Qt.TextFlag.TextDontClip | Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop
                    rect = QRectF(x-width/2., tickStop+offset, width, height)

                textSpecs.append((rect, textFlags, vstr))

        # update max text size if needed.
        self._updateMaxTextSize(textSize2)

        return axisSpec, tickSpecs, textSpecs

    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        p.setRenderHint(p.RenderHint.Antialiasing, False)
        p.setRenderHint(p.RenderHint.TextAntialiasing, True)

        # draw long line along axis
        pen, p1, p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1, p2)
        p.translate(0.5,0)  # resolves some damn pixel ambiguity

        # draw ticks
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)

        # Draw all text
        if self._tick_font is not None:
            p.setFont(self._tick_font)
        p.setPen(self._tick_label_pen)
        for rect, flags, text in textSpecs:
            p.drawText(rect, int(flags), text)

    def show(self):
        super().show()
        if self._orientation == Qt.Orientation.Vertical:
            self._updateWidth()
        else:
            self._updateHeight()

    def hide(self):
        super().hide()
        if self._orientation == Qt.Orientation.Vertical:
            self._updateWidth()
        else:
            self._updateHeight()

    def close(self) -> None:
        """Override."""
        self.scene().removeItem(self._label)
        self.scene().removeItem(self)

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent) -> None:
        """Override."""
        s = self._vb.wheelMovementToScaleFactor(ev.delta())
        if self._orientation == Qt.Orientation.Vertical:
            self._vb.scaleYBy(s, ev.pos().y())
        else:
            self._vb.scaleXBy(s, ev.pos().x())
        ev.accept()

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        delta = ev.lastPos() - ev.pos()
        if self._orientation == Qt.Orientation.Vertical:
            self._vb.translateYBy(delta.y())
        else:
            self._vb.translateXBy(delta.x())
        ev.accept()

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos())
