#! /usr/bin/env python
import sys

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QStatusBar
from PySide2.QtCore import QFile

class UiLoader(QUiLoader):
    '''
    This works around a dumbness in QUiLoader: it doesn't provide
    a means to apply a ui into a given, existing object (except
    by the Qt Designer "promoted widgets" method, which does
    not work for QMainWindow)

    This is simply a QUiLoader that uses a given object instance
    as the default object for any un-parented widget in the loaded UI.
    '''
    def __init__(self, baseInstance, *args, **kwargs):
        super(UiLoader, self).__init__(*args, **kwargs)
        self.baseInstance = baseInstance

    def createWidget( self, className, parent=None, name=''):
        if parent is None:
            # Don't create a new one, return the existing one.
            return self.baseInstance
        else:
            return super(UiLoader,self).createWidget(className, parent, name)

class AthenaWindow(QMainWindow):
    def __init__( self, ui_file_path ):
        super( AthenaWindow, self).__init__(None)
        ui_file = QFile( ui_file_path )
        ui_file.open( QFile.ReadOnly)

        ui_loader = UiLoader(self)
        ui_loader.load(ui_file)
        ui_file.close()

        self.statusMsg = QLabel("Ready.")
        self.statusBar().addWidget(self.statusMsg)

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AthenaWindow('ui/AthenaMainWindow.ui')
    sys.exit(app.exec_())
