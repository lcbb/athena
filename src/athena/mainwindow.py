import sys
import subprocess
import os
import os.path
import platform
from pathlib import Path

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, QStatusBar, QFileDialog, QWidget, QSizePolicy, QColorDialog, QStackedWidget, QTreeWidget, QTreeWidgetItem, QHeaderView
from PySide2.QtGui import QKeySequence, QPixmap, QIcon, QColor
from PySide2.QtCore import QFile, Qt, Signal
import PySide2.QtXml #Temporary pyinstaller workaround

from athena import viewer, ATHENA_DIR, ATHENA_OUTPUT_DIR

class AutoResizingStackedWidget( QStackedWidget ):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def setCurrentIndex( self, idx ):
        max_width = max( self.widget(x).sizeHint().width() for x in range(self.count()))
        for page_idx in range(self.count()):
            h_policy = self.widget(page_idx).sizePolicy().horizontalPolicy()
            v_policy = QSizePolicy.Maximum if page_idx == idx else QSizePolicy.Ignored
            self.widget(page_idx).setMinimumSize( max_width,0 )
            self.widget(page_idx).setSizePolicy(h_policy, v_policy)
        #    self.widget(page_idx).adjustSize()
        return super().setCurrentIndex( idx )

class FileSelectionTreeWidget( QTreeWidget ):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.header().setSectionResizeMode( 0, QHeaderView.ResizeToContents )
        #self.setStretchLastSection(False)
        self.currentItemChanged.connect( self.handleSelect )

    @staticmethod
    def prettyNameFromPath( input_path ):
        # make words from the file stem, capitalize them, omit a leading number if possible
        # e.g. path/to/06_rhombic_tiling -> 'Rhombic Tiling'
        words = input_path.stem.split('_')
        if len(words) > 1 and words[0].isdigit(): words = words[1:]
        return ' '.join( word.capitalize() for word in words )

    def _addFile( self, heading, name, filepath ):
        item = QTreeWidgetItem( heading )
        item.setText( 0, name )
        item.setData( 0, Qt.UserRole, filepath.resolve() )
        return item

    def add2DExampleFile( self, filepath ):
        self._addFile( self.topLevelItem(0), self.prettyNameFromPath(filepath), filepath )

    def add3DExampleFile( self, filepath ):
        self._addFile( self.topLevelItem(1), self.prettyNameFromPath(filepath), filepath )

    def addUserFile( self, filepath, force_select = False ):
        item = self._addFile( self.topLevelItem(2), filepath.name, filepath )
        if( force_select ):
            self.setCurrentItem( item )

    newFileSelected = Signal( Path )

    def handleSelect( self, current_item, previous_item ):
        data = current_item.data( 0, Qt.UserRole )
        if data is not None:
            self.newFileSelected.emit( data )

class ColorButton(QPushButton):
    def __init__( self, *args, **kw ):
        super().__init__(*args, **kw)
        self.clicked.connect( self.chooseColor )
        self.colorChosen.connect( self.setColor )

    colorChosen = Signal(QColor)

    def chooseColor( self ):
        color = QColorDialog.getColor()
        self.colorChosen.emit(color)

    def setColor( self, color ):
        pixels = QPixmap(50,50)
        pixels.fill(color)
        icon = QIcon(pixels)
        self.setIcon( icon )



class UiLoader(QUiLoader):
    '''
    Athena UI file loader

    This class works around a shortcoming in QUiLoader: it doesn't provide
    a means to apply a ui into a given, existing object (except
    by the Qt Designer "promoted widgets" method, which in turn
    does not work for QMainWindow)

    This extended QUiLoader uses a given object instance
    as the default object for any un-parented widget in the loaded UI,
    allowing us to populate a pre-constructed widget from a ui file.

    It also works around bugs PYSIDE-124 and PYSIDE-77, which prevent
    QUiLoader from working properly with custom widgets when
    createWidget() is overridden.  We maintain our own custom
    widget map to use in this case.

    (QUiLoader has a lot of problems.)
    '''
    def __init__(self, baseInstance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseInstance = baseInstance
        self.customWidgets = {}

    def registerCustomWidget( self, cls ):
        self.customWidgets[ cls.__name__ ] = cls

    def createWidget( self, className, parent=None, name=''):
        if parent is None:
            # Don't create a new one, return the existing one.
            return self.baseInstance
        else:
            if( className in self.customWidgets ):
                return self.customWidgets[className] ( parent )
            else:
                return super().createWidget(className, parent, name)

    @staticmethod
    def populateUI( parent, filepath ):
        ui_file = QFile( filepath )
        ui_file.open( QFile.ReadOnly )
        try:
            ui_loader = UiLoader( parent )
            ui_loader.registerCustomWidget( AutoResizingStackedWidget )
            ui_loader.registerCustomWidget( FileSelectionTreeWidget )
            ui_loader.registerCustomWidget( ColorButton )
            ui_loader.load( ui_file )
        finally:
            ui_file.close()


def runLCBBTool( toolname, p2_input_file, p1_output_dir=Path('athena_tmp_output'),
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
    p1_output_dir = str(p1_output_dir)
    wd = os.path.join( ATHENA_DIR, 'tools', tooldir )
    toolpath = os.path.join( wd, tool )
    tool_call = [toolpath, p1_output_dir, p2_input_file, p3_scaffold, p4_edge_sections,
                           p5_vertex_design, p6_edge_number, p7_edge_length, p8_mesh_spacing, p9_runmode]
    tool_call_strs = [str(x) for x in tool_call]

    print('Calling {} as follows'.format(tool), tool_call_strs)
    return subprocess.run(tool_call_strs, stdout=subprocess.DEVNULL, stderr=None)


class AthenaWindow(QMainWindow):
    default_ui_path = os.path.join( ATHENA_DIR, 'ui', 'AthenaMainWindow.ui' )
    def __init__( self, ui_filepath=default_ui_path ):
        super( AthenaWindow, self).__init__(None)
        UiLoader.populateUI( self, ui_filepath )

        self.statusMsg = QLabel("Ready.")
        self.statusBar().addWidget(self.statusMsg)

        # Menu shortcuts cannot be set up in a cross-platform way within Qt Designer,
        # so do that here.
        self.actionOpen.setShortcut( QKeySequence.StandardKey.Open )
        self.actionQuit.setShortcut( QKeySequence.StandardKey.Quit )

        self.setupToolDefaults()
        self.enable2DControls()

        self.geomView = viewer.AthenaViewer()
        self.viewerWidget_dummy.deleteLater()
        del self.viewerWidget_dummy
        self.geomViewWidget = QWidget.createWindowContainer( self.geomView, self )
        self.upperLayout.insertWidget( 1, self.geomViewWidget )
        sizePolicy = QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        sizePolicy.setHorizontalStretch(1)
        self.geomViewWidget.setSizePolicy(sizePolicy) 

        self.perdixRunButton.clicked.connect(self.runPERDIX)
        self.talosRunButton.clicked.connect(self.runTALOS)
        self.daedalusRunButton.clicked.connect(self.runDAEDALUS2)
        self.metisRunButton.clicked.connect(self.runMETIS)

        self.actionOpen.triggered.connect( self.selectAndAddFileToGeomList )

        self.geometryList.newFileSelected.connect( self.newMesh )

        def _setupColorButton( button, setter, signal, init_value ):
            button.colorChosen.connect( setter )
            signal.connect( button.setColor )
            button.setColor( init_value )

        _setupColorButton( self.lineColorButton, self.geomView.setLineColor, self.geomView.lineColorChanged, self.geomView.lineColor() )
        _setupColorButton( self.flatColorButton, self.geomView.setFlatColor, self.geomView.flatColorChanged, self.geomView.flatColor() )
        _setupColorButton( self.bgColorButton, self.geomView.setBackgroundColor, self.geomView.backgroundColorChanged, self.geomView.backgroundColor() )

        self.actionQuit.triggered.connect(self.close)

        self.alphaSlider.valueChanged.connect( self.geomView.setAlpha )
        self.lineWidthSlider.valueChanged.connect( self.geomView.setLineWidth )
        self.lightDial.valueChanged.connect( self.geomView.setLightOrientation )

        self.newMesh(None)
        self.show()

    def setupToolDefaults( self ):

        perdix_inputs = Path(ATHENA_DIR, "sample_inputs", "PERDIX")
        for ply in perdix_inputs.glob('*.ply'):
            self.geometryList.add2DExampleFile( ply )

        metis_inputs = Path(ATHENA_DIR, "sample_inputs", "METIS" )
        for ply in metis_inputs.glob("*.ply"):
            self.geometryList.add2DExampleFile( ply )

        talos_inputs = Path(ATHENA_DIR, "sample_inputs", "TALOS")
        for ply in talos_inputs.glob("*.ply"):
            self.geometryList.add3DExampleFile( ply )

        daedalus_inputs = Path(ATHENA_DIR, "sample_inputs", "DAEDALUS2" )
        for ply in daedalus_inputs.glob("*.ply"):
            self.geometryList.add3DExampleFile( ply )


    def selectAndAddFileToGeomList( self ):
        fileName = QFileDialog.getOpenFileName( self,
                                               "Open geometry file",
                                               os.path.join(ATHENA_DIR, 'sample_inputs'),
                                               "Geometry files (*.ply)")
        filepath = Path(fileName[0])
        if( filepath.is_file() ):
            self.geometryList.addUserFile( filepath, force_select=True )

    def enable2DControls( self ):
        self.renderControls.setCurrentIndex( 0 )
        self.toolControls.setCurrentIndex( 0 )

    def enable3DControls( self ):
        self.renderControls.setCurrentIndex( 1 )
        self.toolControls.setCurrentIndex( 1 )


    def newMesh( self, meshFile ):
        if( meshFile is None ): return
        mesh_3d = self.geomView.reloadGeom( meshFile )
        if( mesh_3d ):
            self.enable3DControls()
        else:
            self.enable2DControls()

    def updateStatus( self, msg ):
        self.statusMsg.setText( msg )

    def _toolFilenames( self, toolname ):
        active_item = self.geometryList.currentItem()
        infile_path = active_item.data(0, Qt.UserRole)
        infile_name = active_item.text(0)
        outfile_dir_path = ATHENA_OUTPUT_DIR / toolname / infile_name
        return infile_path, outfile_dir_path

    def runPERDIX( self ):
        self.updateStatus('Running PERDIX...')
        infile_path, outfile_dir_path = self._toolFilenames( 'PERDIX' )
        process = runLCBBTool ('PERDIX',
                               p1_output_dir=outfile_dir_path,
                               p2_input_file=infile_path,
                               p7_edge_length=self.perdixEdgeLengthSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('PERDIX returned {}.'.format(human_retval))

    def runTALOS( self ):
        self.updateStatus('Running TALOS...')
        infile_path, outfile_dir_path = self._toolFilenames( 'TALOS' )
        process = runLCBBTool('TALOS',
                              p1_output_dir=outfile_dir_path,
                              p2_input_file=infile_path,
                              p4_edge_sections=self.talosEdgeSectionBox.currentIndex()+2,
                              p5_vertex_design=self.talosVertexDesignBox.currentIndex()+1,
                              p7_edge_length=self.talosEdgeLengthSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('TALOS returned {}.'.format(human_retval))

    def runDAEDALUS2( self ):
        self.updateStatus('Running DAEDALUS...')
        infile_path, outfile_dir_path = self._toolFilenames( 'DAEDALUS2' )
        process = runLCBBTool('DAEDALUS2',
                              p1_output_dir=outfile_dir_path,
                              p2_input_file=infile_path,
                              p4_edge_sections=1, p5_vertex_design=2,
                              p7_edge_length=self.daedalusEdgeLengthSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('DAEDALUS returned {}.'.format(human_retval))


    def runMETIS( self ):
        self.updateStatus('Running METIS...')
        infile_path, outfile_dir_path = self._toolFilenames( 'METIS' )
        process = runLCBBTool ('METIS',
                               p1_output_dir=outfile_dir_path,
                               p2_input_file=infile_path,
                               p4_edge_sections=3, p5_vertex_design=2,
                               p7_edge_length=self.metisEdgeLengthSpinner.value())
        human_retval = 'success' if process.returncode == 0 else 'failure ({})'.format(process.returncode)
        self.updateStatus('METIS returned {}.'.format(human_retval))


