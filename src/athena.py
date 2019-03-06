#! /usr/bin/env python
import sys
import subprocess
import os
import os.path
import platform

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QStatusBar
from PySide2.QtCore import QFile
import PySide2.QtXml #Temporary pyinstaller workaround

# Set ATHENA_DIR, the base project path, relative to which files and tools will be found
if getattr(sys, 'frozen', False):
    # We're inside a PyInstaller bundle of some kind
    ATHENA_DIR = sys._MEIPASS
else:
    # Not bundled, __file__ is within src/
    ATHENA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class UiLoader(QUiLoader):
    '''
    This works around a shortcoming in QUiLoader: it doesn't provide
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

def runLCBBTool( toolname, p3_input_file, p1_input_dir='input', p2_output_dir='output',
                 p4_scaffold='m13', p5_edge_sections=1, p6_vertex_design=1, p7_edge_number=0,
                 p8_edge_length=38, p9_mesh_spacing=0.0, p10_runmode='s' ):
    tooldir = toolname
    if platform.system() ==  'Windows':
        tool = 'designer-win-{}.exe'.format(toolname)
    elif platform.system() == 'Darwin':
        tool = 'designer-mac-{}'.format(toolname)
    else:
        print("WARNING: unknown platform '{}' for LCBB tool!".format(platform.system()), file=sys.stderr)
        tool = 'designer-{}'.format(toolname)
    wd = os.path.join( ATHENA_DIR, 'tools', tooldir )
    toolpath = os.path.join( wd, tool )
    tool_call = [toolpath, p1_input_dir, p2_output_dir, p3_input_file, p4_scaffold, p5_edge_sections,
                           p6_vertex_design, p7_edge_number, p8_edge_length, p9_mesh_spacing, p10_runmode]
    tool_call_str = [str(x) for x in tool_call]

    print('Calling {} as follows'.format(tool), tool_call_str, "cwd=", wd )
    return subprocess.run(tool_call_str, cwd=wd, )

def runPERDIX(input_file):
    return runLCBBTool( 'PERDIX', p3_input_file=input_file )

def runTALOS(input_file):
    return runLCBBTool( 'TALOS', p3_input_file=input_file, p8_edge_length=42 )

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
        tool_func = [runPERDIX, runTALOS] [ self.toolChooser.currentIndex() ]
        tool_args = self.cmdInput.text()
        result = tool_func( tool_args )
        self.updateStatus("Ran " + self.toolChooser.currentText() + " "
                           + tool_args + ", result: " + str(result.returncode) )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AthenaWindow( os.path.join( ATHENA_DIR, 'ui', 'AthenaMainWindow.ui'))
    sys.exit(app.exec_())
