"""
This stub file is to aid in the PyCharm auto-completion of the Qt imports.
"""

from typing import Union

try:
    from PyQt6 import QtCore, QtGui, QtTest, QtWidgets

    QtCore = QtCore
    QtGui = QtGui
    QtTest = QtTest
    QtWidgets = QtWidgets
except ImportError:
    try:
        from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

        QtCore = QtCore
        QtGui = QtGui
        QtTest = QtTest
        QtWidgets = QtWidgets


QT_LIB: str
def mkQApp(name: Union[str, None] = None) -> QtWidgets.QApplication: ...
