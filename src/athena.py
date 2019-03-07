#! /usr/bin/env python
import sys
import subprocess
import os
import os.path
import platform

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QStatusBar, QFileDialog
from PySide2.QtGui import QKeySequence
from PySide2.QtCore import QFile
import PySide2.QtXml #Temporary pyinstaller workaround

print("My CWD is", os.getcwd())

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

def runLCBBTool( toolname, p3_input_file, p1_input_dir='.', p2_output_dir='output',
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
    # lcbb tools require a trailing path separator for directory arguments
    if not p1_input_dir.endswith(os.sep): p1_input_dir += os.sep
    if not p2_output_dir.endswith(os.sep): p2_output_dir += os.sep
    wd = os.path.join( ATHENA_DIR, 'tools', tooldir )
    toolpath = os.path.join( wd, tool )
    tool_call = [toolpath, p1_input_dir, p2_output_dir, p3_input_file, p4_scaffold, p5_edge_sections,
                           p6_vertex_design, p7_edge_number, p8_edge_length, p9_mesh_spacing, p10_runmode]
    tool_call_str = [str(x) for x in tool_call]

    print('Calling {} as follows'.format(tool), tool_call_str)
    return subprocess.run(tool_call_str, stdout=subprocess.DEVNULL, stderr=None)


class AthenaWindow(QMainWindow):
    def __init__( self, ui_filepath ):
        super( AthenaWindow, self).__init__(None)
        UiLoader.populateUI( self, ui_filepath )

        self.statusMsg = QLabel("Ready.")
        self.statusBar().addWidget(self.statusMsg)

        # Menu shortcuts cannot be set up in a cross-platform way within Qt Designer,
        # so do that here.
        self.actionOpen.setShortcut( QKeySequence.StandardKey.Open )
        self.actionQuit.setShortcut( QKeySequence.StandardKey.Quit )

        self.show()

        self.perdixRunButton.clicked.connect(self.runPERDIX)
        self.talosRunButton.clicked.connect(self.runTALOS)
        self.actionOpen.triggered.connect(self.selectGeometryFile)
        self.actionQuit.triggered.connect(self.close)

    def selectGeometryFile( self ):
        fileName = QFileDialog.getOpenFileName( self, 
                                               "Open geometry file", 
                                               os.path.join(ATHENA_DIR, 'sample_inputs'),
                                               "Geometry files (*.ply)")
        self.filenameInput.setText(fileName[0])

    def updateStatus( self, msg ):
        self.statusMsg.setText( msg )

    def runPERDIX( self ):
        self.updateStatus('Running PERDIX...')
        infile = self.filenameInput.text()
        infile_dir = os.path.abspath( os.path.dirname(infile) )
        infile_name = os.path.basename(infile)
        process = runLCBBTool ('PERDIX',
                               p1_input_dir=infile_dir,
                               p3_input_file=infile_name,
                               p8_edge_length=self.perdixEdgeLengthSpinner.value(),
                               p9_mesh_spacing=self.perdixMeshSpacingSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('PERDIX returned {}.'.format(human_retval))

    def runTALOS( self ):
        self.updateStatus('Running TALOS...')
        infile = self.filenameInput.text()
        infile_dir = os.path.abspath( os.path.dirname(infile) )
        infile_name = os.path.basename(infile)
        process = runLCBBTool('TALOS',
                              p1_input_dir=infile_dir,
                              p3_input_file=infile_name,
                              p5_edge_sections=self.talosEdgeSectionBox.currentIndex()+1,
                              p6_vertex_design=self.talosVertexDesignBox.currentIndex()+1,
                              p8_edge_length=self.talosEdgeLengthSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('TALOS returned {}.'.format(human_retval))

    def runCmd( self ):
        tool_func = [runPERDIX, runTALOS] [ self.toolChooser.currentIndex() ]
        tool_args = self.filenameInput.text()
        result = tool_func( tool_args )
        self.updateStatus("Ran " + self.toolChooser.currentText() + " "
                           + tool_args + ", result: " + str(result.returncode) )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AthenaWindow( os.path.join( ATHENA_DIR, 'ui', 'AthenaMainWindow.ui'))
    sys.exit(app.exec_())
