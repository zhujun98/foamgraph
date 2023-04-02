"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from ..backend.QtCore import pyqtSignal, Qt
from ..backend.QtWidgets import (
    QLayout, QSizePolicy, QToolButton, QVBoxLayout, QWidget
)


class Section(QWidget):

    collapse_toggled_sgn = pyqtSignal(bool)

    def __init__(self, *, parent=None):
        super().__init__(parent=parent)
        btn = QToolButton()
        btn.setStyleSheet("QToolButton { border: none; }")
        btn.setArrowType(Qt.ArrowType.RightArrow)
        btn.setSizePolicy(QSizePolicy.Policy.Minimum,
                          QSizePolicy.Policy.Minimum)
        btn.setCheckable(True)
        self._toggle_btn = btn

        self._cw = QWidget()
        self._cw.setContentsMargins(0, 0, 0, 0)

        self._toggle_btn.setChecked(False)
        self._cw.setVisible(False)

        self.init()

    def init(self):
        self._initUI()
        self._initConnections()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self._toggle_btn)
        layout.addWidget(self._cw)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(QSizePolicy.Policy.Minimum,
                           QSizePolicy.Policy.Minimum)

    def _initConnections(self):
        self._toggle_btn.clicked.connect(
            self._onToggleButtonTriggered)

    def setLayout(self, layout: QLayout):
        self._cw.setLayout(layout)

    def _onToggleButtonTriggered(self):
        checked = self._toggle_btn.isChecked()
        arrow_type = Qt.ArrowType.DownArrow \
            if checked else Qt.ArrowType.RightArrow
        self._cw.setVisible(checked)
        self._toggle_btn.setArrowType(arrow_type)
        self.collapse_toggled_sgn.emit(not checked)
