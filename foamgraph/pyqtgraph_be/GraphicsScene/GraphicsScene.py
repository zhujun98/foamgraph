from enum import Enum
import weakref

from ...backend import QtCore
from ...backend.QtCore import Qt
from ...backend.QtGui import QAction
from ...backend.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QMenu
from .. import ptime
from ..Point import Point


if hasattr(QtCore, 'PYQT_VERSION'):
    try:
        import sip
        HAVE_SIP = True
    except ImportError:
        HAVE_SIP = False
else:
    HAVE_SIP = False


__all__ = ['GraphicsScene', "MouseDragEvent", "MouseClickEvent", "HoverEvent"]


class MouseEventState(Enum):
    OFF = 0
    ON = 1
    ENTER = 2
    EXIT = 3


class MouseDragEvent:
    """
    Instances of this class are delivered to items in a :class:`GraphicsScene <pyqtgraph.GraphicsScene>`
    via their mouseDragEvent() method when the item is being mouse-dragged.

    """

    def __init__(self, moveEvent, pressEvent, lastEvent,
                 state: MouseEventState = MouseEventState.ON):
        self._state = state
        self.accepted = False
        self.currentItem = None
        self._buttonDownScenePos = {}
        self._buttonDownScreenPos = {}
        for btn in [Qt.MouseButton.LeftButton,
                    Qt.MouseButton.MiddleButton,
                    Qt.MouseButton.RightButton]:
            self._buttonDownScenePos[btn] = moveEvent.buttonDownScenePos(btn)
            self._buttonDownScreenPos[btn] = moveEvent.buttonDownScreenPos(btn)
        self._scenePos = moveEvent.scenePos()
        self._screenPos = moveEvent.screenPos()
        if lastEvent is None:
            self._lastScenePos = pressEvent.scenePos()
            self._lastScreenPos = pressEvent.screenPos()
        else:
            self._lastScenePos = lastEvent.scenePos()
            self._lastScreenPos = lastEvent.screenPos()
        self._buttons = moveEvent.buttons()
        self._button = pressEvent.button()
        self._modifiers = moveEvent.modifiers()
        self.acceptedItem = None

    def accept(self):
        """An item should call this method if it can handle the event.

        This will prevent the event being delivered to any other items."""
        self.accepted = True
        self.acceptedItem = self.currentItem

    def ignore(self):
        """An item should call this method if it cannot handle the event.

        This will allow the event to be delivered to other items."""
        self.accepted = False

    def isAccepted(self):
        return self.accepted

    def scenePos(self):
        """Return the current scene position of the mouse."""
        return Point(self._scenePos)

    def screenPos(self):
        """Return the current screen position (pixels relative to widget) of the mouse."""
        return Point(self._screenPos)

    def buttonDownScenePos(self, btn=None):
        """
        Return the scene position of the mouse at the time *btn* was pressed.
        If *btn* is omitted, then the button that initiated the drag is assumed.
        """
        if btn is None:
            btn = self.button()
        return Point(self._buttonDownScenePos[btn])

    def buttonDownScreenPos(self, btn=None):
        """
        Return the screen position (pixels relative to widget) of the mouse at the time *btn* was pressed.
        If *btn* is omitted, then the button that initiated the drag is assumed.
        """
        if btn is None:
            btn = self.button()
        return Point(self._buttonDownScreenPos[btn])

    def lastScenePos(self):
        """
        Return the scene position of the mouse immediately prior to this event.
        """
        return Point(self._lastScenePos)

    def lastScreenPos(self):
        """
        Return the screen position of the mouse immediately prior to this event.
        """
        return Point(self._lastScreenPos)

    def buttons(self):
        """
        Return the buttons currently pressed on the mouse.
        (see QGraphicsSceneMouseEvent::buttons in the Qt documentation)
        """
        return self._buttons

    def button(self):
        """Return the button that initiated the drag (may be different from the buttons currently pressed)
        (see QGraphicsSceneMouseEvent::button in the Qt documentation)

        """
        return self._button

    def pos(self):
        """
        Return the current position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._scenePos))

    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._lastScenePos))

    def buttonDownPos(self, btn=None):
        """
        Return the position of the mouse at the time the drag was initiated
        in the coordinate system of the item that the event was delivered to.
        """
        if btn is None:
            btn = self.button()
        return Point(self.currentItem.mapFromScene(self._buttonDownScenePos[btn]))

    def entering(self):
        """Whether this event is the first one since a drag was initiated."""
        return self._state == MouseEventState.ENTER

    def exiting(self):
        """Whether this event is the last one since a drag was initiated."""
        return self._state == MouseEventState.EXIT

    def __repr__(self):
        if self.currentItem is None:
            lp = self._lastScenePos
            p = self._scenePos
        else:
            lp = self.lastPos()
            p = self.pos()
        return "<MouseDragEvent (%g,%g)->(%g,%g) buttons=%d entering=%s existing=%s>" % (
        lp.x(), lp.y(), p.x(), p.y(), int(self.buttons()), str(self.entering()), str(self.exiting()))

    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)

        """
        return self._modifiers


class MouseClickEvent:
    """
    Instances of this class are delivered to items in a :class:`GraphicsScene <pyqtgraph.GraphicsScene>`
    via their mouseClickEvent() method when the item is clicked.
    """

    def __init__(self, pressEvent, double=False):
        self.accepted = False
        self.currentItem = None
        self._double = double
        self._scenePos = pressEvent.scenePos()
        self._screenPos = pressEvent.screenPos()
        self._button = pressEvent.button()
        self._buttons = pressEvent.buttons()
        self._modifiers = pressEvent.modifiers()
        self._time = ptime.time()
        self.acceptedItem = None

    def accept(self):
        """An item should call this method if it can handle the event.

        This will prevent the event being delivered to any other items."""
        self.accepted = True
        self.acceptedItem = self.currentItem

    def ignore(self):
        """An item should call this method if it cannot handle the event.

        This will allow the event to be delivered to other items."""
        self.accepted = False

    def isAccepted(self):
        return self.accepted

    def scenePos(self):
        """Return the current scene position of the mouse."""
        return Point(self._scenePos)

    def screenPos(self):
        """Return the current screen position (pixels relative to widget) of the mouse."""
        return Point(self._screenPos)

    def buttons(self):
        """
        Return the buttons currently pressed on the mouse.
        (see QGraphicsSceneMouseEvent::buttons in the Qt documentation)
        """
        return self._buttons

    def button(self):
        """Return the mouse button that generated the click event.
        (see QGraphicsSceneMouseEvent::button in the Qt documentation)
        """
        return self._button

    def double(self):
        """Return True if this is a double-click."""
        return self._double

    def pos(self):
        """
        Return the current position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._scenePos))

    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._lastScenePos))

    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)
        """
        return self._modifiers

    def __repr__(self):
        try:
            if self.currentItem is None:
                p = self._scenePos
            else:
                p = self.pos()
            return "<MouseClickEvent (%g,%g) button=%d>" % (p.x(), p.y(), int(self.button()))
        except:
            return "<MouseClickEvent button=%d>" % (int(self.button()))

    def time(self):
        return self._time


class HoverEvent:
    """
    Instances of this class are delivered to items in a :class:`GraphicsScene <pyqtgraph.GraphicsScene>` via their hoverEvent() method when the mouse is hovering over the item.
    This event class both informs items that the mouse cursor is nearby and allows items to
    communicate with one another about whether each item will accept *potential* mouse events.

    It is common for multiple overlapping items to receive hover events and respond by changing
    their appearance. This can be misleading to the user since, in general, only one item will
    respond to mouse events. To avoid this, items make calls to event.acceptClicks(button)
    and/or acceptDrags(button).

    Each item may make multiple calls to acceptClicks/Drags, each time for a different button.
    If the method returns True, then the item is guaranteed to be
    the recipient of the claimed event IF the user presses the specified mouse button before
    moving. If claimEvent returns False, then this item is guaranteed NOT to get the specified
    event (because another has already claimed it) and the item should change its appearance
    accordingly.

    event.isEnter() returns True if the mouse has just entered the item's shape;
    event.isExit() returns True if the mouse has just left.
    """

    def __init__(self, ev: QGraphicsSceneMouseEvent, state: MouseEventState):
        self._state = state
        self.enter = False
        self.exit = False
        self.__clickItems = weakref.WeakValueDictionary()
        self.__dragItems = weakref.WeakValueDictionary()
        self.currentItem = None
        if ev is not None:
            self._scenePos = ev.scenePos()
            self._screenPos = ev.screenPos()
            self._lastScenePos = ev.lastScenePos()
            self._lastScreenPos = ev.lastScreenPos()
            self._buttons = ev.buttons()
            self._modifiers = ev.modifiers()
        else:
            self.exit = True

    def isEnter(self):
        """Returns True if the mouse has just entered the item's shape"""
        return self.enter

    def isExit(self):
        """Returns True if the mouse has just exited the item's shape"""
        return self.exit

    def acceptClicks(self, button: Qt.MouseButton):
        """Inform the scene that the item (that the event was delivered to)
        would accept a mouse click event if the user were to click before
        moving the mouse again.

        Returns True if the request is successful, otherwise returns False (indicating
        that some other item would receive an incoming click).
        """
        if self._state == MouseEventState.EXIT:
            return False

        if button not in self.__clickItems:
            self.__clickItems[button] = self.currentItem
            return True
        return False

    def acceptDrags(self, button: Qt.MouseButton):
        """Inform the scene that the item (that the event was delivered to)
        would accept a mouse drag event if the user were to drag before
        the next hover event.

        Returns True if the request is successful, otherwise returns False (indicating
        that some other item would receive an incoming drag event).
        """
        if self._state == MouseEventState.EXIT:
            return False

        if button not in self.__dragItems:
            self.__dragItems[button] = self.currentItem
            return True
        return False

    def scenePos(self):
        """Return the current scene position of the mouse."""
        return Point(self._scenePos)

    def screenPos(self):
        """Return the current screen position of the mouse."""
        return Point(self._screenPos)

    def lastScenePos(self):
        """Return the previous scene position of the mouse."""
        return Point(self._lastScenePos)

    def lastScreenPos(self):
        """Return the previous screen position of the mouse."""
        return Point(self._lastScreenPos)

    def buttons(self):
        """
        Return the buttons currently pressed on the mouse.
        (see QGraphicsSceneMouseEvent::buttons in the Qt documentation)
        """
        return self._buttons

    def pos(self):
        """
        Return the current position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._scenePos))

    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return Point(self.currentItem.mapFromScene(self._lastScenePos))

    def __repr__(self):
        if self.exit:
            return "<HoverEvent exit=True>"

        if self.currentItem is None:
            lp = self._lastScenePos
            p = self._scenePos
        else:
            lp = self.lastPos()
            p = self.pos()
        return "<HoverEvent (%g,%g)->(%g,%g) buttons=%d enter=%s exit=%s>" % (
        lp.x(), lp.y(), p.x(), p.y(), int(self.buttons()), str(self.isEnter()), str(self.isExit()))

    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)
        """
        return self._modifiers

    def clickItems(self):
        return self.__clickItems

    def dragItems(self):
        return self.__dragItems


class GraphicsScene(QGraphicsScene):
    """Extension of QGraphicsScene that implements a complete, parallel mouse event system.

    (It would have been preferred to just alter the way QGraphicsScene creates and delivers 
    events, but this turned out to be impossible because the constructor for QGraphicsMouseEvent
    is private)
    
    *  Generates MouseClicked events in addition to the usual press/move/release events. 
       (This works around a problem where it is impossible to have one item respond to a 
       drag if another is watching for a click.)
    *  Adjustable radius around click that will catch objects so you don't have to click *exactly* over small/thin objects
    *  Global context menu--if an item implements a context menu, then its parent(s) may also add items to the menu.
    *  Allows items to decide _before_ a mouse click which item will be the recipient of mouse events.
       This lets us indicate unambiguously to the user which item they are about to click/drag on
    *  Eats mouseMove events that occur too soon after a mouse press.
    *  Reimplements items() and itemAt() to circumvent PyQt bug
    
    Mouse interaction is as follows:
    
    1) Every time the mouse moves, the scene delivers both the standard hoverEnter/Move/LeaveEvents 
       as well as custom HoverEvents. 
    2) Items are sent HoverEvents in Z-order and each item may optionally call event.acceptClicks(button), 
       acceptDrags(button) or both. If this method call returns True, this informs the item that _if_ 
       the user clicks/drags the specified mouse button, the item is guaranteed to be the 
       recipient of click/drag events (the item may wish to change its appearance to indicate this).
       If the call to acceptClicks/Drags returns False, then the item is guaranteed to *not* receive
       the requested event (because another item has already accepted it). 
    3) If the mouse is clicked, a mousePressEvent is generated as usual. If any items accept this press event, then
       No click/drag events will be generated and mouse interaction proceeds as defined by Qt. This allows
       items to function properly if they are expecting the usual press/move/release sequence of events.
       (It is recommended that items do NOT accept press events, and instead use click/drag events)
       Note: The default implementation of QGraphicsItem.mousePressEvent will *accept* the event if the 
       item is has its Selectable or Movable flags enabled. You may need to override this behavior.
    4) If no item accepts the mousePressEvent, then the scene will begin delivering mouseDrag and/or mouseClick events.
       If the mouse is moved a sufficient distance (or moved slowly enough) before the button is released, 
       then a mouseDragEvent is generated.
       If no drag events are generated before the button is released, then a mouseClickEvent is generated. 
    5) Click/drag events are delivered to the item that called acceptClicks/acceptDrags on the HoverEvent
       in step 1. If no such items exist, then the scene attempts to deliver the events to items near the event. 
       ClickEvents may be delivered in this way even if no
       item originally claimed it could accept the click. DragEvents may only be delivered this way if it is the initial
       move in a drag.
    """
    # Emitted a list of objects under the cursor when the mouse is
    # moved over the scene.
    mouse_hover_sgn = QtCore.Signal(object)
    # Emitted when the mouse cursor moves over the scene. The position
    # is given in the scene coordinate system.
    mouse_moved_sgn = QtCore.Signal(object)
    # Emitted when the mouse is clicked over the scene. Use ev.pos() to
    # get the click position relative to the item that was clicked on,
    # or ev.scenePos() to get the click position in scene coordinates.
    # See :class:`pyqtgraph.GraphicsScene.MouseClickEvent`.
    mouse_clicked_sgn = QtCore.Signal(object)

    # emitted immediately before the scene is about to be rendered
    prepare_for_paint_sgn = QtCore.Signal()

    def __init__(self, clickRadius=2, moveDistance=5, parent=None):
        super().__init__(parent)
        self.setClickRadius(clickRadius)
        self.setMoveDistance(moveDistance)

        self.clickEvents = []
        self.dragButtons = []
        self.mouseGrabber = None
        self.dragItem = None
        self.lastDrag = None
        self.hoverItems = weakref.WeakKeyDictionary()
        self.lastHoverEvent = None
        self.minDragTime = 0.5  # drags shorter than 0.5 sec are interpreted as clicks
        
        self.contextMenu = []

    def render(self, *args):
        self.prepareForPaint()
        return QGraphicsScene.render(self, *args)

    def prepareForPaint(self):
        """Called before every render.

        This method will inform items that the scene is about to
        be rendered by emitting prepare_for_paint_sgn.
        
        This allows items to delay expensive processing until they know a paint will be required."""
        self.prepare_for_paint_sgn.emit()

    def setClickRadius(self, r):
        """
        Set the distance away from mouse clicks to search for interacting items.
        When clicking, the scene searches first for items that directly intersect the click position
        followed by any other items that are within a rectangle that extends r pixels away from the 
        click position. 
        """
        self._clickRadius = r
        
    def setMoveDistance(self, d):
        """
        Set the distance the mouse must move after a press before mouseMoveEvents will be delivered.
        This ensures that clicks with a small amount of movement are recognized as clicks instead of
        drags.
        """
        self._moveDistance = d

    def mousePressEvent(self, ev: QGraphicsSceneMouseEvent):
        """Override."""
        super().mousePressEvent(ev)

        if self.mouseGrabberItem() is None:  # nobody claimed press; we are free to generate drag/click events
            if self.lastHoverEvent is not None:
                # If the mouse has moved since the last hover event, send a new one.
                # This can happen if a context menu is open while the mouse is moving.
                if ev.scenePos() != self.lastHoverEvent.scenePos():
                    self.sendHoverEvents(ev)
            
            self.clickEvents.append(MouseClickEvent(ev))
            
            # set focus on the topmost focusable item under this click
            items = self.items(ev.scenePos())
            for i in items:
                if i.isEnabled() and i.isVisible() and (i.flags() & i.GraphicsItemFlag.ItemIsFocusable):
                    i.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
                    break
        
    def mouseMoveEvent(self, ev: QGraphicsSceneMouseEvent):
        """Override."""
        self.mouse_moved_sgn.emit(ev.scenePos())

        # First allow QGraphicsScene to deliver hoverEnter/Move/ExitEvents
        super().mouseMoveEvent(ev)
        
        # Next deliver our own HoverEvents
        self.sendHoverEvents(ev)
        
        if ev.buttons():  # button is pressed; send mouseMoveEvents and mouseDragEvents
            # FIXME: duplicated?
            super().mouseMoveEvent(ev)
            if self.mouseGrabberItem() is None:
                now = ptime.time()
                init = False
                # keep track of which buttons are involved in dragging
                for btn in [QtCore.Qt.MouseButton.LeftButton,
                            QtCore.Qt.MouseButton.MiddleButton,
                            QtCore.Qt.MouseButton.RightButton]:
                    if not (ev.buttons() & btn):
                        continue
                    if btn not in self.dragButtons:  # see if we've dragged far enough yet
                        cev = [e for e in self.clickEvents if e.button() == btn]
                        if cev:
                            cev = cev[0]
                            dist = Point(ev.scenePos() - cev.scenePos()).length()
                            if dist == 0 or (dist < self._moveDistance and now - cev.time() < self.minDragTime):
                                continue
                            # If this is the first button to be dragged, then init=True
                            init = init or (len(self.dragButtons) == 0)
                            self.dragButtons.append(btn)

                # If we have dragged buttons, deliver a drag event
                if len(self.dragButtons) > 0:
                    if self.sendDragEvent(
                            ev, MouseEventState.ENTER if init
                            else MouseEventState.ON):
                        ev.accept()

    def mouseReleaseEvent(self, ev: QGraphicsSceneMouseEvent):
        """Override."""
        if self.mouseGrabberItem() is None:
            if ev.button() in self.dragButtons:
                if self.sendDragEvent(ev, MouseEventState.EXIT):
                    ev.accept()
                self.dragButtons.remove(ev.button())
            else:
                cev = [e for e in self.clickEvents if e.button() == ev.button()]
                if cev:
                    if self.sendClickEvent(cev[0]):
                        ev.accept()
                    self.clickEvents.remove(cev[0])

        if not ev.buttons():
            self.dragItem = None
            self.dragButtons = []
            self.clickEvents = []
            self.lastDrag = None

        super().mouseReleaseEvent(ev)
        
        self.sendHoverEvents(ev)  # let items prepare for next click/drag

    def mouseDoubleClickEvent(self, ev: QGraphicsSceneMouseEvent):
        """Override."""
        super().mouseDoubleClickEvent(ev)

        if self.mouseGrabberItem() is None:  # nobody claimed press; we are free to generate drag/click events
            self.clickEvents.append(MouseClickEvent(ev, double=True))
        
    def sendHoverEvents(self, ev: QGraphicsSceneMouseEvent,
                        state: MouseEventState = MouseEventState.ON):
        """Send out HoverEvent.

        :param ev:
        :param state:
        """
        if state == MouseEventState.EXIT:
            items = []
            event = HoverEvent(ev, False)
        else:
            # if we are in mid-drag, do not allow items to accept the hover event.
            event = HoverEvent(ev, not ev.buttons())
            items = self.itemsNearEvent(event, hoverable=True)
            self.mouse_hover_sgn.emit(items)
            
        prev_items = list(self.hoverItems.keys())
            
        for item in items:
            if hasattr(item, 'hoverEvent'):
                event.currentItem = item
                if item not in self.hoverItems:
                    self.hoverItems[item] = None
                    event.enter = True
                else:
                    prev_items.remove(item)
                    event.enter = False
                    
                item.hoverEvent(event)
        
        event.enter = False
        event.exit = True
        for item in prev_items:
            event.currentItem = item

            if item.scene() is self:
                item.hoverEvent(event)
            del self.hoverItems[item]
        
        # Update last hover event unless:
        #   - mouse is dragging (move+buttons); in this case we want the dragged
        #     item to continue receiving events until the drag is over
        #   - event is not a mouse event (QEvent.Leave sometimes appears here)
        if (ev.type() == ev.Type.GraphicsSceneMousePress or
                (ev.type() == ev.Type.GraphicsSceneMouseMove and not ev.buttons())):
            self.lastHoverEvent = event  # save this so we can ask about accepted events later.

    def sendDragEvent(self,
                      ev: QGraphicsSceneMouseEvent,
                      state: MouseEventState):
        """Send out a MouseDragEvent.

        to the current dragItem or to items near the beginning of the drag.

        :param ev:
        :param state:
        """
        event = MouseDragEvent(ev, self.clickEvents[0], self.lastDrag, state=state)
        if state == MouseEventState.ENTER and self.dragItem is None:
            if self.lastHoverEvent is not None:
                acceptedItem = self.lastHoverEvent.dragItems().get(event.button(), None)
            else:
                acceptedItem = None
                
            if acceptedItem is not None and acceptedItem.scene() is self:
                self.dragItem = acceptedItem
                event.currentItem = self.dragItem
                self.dragItem.mouseDragEvent(event)
                    
            else:
                for item in self.itemsNearEvent(event):
                    if not item.isVisible() or not item.isEnabled():
                        continue
                    if hasattr(item, 'mouseDragEvent'):
                        event.currentItem = item
                        item.mouseDragEvent(event)
                        if event.isAccepted():
                            self.dragItem = item
                            if item.flags() & item.GraphicsItemFlag.ItemIsFocusable:
                                item.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
                            break
        elif self.dragItem is not None:
            event.currentItem = self.dragItem
            self.dragItem.mouseDragEvent(event)

        self.lastDrag = event
        
        return event.isAccepted()

    def sendClickEvent(self, ev: QGraphicsSceneMouseEvent):
        # if we are in mid-drag, click events may only go to the dragged item.
        if self.dragItem is not None and hasattr(self.dragItem, 'MouseDragEvent'):
            ev.currentItem = self.dragItem
            self.dragItem.mouseClickEvent(ev)
            
        # otherwise, search near the cursor
        else:
            if self.lastHoverEvent is not None:
                acceptedItem = self.lastHoverEvent.clickItems().get(ev.button(), None)
            else:
                acceptedItem = None
            if acceptedItem is not None:
                ev.currentItem = acceptedItem
                acceptedItem.mouseClickEvent(ev)
            else:
                for item in self.itemsNearEvent(ev):
                    if not item.isVisible() or not item.isEnabled():
                        continue
                    if hasattr(item, 'mouseClickEvent'):
                        ev.currentItem = item
                        item.mouseClickEvent(ev)

                        if ev.isAccepted():
                            if item.flags() & item.GraphicsItemFlag.ItemIsFocusable:
                                item.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
                            break
        self.mouse_clicked_sgn.emit(ev)
        return ev.isAccepted()
        
    def items(self, *args):
        items = QGraphicsScene.items(self, *args)
        return self.translateGraphicsItems(items)
    
    def selectedItems(self, *args):
        items = QGraphicsScene.selectedItems(self, *args)
        return self.translateGraphicsItems(items)

    def itemAt(self, *args):
        item = super().itemAt(*args)
        return self.translateGraphicsItem(item)

    def itemsNearEvent(self,
                       event,
                       selMode=Qt.ItemSelectionMode.IntersectsItemShape,
                       sortOrder=Qt.SortOrder.DescendingOrder,
                       hoverable=False):
        """
        Return an iterator that iterates first through the items that directly intersect point (in Z order)
        followed by any other items that are within the scene's click radius.
        """
        view = self.views()[0]
        tr = view.viewportTransform()
        r = self._clickRadius
        rect = view.mapToScene(QtCore.QRect(0, 0, 2*r, 2*r)).boundingRect()
        
        if hasattr(event, 'buttonDownScenePos'):
            point = event.buttonDownScenePos()
        else:
            point = event.scenePos()

        items = self.items(point, selMode, sortOrder, tr)
        
        # remove items whose shape does not contain point (scene.items() apparently sucks at this)
        items2 = []
        for item in items:
            if hoverable and not hasattr(item, 'hoverEvent'):
                continue
            if item.scene() is not self:
                continue
            shape = item.shape() # Note: default shape() returns boundingRect()
            if shape is None:
                continue
            if shape.contains(item.mapFromScene(point)):
                items2.append(item)
        
        # Sort by descending Z-order (don't trust scene.itms() to do this either)
        # use 'absolute' z value, which is the sum of all item/parent ZValues
        def absZValue(item):
            if item is None:
                return 0
            return item.zValue() + absZValue(item.parentItem())
        
        items2.sort(key=absZValue, reverse=True)
        
        return items2
        
    def getViewWidget(self):
        return self.views()[0]

    def addParentContextMenus(self, item, menu, event):
        """
        Can be called by any item in the scene to expand its context menu to include parent context menus.
        Parents may implement getContextMenus to add new menus / actions to the existing menu.
        getContextMenus must accept 1 argument (the event that generated the original menu) and
        return a single QMenu or a list of QMenus.
        
        The final menu will look like:
        
            |    Original Item 1
            |    Original Item 2
            |    ...
            |    Original Item N
            |    ------------------
            |    Parent Item 1
            |    Parent Item 2
            |    ...
            |    Grandparent Item 1
            |    ...
            
        
        ==============  ==================================================
        **Arguments:**
        item            The item that initially created the context menu 
                        (This is probably the item making the call to this function)
        menu            The context menu being shown by the item
        event           The original event that triggered the menu to appear.
        ==============  ==================================================
        """
        menusToAdd = []
        while item is not self:
            item = item.parentItem()
            if item is None:
                item = self
            if not hasattr(item, "getContextMenus"):
                continue
            subMenus = item.getContextMenus(event) or []
            if isinstance(subMenus, list): # so that some items (like FlowchartViewBox) can return multiple menus
                menusToAdd.extend(subMenus)
            else:
                menusToAdd.append(subMenus)

        if menusToAdd:
            menu.addSeparator()

        for m in menusToAdd:
            if isinstance(m, QMenu):
                menu.addMenu(m)
            elif isinstance(m, QAction):
                menu.addAction(m)
            else:
                raise Exception("Cannot add object %s (type=%s) to QMenu." % (str(m), str(type(m))))
            
        return menu

    def getContextMenus(self, event):
        self.contextMenuItem = event.acceptedItem
        return self.contextMenu

    @staticmethod
    def translateGraphicsItem(item):
        # This function is intended as a workaround for a problem with older
        # versions of PyQt (< 4.9?), where methods returning 'QGraphicsItem *'
        # lose the type of the QGraphicsObject subclasses and instead return
        # generic QGraphicsItem wrappers.
        if HAVE_SIP and isinstance(item, sip.wrapper):
            obj = item.toGraphicsObject()
            if obj is not None:
                item = obj
        return item

    @staticmethod
    def translateGraphicsItems(items):
        return list(map(GraphicsScene.translateGraphicsItem, items))
