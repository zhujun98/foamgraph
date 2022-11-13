try:
    from PyQt6 import QtCore, QtGui, QtWidgets

    QtCore = QtCore
    QtGui = QtGui
    QtWidgets = QtWidgets
except ModuleNotFoundError:
    ...

try:
    from PyQt5 import QtCore, QtGui, QtWidgets

    QtCore = QtCore
    QtGui = QtGui
    QtWidgets = QtWidgets
except ModuleNotFoundError:
    ...
