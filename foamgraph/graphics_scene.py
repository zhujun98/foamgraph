from enum import Enum
import time
import weakref

from .backend.QtCore import pyqtSignal, QLineF, QRect, Qt
from .backend.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent


class MouseEventState(Enum):
    OFF = 0
    ON = 1
    ENTER = 2
    EXIT = 3


class MouseDragEvent:
    """Mouse event delivered by :class:`GraphicsScene` when a item is dragged.
    """
    def __init__(self, move_ev, press_ev, last_ev,
                 state: MouseEventState = MouseEventState.ON):
        self._state = state
        self.accepted = False
        self.current_item = None
        self._button_down_scene_pos = {}
        self._button_down_screen_pos = {}
        for btn in [Qt.MouseButton.LeftButton,
                    Qt.MouseButton.MiddleButton,
                    Qt.MouseButton.RightButton]:
            self._button_down_scene_pos[btn] = move_ev.buttonDownScenePos(btn)
            self._button_down_screen_pos[btn] = move_ev.buttonDownScreenPos(btn)
        self._scene_pos = move_ev.scenePos()
        self._screen_pos = move_ev.screenPos()
        if last_ev is None:
            self._last_scene_pos = press_ev.scenePos()
            self._last_screen_pos = press_ev.screenPos()
        else:
            self._last_scene_pos = last_ev.scenePos()
            self._last_screen_pos = last_ev.screenPos()
        self._buttons = move_ev.buttons()
        self._button = press_ev.button()
        self._modifiers = move_ev.modifiers()
        self.accepted_item = None

    def accept(self):
        """An item should call this method if it can handle the event.

        This will prevent the event being delivered to any other items."""
        self.accepted = True
        self.accepted_item = self.current_item

    def ignore(self):
        """An item should call this method if it cannot handle the event.

        This will allow the event to be delivered to other items."""
        self.accepted = False

    def isAccepted(self):
        return self.accepted

    def scenePos(self):
        """Return the current scene position of the mouse."""
        return self._scene_pos

    def screenPos(self):
        """Return the current screen position (pixels relative to widget) of the mouse."""
        return self._screen_pos

    def buttonDownScenePos(self, btn=None):
        """
        Return the scene position of the mouse at the time *btn* was pressed.
        If *btn* is omitted, then the button that initiated the drag is assumed.
        """
        if btn is None:
            btn = self.button()
        return self._button_down_scene_pos[btn]

    def buttonDownScreenPos(self, btn=None):
        """
        Return the screen position (pixels relative to widget) of the mouse at the time *btn* was pressed.
        If *btn* is omitted, then the button that initiated the drag is assumed.
        """
        if btn is None:
            btn = self.button()
        return self._button_down_screen_pos[btn]

    def lastScenePos(self):
        """
        Return the scene position of the mouse immediately prior to this event.
        """
        return self._last_scene_pos

    def lastScreenPos(self):
        """
        Return the screen position of the mouse immediately prior to this event.
        """
        return self._last_screen_pos

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
        return self.current_item.mapFromScene(self._scene_pos)

    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return self.current_item.mapFromScene(self._last_scene_pos)

    def buttonDownPos(self, btn=None):
        """
        Return the position of the mouse at the time the drag was initiated
        in the coordinate system of the item that the event was delivered to.
        """
        if btn is None:
            btn = self.button()
        return self.current_item.mapFromScene(self._button_down_scene_pos[btn])

    def entering(self):
        """Whether this event is the first one since a drag was initiated."""
        return self._state == MouseEventState.ENTER

    def exiting(self):
        """Whether this event is the last one since a drag was initiated."""
        return self._state == MouseEventState.EXIT

    def __repr__(self):
        if self.current_item is None:
            lp = self._last_scene_pos
            p = self._scene_pos
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
        self.current_item = None
        self._double = double
        self._scene_pos = pressEvent.scenePos()
        self._screen_pos = pressEvent.screenPos()
        self._button = pressEvent.button()
        self._buttons = pressEvent.buttons()
        self._modifiers = pressEvent.modifiers()
        self._time = time.time()
        self.accepted_item = None

    def accept(self):
        """An item should call this method if it can handle the event.

        This will prevent the event being delivered to any other items."""
        self.accepted = True
        self.accepted_item = self.current_item

    def ignore(self):
        """An item should call this method if it cannot handle the event.

        This will allow the event to be delivered to other items."""
        self.accepted = False

    def isAccepted(self):
        return self.accepted

    def scenePos(self):
        """Return the current scene position of the mouse."""
        return self._scene_pos

    def screenPos(self):
        """Return the current screen position (pixels relative to widget) of the mouse."""
        return self._screen_pos

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
        return self.current_item.mapFromScene(self._scene_pos)

    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return self.current_item.mapFromScene(self._last_scene_pos)

    def modifiers(self):
        """Return any keyboard modifiers currently pressed.
        (see QGraphicsSceneMouseEvent::modifiers in the Qt documentation)
        """
        return self._modifiers

    def __repr__(self):
        try:
            if self.current_item is None:
                p = self._scene_pos
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
        self.__click_items = weakref.WeakValueDictionary()
        self.__drag_items = weakref.WeakValueDictionary()
        self.current_item = None
        if ev is not None:
            self._scene_pos = ev.scenePos()
            self._screen_pos = ev.screenPos()
            self._last_scene_pos = ev.lastScenePos()
            self._last_screen_pos = ev.lastScreenPos()
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

        if button not in self.__click_items:
            self.__click_items[button] = self.current_item
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

        if button not in self.__drag_items:
            self.__drag_items[button] = self.current_item
            return True
        return False

    def scenePos(self):
        """Return the current scene position of the mouse."""
        return self._scene_pos

    def screenPos(self):
        """Return the current screen position of the mouse."""
        return self._screen_pos

    def lastScenePos(self):
        """Return the previous scene position of the mouse."""
        return self._last_scene_pos

    def lastScreenPos(self):
        """Return the previous screen position of the mouse."""
        return self._last_screen_pos

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
        return self.current_item.mapFromScene(self._scene_pos)

    def lastPos(self):
        """
        Return the previous position of the mouse in the coordinate system of the item
        that the event was delivered to.
        """
        return self.current_item.mapFromScene(self._last_scene_pos)

    def __repr__(self):
        if self.exit:
            return "<HoverEvent exit=True>"

        if self.current_item is None:
            lp = self._last_scene_pos
            p = self._scene_pos
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
        return self.__click_items

    def dragItems(self):
        return self.__drag_items


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
    mouse_hover_sgn = pyqtSignal(object)
    # Emitted when the mouse cursor moves over the scene. The position
    # is given in the scene coordinate system.
    mouse_moved_sgn = pyqtSignal(object)
    # Emitted when the mouse is clicked over the scene. Use ev.pos() to
    # get the click position relative to the item that was clicked on,
    # or ev.scenePos() to get the click position in scene coordinates.
    mouse_clicked_sgn = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._click_radius = 2
        self._move_distance = 5

        self.click_events = []
        self.drag_buttons = []
        self.drag_item = None
        self.last_drag = None
        self.hover_items = weakref.WeakKeyDictionary()
        self.last_hover_event = None
        self.min_drag_time = 0.5  # drags shorter than 0.5 sec are interpreted as clicks

    def mousePressEvent(self, ev: QGraphicsSceneMouseEvent) -> None:
        """Override."""
        super().mousePressEvent(ev)

        if self.mouseGrabberItem() is None:  # nobody claimed press; we are free to generate drag/click events
            if self.last_hover_event is not None:
                # If the mouse has moved since the last hover event, send a new one.
                # This can happen if a context menu is open while the mouse is moving.
                if ev.scenePos() != self.last_hover_event.scenePos():
                    self.sendHoverEvents(ev)
            
            self.click_events.append(MouseClickEvent(ev))
            
            # set focus on the topmost focusable item under this click
            items = self.items(ev.scenePos())
            for i in items:
                if i.isEnabled() and i.isVisible() and (i.flags() & i.GraphicsItemFlag.ItemIsFocusable):
                    i.setFocus(Qt.FocusReason.MouseFocusReason)
                    break
        
    def mouseMoveEvent(self, ev: QGraphicsSceneMouseEvent) -> None:
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
                now = time.time()
                init = False
                # keep track of which buttons are involved in dragging
                for btn in [Qt.MouseButton.LeftButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.RightButton]:
                    if not (ev.buttons() & btn):
                        continue
                    if btn not in self.drag_buttons:  # see if we've dragged far enough yet
                        cev = [e for e in self.click_events if e.button() == btn]
                        if cev:
                            cev = cev[0]
                            dist = QLineF(ev.scenePos(), cev.scenePos()).length()
                            if dist == 0 or (dist < self._move_distance and now - cev.time() < self.min_drag_time):
                                continue
                            # If this is the first button to be dragged, then init=True
                            init = init or (len(self.drag_buttons) == 0)
                            self.drag_buttons.append(btn)

                # If we have dragged buttons, deliver a drag event
                if len(self.drag_buttons) > 0:
                    if self.sendDragEvent(
                            ev, MouseEventState.ENTER if init
                            else MouseEventState.ON):
                        ev.accept()

    def mouseReleaseEvent(self, ev: QGraphicsSceneMouseEvent) -> None:
        """Override."""
        if self.mouseGrabberItem() is None:
            if ev.button() in self.drag_buttons:
                if self.sendDragEvent(ev, MouseEventState.EXIT):
                    ev.accept()
                self.drag_buttons.remove(ev.button())
            else:
                cev = [e for e in self.click_events if e.button() == ev.button()]
                if cev:
                    if self.sendClickEvent(cev[0]):
                        ev.accept()
                    self.click_events.remove(cev[0])

        if not ev.buttons():
            self.drag_item = None
            self.drag_buttons = []
            self.click_events = []
            self.last_drag = None

        super().mouseReleaseEvent(ev)
        
        self.sendHoverEvents(ev)  # let items prepare for next click/drag

    def mouseDoubleClickEvent(self, ev: QGraphicsSceneMouseEvent):
        """Override."""
        super().mouseDoubleClickEvent(ev)

        if self.mouseGrabberItem() is None:  # nobody claimed press; we are free to generate drag/click events
            self.click_events.append(MouseClickEvent(ev, double=True))
        
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
            
        prev_items = list(self.hover_items.keys())
            
        for item in items:
            if hasattr(item, 'hoverEvent'):
                event.current_item = item
                if item not in self.hover_items:
                    self.hover_items[item] = None
                    event.enter = True
                else:
                    prev_items.remove(item)
                    event.enter = False
                    
                item.hoverEvent(event)
        
        event.enter = False
        event.exit = True
        for item in prev_items:
            event.current_item = item

            if item.scene() is self:
                item.hoverEvent(event)
            del self.hover_items[item]
        
        # Update last hover event unless:
        #   - mouse is dragging (move+buttons); in this case we want the dragged
        #     item to continue receiving events until the drag is over
        #   - event is not a mouse event (QEvent.Leave sometimes appears here)
        if (ev.type() == ev.Type.GraphicsSceneMousePress or
                (ev.type() == ev.Type.GraphicsSceneMouseMove and not ev.buttons())):
            self.last_hover_event = event  # save this so we can ask about accepted events later.

    def sendDragEvent(self,
                      ev: QGraphicsSceneMouseEvent,
                      state: MouseEventState):
        """Send out a MouseDragEvent.

        to the current drag_item or to items near the beginning of the drag.

        :param ev:
        :param state:
        """
        event = MouseDragEvent(ev, self.click_events[0], self.last_drag, state=state)
        if state == MouseEventState.ENTER and self.drag_item is None:
            if self.last_hover_event is not None:
                accepted_item = self.last_hover_event.dragItems().get(event.button(), None)
            else:
                accepted_item = None
                
            if accepted_item is not None and accepted_item.scene() is self:
                self.drag_item = accepted_item
                event.current_item = self.drag_item
                self.drag_item.mouseDragEvent(event)
                    
            else:
                for item in self.itemsNearEvent(event):
                    if not item.isVisible() or not item.isEnabled():
                        continue
                    if hasattr(item, 'mouseDragEvent'):
                        event.current_item = item
                        item.mouseDragEvent(event)
                        if event.isAccepted():
                            self.drag_item = item
                            if item.flags() & item.GraphicsItemFlag.ItemIsFocusable:
                                item.setFocus(Qt.FocusReason.MouseFocusReason)
                            break
        elif self.drag_item is not None:
            event.current_item = self.drag_item
            self.drag_item.mouseDragEvent(event)

        self.last_drag = event
        
        return event.isAccepted()

    def sendClickEvent(self, ev: QGraphicsSceneMouseEvent):
        # if we are in mid-drag, click events may only go to the dragged item.
        if self.drag_item is not None and hasattr(self.drag_item, 'MouseDragEvent'):
            ev.current_item = self.drag_item
            self.drag_item.mouseClickEvent(ev)
            
        # otherwise, search near the cursor
        else:
            if self.last_hover_event is not None:
                accepted_item = self.last_hover_event.clickItems().get(ev.button(), None)
            else:
                accepted_item = None
            if accepted_item is not None:
                ev.current_item = accepted_item
                accepted_item.mouseClickEvent(ev)
            else:
                for item in self.itemsNearEvent(ev):
                    if not item.isVisible() or not item.isEnabled():
                        continue
                    if hasattr(item, 'mouseClickEvent'):
                        ev.current_item = item
                        item.mouseClickEvent(ev)

                        if ev.isAccepted():
                            if item.flags() & item.GraphicsItemFlag.ItemIsFocusable:
                                item.setFocus(Qt.FocusReason.MouseFocusReason)
                            break
        self.mouse_clicked_sgn.emit(ev)
        return ev.isAccepted()
        
    def items(self, *args):
        return QGraphicsScene.items(self, *args)

    def selectedItems(self, *args):
        return QGraphicsScene.selectedItems(self, *args)

    def itemAt(self, *args):
        return super().itemAt(*args)

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
        r = self._click_radius
        rect = view.mapToScene(QRect(0, 0, 2*r, 2*r)).boundingRect()
        
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
