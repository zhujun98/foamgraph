import sys

QT_LIB = None

try:
    from PyQt6 import QtCore, QtGui, QtWidgets, QtTest
    QT_LIB = "PyQt6"
except ModuleNotFoundError:
    ...

if QT_LIB is None:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets, QtTest
        QT_LIB = "PyQt5"
    except ModuleNotFoundError:
        ...

if QT_LIB is None:
    raise ImportError(
        "Failed to import any of the supported Qt libraries: ['PyQt6', 'PyQt5']")


sys.modules["foamgraph.backend.QtCore"] = QtCore
sys.modules["foamgraph.backend.QtGui"] = QtGui
sys.modules["foamgraph.backend.QtWidgets"] = QtWidgets
sys.modules["foamgraph.backend.QtTest"] = QtTest


def qt_enum_to_int(value):
    if QT_LIB == "PyQt5":
        return value
    return value.value
