#! /usr/bin/env python

import sys
from PySide2.QtCore import Qt
from PySide2.QtGui import QSurfaceFormat
from PySide2.QtWidgets import QApplication
from athena import athena_cleanup
from athena.mainwindow import AthenaWindow

# Workaround function borrowed from https://github.com/biolab/orange3/blob/master/Orange/canvas/__main__.py
def fix_macos_nswindow_tabbing():
    """
    Disable automatic NSWindow tabbing on macOS Sierra and higher.
    See QTBUG-61707
    """
    import platform
    if sys.platform != "darwin":
        return

    ver, _, _ = platform.mac_ver()
    ver = tuple(map(int, ver.split(".")[:2]))
    if ver < (10, 12):
        return

    import ctypes
    import ctypes.util

    c_char_p, c_void_p = ctypes.c_char_p, ctypes.c_void_p
    id = Sel = Class = c_void_p

    def annotate(func, restype, argtypes):
        func.restype = restype
        func.argtypes = argtypes
        return func
    try:
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("libobjc"))
        # Load AppKit.framework which contains NSWindow class
        # pylint: disable=unused-variable
        AppKit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("AppKit"))
        objc_getClass = annotate(
            libobjc.objc_getClass, Class, [c_char_p])
        objc_msgSend = annotate(
            libobjc.objc_msgSend, id, [id, Sel])
        sel_registerName = annotate(
            libobjc.sel_registerName, Sel, [c_char_p])
        class_getClassMethod = annotate(
            libobjc.class_getClassMethod, c_void_p, [Class, Sel])
    except (OSError, AttributeError):
        return

    NSWindow = objc_getClass(b"NSWindow")
    if NSWindow is None:
        return
    setAllowsAutomaticWindowTabbing = sel_registerName(
        b'setAllowsAutomaticWindowTabbing:'
    )
    # class_respondsToSelector does not work (for class methods)
    if class_getClassMethod(NSWindow, setAllowsAutomaticWindowTabbing):
        # [NSWindow setAllowsAutomaticWindowTabbing: NO]
        objc_msgSend(
            NSWindow,
            setAllowsAutomaticWindowTabbing,
            ctypes.c_bool(False),
        )

fix_macos_nswindow_tabbing()
f = QSurfaceFormat()
f.setDepthBufferSize(24)
f.setSamples(4)
QSurfaceFormat.setDefaultFormat(f)
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_SynthesizeMouseForUnhandledTouchEvents, False)
app.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, False)
app.aboutToQuit.connect( athena_cleanup )
window = AthenaWindow( )
sys.exit(app.exec_())
