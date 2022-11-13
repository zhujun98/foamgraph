"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend import qt_enum_to_int
from ..backend.QtCore import Qt, pyqtSignal, pyqtSlot
from ..backend.QtGui import QIntValidator
from ..backend.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QVBoxLayout
)

from .base_ctrl_widgets import AbstractCtrlWidget, AbstractGroupBoxCtrlWidget
from .smart_widgets import SmartLineEdit
from ..aesthetics import FColor
from ..roi import RectROI


class RoiCtrlWidget(AbstractCtrlWidget):
    """RoiCtrlWidget class.

    Widget which controls a single ROI.
    """
    # TODO: locked currently is always 0
    # (idx, activated, locked, x, y, w, h) where idx starts from 1
    roi_geometry_change_sgn = pyqtSignal(object)

    _pos_validator = QIntValidator(-10000, 10000)
    _size_validator = QIntValidator(1, 10000)

    def __init__(self, roi: RectROI, *, enable_lock: bool = True, **kwargs):
        super().__init__(**kwargs)

        self._roi = roi
        roi.setLocked(False)

        self._activate_cb = QCheckBox(f"ROI{self._roi.index}")
        palette = self._activate_cb.palette()
        palette.setColor(palette.ColorRole.WindowText, FColor.mkColor(roi.color))
        self._activate_cb.setPalette(palette)

        self._enable_lock = enable_lock
        self._lock_cb = QCheckBox("Lock")

        self._width_le = SmartLineEdit()
        self._width_le.setValidator(self._size_validator)
        self._height_le = SmartLineEdit()
        self._height_le.setValidator(self._size_validator)
        self._px_le = SmartLineEdit()
        self._px_le.setValidator(self._pos_validator)
        self._py_le = SmartLineEdit()
        self._py_le.setValidator(self._pos_validator)

        self._line_edits = (self._width_le, self._height_le,
                            self._px_le, self._py_le)

        self.initUI()
        self.initConnections()

        self.disableAllEdit()

    def initUI(self):
        """Override."""
        layout = QHBoxLayout()

        layout.addWidget(self._activate_cb)
        if self._enable_lock:
            layout.addWidget(self._lock_cb)
        layout.addWidget(QLabel("w: "))
        layout.addWidget(self._width_le)
        layout.addWidget(QLabel("h: "))
        layout.addWidget(self._height_le)
        layout.addWidget(QLabel("x: "))
        layout.addWidget(self._px_le)
        layout.addWidget(QLabel("y: "))
        layout.addWidget(self._py_le)

        self.setLayout(layout)

    def initConnections(self):
        """Override."""
        self.roi_geometry_change_sgn.connect(
            self.parent().roi_geometry_change_sgn)

        self._width_le.value_changed_sgn.connect(self.onRoiSizeEdited)
        self._height_le.value_changed_sgn.connect(self.onRoiSizeEdited)
        self._px_le.value_changed_sgn.connect(self.onRoiPositionEdited)
        self._py_le.value_changed_sgn.connect(self.onRoiPositionEdited)

        self._roi.region_change_finished_sgn.connect(
            self.onRoiGeometryChangeFinished)

        self._activate_cb.stateChanged.connect(self.onToggleRoiActivation)
        self._activate_cb.stateChanged.emit(
            qt_enum_to_int(self._activate_cb.checkState()))

        self._lock_cb.stateChanged.connect(self.onLock)

    def setLabel(self, text):
        self._activate_cb.setText(text)

    @pyqtSlot(int)
    def onToggleRoiActivation(self, state):
        if state == qt_enum_to_int(Qt.CheckState.Checked):
            self._roi.show()
            self.enableAllEdit()
        else:
            self._roi.hide()
            self.disableAllEdit()

        x, y = [int(v) for v in self._roi.pos()]
        w, h = [int(v) for v in self._roi.size()]
        self.roi_geometry_change_sgn.emit(
            (self._roi.index, state == Qt.CheckState.Checked, 0, x, y, w, h))

    @pyqtSlot(object)
    def onRoiPositionEdited(self, value):
        x, y = [int(v) for v in self._roi.pos()]
        w, h = [int(v) for v in self._roi.size()]

        if self.sender() == self._px_le:
            x = int(value)
        elif self.sender() == self._py_le:
            y = int(value)

        # If 'update' == False, the state change will be remembered
        # but not processed and no signals will be emitted.
        self._roi.setPos((x, y), update=False)
        # trigger region_changed_sgn which moves the handler(s)
        # finish=False -> region_change_finished_sgn will not emit, which
        # otherwise triggers infinite recursion
        self._roi.stateChanged(finish=False)

        state = self._activate_cb.isChecked()
        self.roi_geometry_change_sgn.emit(
            (self._roi.index, state, 0, x, y, w, h))

    @pyqtSlot(object)
    def onRoiSizeEdited(self, value):
        x, y = [int(v) for v in self._roi.pos()]
        w, h = [int(v) for v in self._roi.size()]
        if self.sender() == self._width_le:
            w = int(value)
        elif self.sender() == self._height_le:
            h = int(value)

        # If 'update' == False, the state change will be remembered
        # but not processed and no signals will be emitted.
        self._roi.setSize((w, h), update=False)
        # trigger region_changed_sgn which moves the handler(s)
        # finish=False -> region_change_finished_sgn will not emit, which
        # otherwise triggers infinite recursion
        self._roi.stateChanged(finish=False)

        self.roi_geometry_change_sgn.emit(
            (self._roi.index, self._activate_cb.isChecked(), 0, x, y, w, h))

    @pyqtSlot(object)
    def onRoiGeometryChangeFinished(self, roi):
        """Connect to the signal from an ROI object."""
        x, y = [int(v) for v in roi.pos()]
        w, h = [int(v) for v in roi.size()]
        self._updateParameters(x, y, w, h)
        # inform other widgets
        self.roi_geometry_change_sgn.emit(
            (roi.index, self._activate_cb.isChecked(), 0, x, y, w, h))

    def notifyRoiParams(self):
        # fill the QLineEdit(s) and Redis
        self._roi.region_change_finished_sgn.emit(self._roi)

    def _updateParameters(self, x, y, w, h):
        self.roi_geometry_change_sgn.disconnect()
        self._px_le.setText(str(x))
        self._py_le.setText(str(y))
        self._width_le.setText(str(w))
        self._height_le.setText(str(h))
        self.roi_geometry_change_sgn.connect(
           self.parent().roi_geometry_change_sgn)

    def reloadRoiParams(self, cfg):
        state, _, x, y, w, h = [v.strip() for v in cfg.split(',')]

        self.roi_geometry_change_sgn.disconnect()
        self._px_le.setText(x)
        self._py_le.setText(y)
        self._width_le.setText(w)
        self._height_le.setText(h)
        self.roi_geometry_change_sgn.connect(
            self.parent().roi_geometry_change_sgn)
        self._activate_cb.setChecked(bool(int(state)))

    def setEditable(self, editable):
        for w in self._line_edits:
            w.setDisabled(not editable)

    @pyqtSlot(int)
    def onLock(self, state):
        locked = state == qt_enum_to_int(Qt.CheckState.Checked)
        self._roi.setLocked(locked)
        self.setEditable(not locked)

    def disableAllEdit(self):
        self.setEditable(False)
        self._lock_cb.setDisabled(True)

    def enableAllEdit(self):
        self._lock_cb.setDisabled(False)
        self.setEditable(True)


class RoiCtrlWidgetGroup(AbstractGroupBoxCtrlWidget):
    """Widget for controlling a group of ROIs."""

    # forward the signal from RoiCtrlWidget
    roi_geometry_change_sgn = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__("ROI control", *args, **kwargs)
        self._widgets = []

        self.initUI()
        self.initConnections()

    def initUI(self):
        """Override."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def initConnections(self):
        """Override."""
        ...

    def updateMetaData(self):
        """Override."""
        for widget in self._widgets:
            widget.notifyRoiParams()
        return True

    def loadMetaData(self):
        """Override."""
        ...

    def addRoi(self, roi: RectROI):
        widget = RoiCtrlWidget(roi, with_frame=False, parent=self)
        self._widgets.append(widget)
        self.layout().addWidget(widget)
        self.setFixedHeight(self.minimumSizeHint().height())
        widget.notifyRoiParams()
