import numpy as np

from ..backend.QtCore import pyqtSignal, QLineF, QPointF, QRectF, Qt
from ..backend.QtGui import QAction, QPen, QPicture, QPainter
from ..backend.QtWidgets import (
    QCheckBox, QGraphicsSceneMouseEvent, QGraphicsSceneResizeEvent,
    QGraphicsSceneWheelEvent, QGridLayout, QMenu, QGraphicsTextItem,
    QWidget, QWidgetAction
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

        self._range = (0, 1)

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

        self._text_width = 30  # Keeps track of maximum width / height of tick text
        self._text_height = 18

        self.showLabel(False)

        self._tick_pen = None
        self.setTickPen(FColor.mkPen('foreground'))

        self._tick_label_pen = None
        self.setTickLabelPen(FColor.mkPen('foreground'))

        self._canvas = None

        self._menu = self.initMenu()
        self._invert_axis_act = self.getMenuAction("InvertAxis")
        self._show_grid_act = self.getMenuAction("ShowGrid")
        self._log_scale_act = self.getMenuAction("LogScale")

    def initMenu(self):
        menu = QMenu()

        action = menu.addAction("Log Scale")
        action.setObjectName("LogScale")
        action.setCheckable(True)
        action.toggled.connect(self.onLogScaleToggled)

        action = menu.addAction("Show Grid")
        action.setObjectName("ShowGrid")
        action.setCheckable(True)
        action.toggled.connect(self.onShowGridToggled)

        action = menu.addAction("Invert Axis")
        action.setObjectName("InvertAxis")
        action.setCheckable(True)

        return menu

    def getMenuAction(self, name: str) -> QAction:
        return self._menu.findChild(QAction, name)

    def logScale(self) -> bool:
        return self._log_scale_act.isChecked()

    def onShowGridToggled(self):
        self._picture = None
        self.prepareGeometryChange()
        self.update()

    def onLogScaleToggled(self, state: bool):
        self.log_Scale_toggled_sgn.emit(state)
        self._picture = None
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
            mx = max(self._text_width, x)
            if mx > self._text_width or mx < self._text_width - 10:
                self._text_width = mx
                self._updateWidth()
        else:
            mx = max(self._text_height, x)
            if mx > self._text_height or mx < self._text_height - 10:
                self._text_height = mx
                self._updateHeight()

    def _adjustSize(self):
        if self._orientation == Qt.Orientation.Vertical:
            self._updateWidth()
        else:
            self._updateHeight()

    def _updateHeight(self):
        if not self.isVisible():
            h = 0
        else:
            h = self._text_height

            h += self._tick_text_offset[1]
            h += max(0, self._tick_length)
            if self._label.isVisible():
                h += self._label.boundingRect().height() * 0.8

        self.setMaximumHeight(h)
        self.setMinimumHeight(h)
        self._picture = None

    def _updateWidth(self):
        if not self.isVisible():
            w = 0
        else:
            w = self._text_width
            w += self._tick_text_offset[0]
            w += max(0, self._tick_length)
            if self._label.isVisible():
                w += self._label.boundingRect().height() * 0.8  # bounding rect is usually an overestimate

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
        self._range = (vmin, vmax)
        self._picture = None
        self.update()

    def linkToCanvas(self, canvas: "Canvas"):
        """Link the axis to a Canvas."""
        if self._canvas is not None:
            raise RuntimeError(
                "The axis has already been linked to a Canvas.")

        self._canvas = canvas
        if self._orientation == Qt.Orientation.Vertical:
            self._invert_axis_act.triggered.connect(canvas.invertY)
            canvas.y_range_changed_sgn.connect(self.onCanvasChanged)

        else:
            self._invert_axis_act.triggered.connect(canvas.invertX)
            canvas.x_range_changed_sgn.connect(self.onCanvasChanged)

    def onCanvasChanged(self) -> None:
        rect = self._canvas.viewRect()
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
        canvas = self._canvas
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

        ticks = []
        tickLevels = self.tickSpacing(minVal, maxVal, size)
        allValues = np.array([])
        for i in range(len(tickLevels)):
            spacing, offset = tickLevels[i]

            # determine starting tick
            start = (np.ceil((minVal-offset) / spacing) * spacing) + offset
            # determine number of ticks
            num = int((maxVal-start) / spacing) + 1
            values = (np.arange(num) * spacing + start)
            # remove any ticks that were present in higher levels
            # we assume here that if the difference between a tick value and a previously seen tick value
            # is less than spacing/100, then they are 'equal' and we can ignore the new tick.
            values = list(filter(lambda x: all(np.abs(allValues-x) > spacing * 0.01), values))
            allValues = np.concatenate([allValues, values])
            ticks.append((spacing, values))

        if self._log_scale_act.isChecked():
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

    def tickStrings(self, values, spacing):
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
        if self._log_scale_act.isChecked():
            return self.logTickStrings(values, spacing)

        places = max(0, np.ceil(-np.log10(spacing)))
        strings = []
        for v in values:
            vs = v
            if abs(vs) < .001 or abs(vs) >= 10000:
                vstr = "%g" % vs
            else:
                vstr = ("%%0.%df" % places) % vs
            strings.append(vstr)
        return strings

    def logTickStrings(self, values, spacing):
        estrings = ["%0.1g"%x for x in 10 ** np.array(values).astype(float)]

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
        bounds = self.mapRectFromParent(self.geometry())

        canvas = self._canvas
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
        tickLevels = self.tickValues(self._range[0], self._range[1], lengthInPixels)
        tickStrings = None

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

        for i in range(min(len(tickLevels), self._max_text_level + 1)):
            # Get the list of strings to display for this level
            if tickStrings is None:
                spacing, values = tickLevels[i]
                strings = self.tickStrings(values, spacing)
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

    def _onMouseDClickEvent(self):
        if self._orientation == Qt.Orientation.Vertical:
            self._canvas.enableAutoYRange(True)
        else:
            self._canvas.enableAutoXRange(True)

    def mouseDoubleClickEvent(self, ev: QGraphicsSceneMouseEvent):
        """Override."""
        if ev.button() == Qt.MouseButton.LeftButton:
            ev.accept()
            self._onMouseDClickEvent()

    def close(self) -> None:
        """Override."""
        self.scene().removeItem(self._label)
        self.scene().removeItem(self)

    def wheelEvent(self, ev: QGraphicsSceneWheelEvent) -> None:
        """Override."""
        s = self._canvas.wheelMovementToScaleFactor(ev.delta())
        if self._orientation == Qt.Orientation.Vertical:
            self._canvas.scaleYBy(s, ev.pos().y())
        else:
            self._canvas.scaleXBy(s, ev.pos().x())
        ev.accept()

    def mouseDragEvent(self, ev: MouseDragEvent) -> None:
        delta = ev.lastPos() - ev.pos()
        if self._orientation == Qt.Orientation.Vertical:
            self._canvas.translateYBy(delta.y())
        else:
            self._canvas.translateXBy(delta.x())
        ev.accept()

    def mouseClickEvent(self, ev: MouseClickEvent):
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self._menu.popup(ev.screenPos())
