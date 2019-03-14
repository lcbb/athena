#! /usr/bin/env python
import sys
import subprocess
import os
import os.path
import platform
from pathlib import Path

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QStatusBar, QFileDialog, QWidget, QSizePolicy
from PySide2.QtGui import QKeySequence, QColor
from PySide2.QtCore import QFile, Qt
import PySide2.QtXml #Temporary pyinstaller workaround

import geomview

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

def runLCBBTool( toolname, p2_input_file, p1_output_dir='athena_tmp_output',
                 p3_scaffold='m13', p4_edge_sections=1, p5_vertex_design=1, p6_edge_number=0,
                 p7_edge_length=42, p8_mesh_spacing=0.0, p9_runmode='s' ):
    tooldir = toolname
    if platform.system() ==  'Windows':
        tool = '{}.exe'.format(toolname)
    elif platform.system() == 'Darwin':
        tool = toolname
    else:
        print("WARNING: unknown platform '{}' for LCBB tool!".format(platform.system()), file=sys.stderr)
        tool = toolname
    # lcbb tools require a trailing path separator for directory arguments
    if not p1_output_dir.endswith(os.sep): p1_output_dir += os.sep
    wd = os.path.join( ATHENA_DIR, 'tools', tooldir )
    toolpath = os.path.join( wd, tool )
    tool_call = [toolpath, p1_output_dir, p2_input_file, p3_scaffold, p4_edge_sections,
                           p5_vertex_design, p6_edge_number, p7_edge_length, p8_mesh_spacing, p9_runmode]
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

        self.setupToolDefaults()

        self.geomView = geomview.AthenaGeomView()
        self.geomViewWidget = QWidget.createWindowContainer( self.geomView, self )
        self.verticalLayout.insertWidget( 0, self.geomViewWidget )
        self.geomViewWidget.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        self.show()

        self.perdixRunButton.clicked.connect(self.runPERDIX)
        self.talosRunButton.clicked.connect(self.runTALOS)
        self.perdixOpenButton.clicked.connect(self.addFileToComboBox_action(self.perdixGeometryChooser))
        self.perdixGeometryChooser.currentIndexChanged.connect(self.newMesh)
        self.talosGeometryChooser.currentIndexChanged.connect(self.newMesh)
        self.talosOpenButton.clicked.connect(self.addFileToComboBox_action(self.talosGeometryChooser))
        self.actionQuit.triggered.connect(self.close)

    def setupToolDefaults( self ):
        def pretty_name( input_path ):
            # make words from the file stem, capitalize them, omit a leading number if possible
            # e.g. path/to/06_rhombic_tiling -> 'Rhombic Tiling'
            words = input_path.stem.split('_')
            if len(words) > 1 and words[0].isdigit(): words = words[1:]
            return ' '.join( word.capitalize() for word in words )

        perdix_inputs = Path(ATHENA_DIR, "sample_inputs", "PERDIX")
        for ply in perdix_inputs.glob('*.ply'):
            self.perdixGeometryChooser.addItem( pretty_name(ply), ply.resolve() )

        talos_inputs = Path(ATHENA_DIR, "sample_inputs", "TALOS")
        for ply in talos_inputs.glob("*.ply"):
            self.talosGeometryChooser.addItem( pretty_name(ply), ply.resolve() )


    def addFileToComboBox_action( self, combobox ):
        def selection_slot():
            fileName = QFileDialog.getOpenFileName( self,
                                                   "Open geometry file",
                                                   os.path.join(ATHENA_DIR, 'sample_inputs'),
                                                   "Geometry files (*.ply)")
            filepath = Path(fileName[0])
            if( filepath.is_file() ):
                combobox.addItem( filepath.name, filepath )
                combobox.setCurrentIndex( combobox.count()-1 )
        return selection_slot

    def newMesh( self ):
        # Determine which mesh is displaying
        chooser = [self.perdixGeometryChooser, self.talosGeometryChooser][ self.tabWidget.currentIndex() ]
        selection = chooser.currentData()
        self.geomView.reloadGeom( selection )

    def updateStatus( self, msg ):
        self.statusMsg.setText( msg )

    def runPERDIX( self ):
        self.updateStatus('Running PERDIX...')
        infile_path = self.perdixGeometryChooser.currentData()
        process = runLCBBTool ('PERDIX',
                               p2_input_file=infile_path,
                               p7_edge_length=self.perdixEdgeLengthSpinner.value(),
                               p8_mesh_spacing=self.perdixMeshSpacingSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('PERDIX returned {}.'.format(human_retval))

    def runTALOS( self ):
        self.updateStatus('Running TALOS...')
        infile_path = self.talosGeometryChooser.currentData()
        process = runLCBBTool('TALOS',
                              p2_input_file=infile_path,
                              p4_edge_sections=self.talosEdgeSectionBox.currentIndex()+2,
                              p5_vertex_design=self.talosVertexDesignBox.currentIndex()+1,
                              p7_edge_length=self.talosEdgeLengthSpinner.value())
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
