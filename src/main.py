#! /usr/bin/env python

import sys
from PySide2.QtCore import Qt, QObject, QEvent
from PySide2.QtGui import QSurfaceFormat, QPaintEvent, QMouseEvent, QWindow, QCursor
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

class DebugApp(QApplication):

    def notify( self, x, y ):
        if( x.__class__ == QWindow and y.__class__ == QMouseEvent ):
            x.event(y)
            return True
        if( y.__class__ == QMouseEvent ):
            print('App:', x, y)
            print(y.isAccepted(), int(y.buttons()), int(y.source()))
        return super().notify(x,y)

class MacMouseReleaseFilter(QObject):
    '''
    Ugly workaround for an elusive bug in Mac OSX, wherein mouse release
    events generated from touchpad taps are not properly dispatched.
    This occurs only on fairly recent mac laptops with a force touch
    trackpad and "Tap To Click" enabled.

    Since the lost mouse release events do get delivered to the containing QWindow
    object, this filter is installed on that object and manually dispatches
    the events down to the widget under the mouse cursor.

    This was bug #10 in the Athena github repository.  I am uncertain how
    robust this fix will prove to be, but here's hoping it sticks.
    '''

    def eventFilter(self, receiver, event):
        if( event.type() == QEvent.MouseButtonRelease ):
            curs = QCursor.pos()
            widget = QApplication.widgetAt(curs)
            local = widget.mapFromGlobal(curs)
            newEvent = QMouseEvent( event.type(), local, event.button(), event.buttons(), event.modifiers())
            ret = widget.event(newEvent)
            return ret and newEvent.isAccepted()
        return False


#app = DebugApp(sys.argv)
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_SynthesizeMouseForUnhandledTouchEvents, False)
app.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, False)
app.aboutToQuit.connect( athena_cleanup )
window = AthenaWindow( )
if sys.platform == "darwin":
    mousefilter = MacMouseReleaseFilter()
    app.topLevelWindows()[0].installEventFilter( mousefilter )
sys.exit(app.exec_())
