"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
import abc

from ..backend.QtCore import Qt
from ..backend.QtWidgets import (
    QAbstractSpinBox, QCheckBox, QFrame, QGroupBox, QLineEdit, QWidget
)

from .smart_widgets import SmartBoundaryLineEdit, SmartSliceLineEdit
from ..utilities import parse_slice_inv


class _CtrlWidgetMeta(type(QWidget), abc.ABCMeta):
    ...


class _CtrlWidgetMixin(metaclass=_CtrlWidgetMeta):
    @abc.abstractmethod
    def initUI(self):
        """Initialization of UI."""
        ...

    @abc.abstractmethod
    def initConnections(self):
        """Initialization of signal-slot connections."""
        ...

    def updateMetaData(self):
        """Update metadata belong to this control widget.

        :returns bool: True if all metadata successfully parsed
            and emitted, otherwise False.
        """
        return True

    def loadMetaData(self):
        """Load metadata from Redis and set this control widget."""
        ...

    def onStart(self):
        ...

    def onStop(self):
        ...

    def _updateWidgetValue(self, widget, config, key, *, cast=None):
        """Update widget value from meta data."""
        value = self._getMetaData(config, key)
        if value is None:
            return

        if cast is not None:
            value = cast(value)

        if isinstance(widget, QCheckBox):
            widget.setChecked(value == 'True')
        elif isinstance(widget, SmartBoundaryLineEdit):
            widget.setText(value[1:-1])
        elif isinstance(widget, SmartSliceLineEdit):
            widget.setText(parse_slice_inv(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QAbstractSpinBox):
            widget.setValue(value)
        else:
            raise TypeError(f"Unknown widget type: {type(widget)}")


class AbstractCtrlWidget(QFrame, _CtrlWidgetMixin):
    def __init__(self, *, with_frame: bool = True, parent=None):
        """Initialization."""
        super().__init__(parent=parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        # widgets whose values are not allowed to change after the "run"
        # button is clicked
        self._non_reconfigurable_widgets = []

        if with_frame:
            self.setFrameStyle(QFrame.StyledPanel)
        else:
            self.setFrameStyle(QFrame.Shape.NoFrame)

    def onStart(self):
        """Override."""
        for widget in self._non_reconfigurable_widgets:
            widget.setEnabled(False)

    def onStop(self):
        """Override."""
        for widget in self._non_reconfigurable_widgets:
            widget.setEnabled(True)


class AbstractGroupBoxCtrlWidget(QGroupBox, _CtrlWidgetMixin):
    GROUP_BOX_STYLE_SHEET = 'QGroupBox:title {'\
                            'color: #8B008B;' \
                            'border: 1px;' \
                            'subcontrol-origin: margin;' \
                            'subcontrol-position: top left;' \
                            'padding-left: 10px;' \
                            'padding-top: 10px;' \
                            'margin-top: 0.0em;}'

    def __init__(self, title, *, parent=None):
        """Initialization."""
        super().__init__(title, parent=parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet(self.GROUP_BOX_STYLE_SHEET)

        # widgets whose values are not allowed to change after the "run"
        # button is clicked
        self._non_reconfigurable_widgets = []

    def onStart(self):
        """Override."""
        for widget in self._non_reconfigurable_widgets:
            widget.setEnabled(False)

    def onStop(self):
        """Override."""
        for widget in self._non_reconfigurable_widgets:
            widget.setEnabled(True)
