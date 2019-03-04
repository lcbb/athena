#! /usr/bin/env python
import sys
import subprocess
import os
import os.path

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QStatusBar
from PySide2.QtCore import QFile
import PySide2.QtXml #Temporary pyinstaller workaround

if getattr(sys, 'frozen', False):
    ATHENA_DIR = sys._MEIPASS
else:
    ATHENA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class UiLoader(QUiLoader):
    '''
    This works around a dumbness in QUiLoader: it doesn't provide
    a means to apply a ui into a given, existing object (except
    by the Qt Designer "promoted widgets" method, which in turn
    does not work for QMainWindow)

    This extended QUiLoader uses a given object instance
    as the default object for any un-parented widget in the loaded UI,
    allowing us to populate a pre-constructed widget from a ui file.
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

    @staticmethod
    def populateUI( parent, filepath ):
        ui_file = QFile( filepath )
        ui_file.open( QFile.ReadOnly )
        try:
            ui_loader = UiLoader( parent )
            ui_loader.load( ui_file )
        finally:
            ui_file.close()

def runPERDIX(input_filepath, args):
    wd = os.path.join( ATHENA_DIR, "tools", "PERDIX-Win-MCR" )
    tool = os.path.join( wd, "PERDIX.exe" )
    perdix_call = [tool, input_filepath] + args.split()
    print("Calling PERDIX as follows:", perdix_call, "cwd=", wd)
    return subprocess.run(perdix_call, cwd=wd, ) #stdout=subprocess.DEVNULL, 
                                                 #stderr=subprocess.DEVNULL)


class AthenaWindow(QMainWindow):
    def __init__( self, ui_filepath ):
        super( AthenaWindow, self).__init__(None)
        UiLoader.populateUI( self, ui_filepath )

        self.statusMsg = QLabel("Ready.")
        self.statusBar().addWidget(self.statusMsg)

        self.show()

        self.runButton.clicked.connect(self.runCmd)

    def updateStatus( self, msg ):
        self.statusMsg.setText( msg )

    def runCmd( self ):
        command = self.cmdInput.text()
        cmd_args = command.split()
        result = runPERDIX(command[0], " ".join(command[1:]))
        self.updateStatus("Ran " + command + ", result: " + str(result.returncode) )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AthenaWindow( os.path.join( ATHENA_DIR, 'ui', 'AthenaMainWindow.ui'))
    sys.exit(app.exec_())
