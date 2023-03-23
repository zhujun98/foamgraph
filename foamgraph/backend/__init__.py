import importlib


# We borrow the pyqtgraph way of managing Qt modules from different bindings
QT_LIB = None


def _copy_attrs(src, dst):
    for o in dir(src):
        if not hasattr(dst, o):
            setattr(dst, o, getattr(src, o))


supported_bindings = ["PyQt6", "PyQt5"]
for binding in supported_bindings:
    try:
        importlib.import_module(f"{binding}.QtCore")
        QT_LIB = binding
        break
    except ModuleNotFoundError:
        ...


if QT_LIB is None:
    raise ImportError(
        f"Failed to import any of the supported Qt libraries: "
        f"{supported_bindings}")


from . import QtCore, QtGui, QtTest, QtWidgets


if QT_LIB == "PyQt6":
    import PyQt6.QtCore
    import PyQt6.QtGui
    import PyQt6.QtTest
    import PyQt6.QtWidgets

    _copy_attrs(PyQt6.QtCore, QtCore)
    _copy_attrs(PyQt6.QtGui, QtGui)
    _copy_attrs(PyQt6.QtWidgets, QtWidgets)
    _copy_attrs(PyQt6.QtTest, QtTest)

    from PyQt6 import sip

elif QT_LIB == "PyQt5":
    import PyQt5.QtCore
    import PyQt5.QtGui
    import PyQt5.QtTest
    import PyQt5.QtWidgets

    _copy_attrs(PyQt5.QtCore, QtCore)
    _copy_attrs(PyQt5.QtGui, QtGui)
    _copy_attrs(PyQt5.QtWidgets, QtWidgets)
    _copy_attrs(PyQt5.QtTest, QtTest)

    from PyQt5 import sip

    # Shim Qt5 namespace to match Qt6
    module_whitelist = [
        "QAction",
        "QActionGroup",
        "QFileSystemModel",
        "QShortcut",
        "QUndoCommand",
        "QUndoGroup",
        "QUndoStack",
    ]
    for module in module_whitelist:
        attr = getattr(QtWidgets, module)
        setattr(QtGui, module, attr)


def qt_enum_to_int(value):
    if QT_LIB == "PyQt5":
        return value
    return value.value


def mkQApp(name=None):
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    if name is not None:
        app.setApplicationName(name)
    return app
