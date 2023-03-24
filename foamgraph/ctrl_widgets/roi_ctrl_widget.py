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
from foamgraph.graphics_item.roi import ROIBase, RectROI, EllipseROI


class RoiCtrlWidget(AbstractCtrlWidget):
    """RoiCtrlWidget class.

    Widget which controls a single ROI.
    """
    # (activated, x, y, w, h) where idx starts from 1
    roi_geometry_change_sgn = pyqtSignal(str, object)

    _pos_validator = QIntValidator(-10000, 10000)
    _size_validator = QIntValidator(1, 10000)

    def __init__(self, roi: ROIBase, id_: str, **kwargs):
        super().__init__(**kwargs)

        self._roi = roi
        self._id = id_

        self._activate_cb = QCheckBox(self._id)
        palette = self._activate_cb.palette()
        palette.setColor(palette.ColorRole.WindowText, roi.pen().color())
        self._activate_cb.setPalette(palette)

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

    def initUI(self):
        """Override."""
        layout = QHBoxLayout()

        layout.addWidget(self._activate_cb)
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

    @pyqtSlot(int)
    def onToggleRoiActivation(self, state):
        if state == qt_enum_to_int(Qt.CheckState.Checked):
            self._roi.show()
            self.setEditable(True)
        else:
            self._roi.hide()
            self.setEditable(False)

        self.roi_geometry_change_sgn.emit(
            self._id, (state == Qt.CheckState.Checked, *self._roi.rect()))

    @pyqtSlot(object)
    def onRoiPositionEdited(self, value):
        x, y, w, h = self._roi.rect()
        if self.sender() == self._px_le:
            x = int(value)
        elif self.sender() == self._py_le:
            y = int(value)

        # If 'update' == False, the state change will be remembered
        # but not processed and no signals will be emitted.
        self._roi.setPos(x, y)
        # trigger region_changed_sgn which moves the handler(s)
        # finish=False -> region_change_finished_sgn will not emit, which
        # otherwise triggers infinite recursion
        self._roi.stateChanged(finish=False)

        state = self._activate_cb.isChecked()
        self.roi_geometry_change_sgn.emit(self._id, (state, x, y, w, h))

    @pyqtSlot(object)
    def onRoiSizeEdited(self, value):
        x, y, w, h = self._roi.rect()
        if self.sender() == self._width_le:
            w = int(float(value))
        elif self.sender() == self._height_le:
            h = int(float(value))

        # If 'update' == False, the state change will be remembered
        # but not processed and no signals will be emitted.
        self._roi.setRect(x, y, w, h)
        # trigger region_changed_sgn which moves the handler(s)
        # finish=False -> region_change_finished_sgn will not emit, which
        # otherwise triggers infinite recursion
        self._roi.stateChanged(finish=False)

        self.roi_geometry_change_sgn.emit(
            self._id, (self._activate_cb.isChecked(), x, y, w, h))

    def onRoiGeometryChangeFinished(self):
        """Connect to the signal from an ROI object."""
        x, y, w, h = self._roi.rect()
        self._updateEditParameters(x, y, w, h)
        # inform other widgets
        self.roi_geometry_change_sgn.emit(
            self._id, (self._activate_cb.isChecked(), x, y, w, h))

    def notifyRoiParams(self):
        self._roi.region_change_finished_sgn.emit()

    def _updateEditParameters(self, x, y, w, h):
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


class RoiCtrlWidgetGroup(AbstractGroupBoxCtrlWidget):
    """Widget for controlling a group of ROIs."""

    roi_geometry_change_sgn = pyqtSignal(str, object)

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

    def addROI(self, id_: str, roi: ROIBase):
        widget = RoiCtrlWidget(roi, id_, with_frame=False, parent=self)
        self._widgets.append(widget)
        self.layout().addWidget(widget)
        self.setFixedHeight(self.minimumSizeHint().height())
        widget.notifyRoiParams()
