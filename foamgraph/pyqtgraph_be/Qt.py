# -*- coding: utf-8 -*-
"""
This module exists to smooth out some of the differences between PySide and PyQt4:

* Automatically import either PyQt4 or PySide depending on availability
* Allow to import QtCore/QtGui pyqtgraph.Qt without specifying which Qt wrapper
  you want to use.
* Declare QtCore.Signal, .Slot in PyQt4
* Declare loadUiType function for Pyside

"""

import sys, subprocess, warnings

from ..backend import QT_LIB, QtCore, QtGui, QtWidgets

PYQT5 = 'PyQt5'
PYQT6 = 'PyQt6'


class FailedImport(object):
    """Used to defer ImportErrors until we are sure the module is needed.
    """
    def __init__(self, err):
        self.err = err
        
    def __getattr__(self, attr):
        raise self.err


def _isQObjectAlive(obj):
    """An approximation of PyQt's isQObjectAlive().
    """
    try:
        if hasattr(obj, 'parent'):
            obj.parent()
        elif hasattr(obj, 'parentItem'):
            obj.parentItem()
        else:
            raise Exception("Cannot determine whether Qt object %s is still alive." % obj)
    except RuntimeError:
        return False
    else:
        return True


# Make a loadUiType function like PyQt has

# Credit:
# http://stackoverflow.com/questions/4442286/python-code-genration-with-pyside-uic/14195313#14195313

class _StringIO(object):
    """Alternative to built-in StringIO needed to circumvent unicode/ascii issues"""
    def __init__(self):
        self.data = []
    
    def write(self, data):
        self.data.append(data)
        
    def getvalue(self):
        return ''.join(map(str, self.data)).encode('utf8')

    
def _loadUiType(uiFile):
    """
    PySide lacks a "loadUiType" command like PyQt4's, so we have to convert
    the ui file to py code in-memory first and then execute it in a
    special frame to retrieve the form_class.

    from stackoverflow: http://stackoverflow.com/a/14195313/3781327

    seems like this might also be a legitimate solution, but I'm not sure
    how to make PyQt4 and pyside look the same...
        http://stackoverflow.com/a/8717832
    """

    try:
        import pyside2uic as pysideuic
    except ImportError:
        # later vserions of pyside2 have dropped pysideuic; use the uic binary instead.
        pysideuic = None

    # get class names from ui file
    import xml.etree.ElementTree as xml
    parsed = xml.parse(uiFile)
    widget_class = parsed.find('widget').get('class')
    form_class = parsed.find('class').text

    # convert ui file to python code
    if pysideuic is None:
        pyside2version = tuple(map(int, PySide2.__version__.split(".")))
        if pyside2version >= (5, 14) and pyside2version < (5, 14, 2, 2):
            warnings.warn('For UI compilation, it is recommended to upgrade to PySide >= 5.15')
        uipy = subprocess.check_output(['pyside2-uic', uiFile])
    else:
        o = _StringIO()
        with open(uiFile, 'r') as f:
            pysideuic.compileUi(f, o, indent=0)
        uipy = o.getvalue()

    # exceute python code
    pyc = compile(uipy, '<string>', 'exec')
    frame = {}
    exec(pyc, frame)

    # fetch the base_class and form class based on their type in the xml from designer
    form_class = frame['Ui_%s'%form_class]
    base_class = eval('QtGui.%s'%widget_class)

    return form_class, base_class


if QT_LIB == PYQT5:
    # We're using PyQt5 which has a different structure so we're going to use a shim to
    # recreate the Qt4 structure for Qt5
    from PyQt5 import sip, uic
    
    # PyQt5, starting in v5.5, calls qAbort when an exception is raised inside
    # a slot. To maintain backward compatibility (and sanity for interactive
    # users), we install a global exception hook to override this behavior.
    ver = QtCore.PYQT_VERSION_STR.split('.')
    if int(ver[1]) >= 5:
        if sys.excepthook == sys.__excepthook__:
            sys_excepthook = sys.excepthook
            def pyqt5_qabort_override(*args, **kwds):
                return sys_excepthook(*args, **kwds)
            sys.excepthook = pyqt5_qabort_override
    
    try:
        from PyQt5 import QtSvg
    except ImportError as err:
        QtSvg = FailedImport(err)

    VERSION_INFO = 'PyQt5 ' + QtCore.PYQT_VERSION_STR + ' Qt ' + QtCore.QT_VERSION_STR

elif QT_LIB == PYQT6:

    from PyQt6 import sip, uic

    try:
        from PyQt6 import QtSvg
    except ImportError as err:
        QtSvg = FailedImport(err)

    VERSION_INFO = 'PyQt5 ' + QtCore.PYQT_VERSION_STR + ' Qt ' + QtCore.QT_VERSION_STR


if QT_LIB in [PYQT5, PYQT6]:
    # We're using Qt5 which has a different structure so we're going to use a shim to
    # recreate the Qt4 structure
    
    __QGraphicsItem_scale = QtWidgets.QGraphicsItem.scale

    def scale(self, *args):
        if args:
            sx, sy = args
            tr = self.transform()
            tr.scale(sx, sy)
            self.setTransform(tr)
        else:
            return __QGraphicsItem_scale(self)

    QtWidgets.QGraphicsItem.scale = scale

    def rotate(self, angle):
        tr = self.transform()
        tr.rotate(angle)
        self.setTransform(tr)
    QtWidgets.QGraphicsItem.rotate = rotate

    def translate(self, dx, dy):
        tr = self.transform()
        tr.translate(dx, dy)
        self.setTransform(tr)
    QtWidgets.QGraphicsItem.translate = translate

    def setMargin(self, i):
        self.setContentsMargins(i, i, i, i)
    QtWidgets.QGridLayout.setMargin = setMargin

    def setResizeMode(self, *args):
        self.setSectionResizeMode(*args)
    QtWidgets.QHeaderView.setResizeMode = setResizeMode

    
    QtGui.QApplication = QtWidgets.QApplication
    QtGui.QGraphicsScene = QtWidgets.QGraphicsScene
    QtGui.QGraphicsObject = QtWidgets.QGraphicsObject
    QtGui.QGraphicsWidget = QtWidgets.QGraphicsWidget

    QtGui.QApplication.setGraphicsSystem = None
    
    # Import all QtWidgets objects into QtGui
    for o in dir(QtWidgets):
        if o.startswith('Q'):
            setattr(QtGui, o, getattr(QtWidgets,o) )


if QT_LIB in [PYQT5, PYQT6]:
    QtVersion = QtCore.QT_VERSION_STR

    def isQObjectAlive(obj):
        return not sip.isdeleted(obj)
    
    loadUiType = uic.loadUiType

    QtCore.Signal = QtCore.pyqtSignal
