import os
from contextlib import contextmanager

from PySide2.QtGui import QImage, QImageWriter
from PySide2.QtWidgets import QDialog, QFileDialog
from PySide2.QtCore import QObject

from athena import mainwindow, ATHENA_DIR, viewer

@contextmanager
def SignalBlocker( *args ):
    '''
    Python context manager to block signals to any number of QObjects;
    
    '''
    original_signals = [ a.blockSignals(True) for a in args ]
    yield
    for a, s in zip( args, original_signals ):
        # restore original settings
        a.blockSignals(s)


class ScreenshotDialog(QDialog):

    default_ui_path = os.path.join( ATHENA_DIR, 'ui', 'ScreenshotDialog.ui' )

    def __init__( self, parent, view, ui_filepath=default_ui_path ):
        super().__init__(parent)
        mainwindow.UiLoader.populateUI( self, ui_filepath )
        self.view = view
        self.dpiBox.setValue( self.view.screen().physicalDotsPerInch() )

        # User may choose between inches and pixels
        self.unitsBox.currentIndexChanged.connect( self.widthBox.setCurrentIndex )
        self.unitsBox.currentIndexChanged.connect( self.heightBox.setCurrentIndex )

        # Automatically track changes to the size of the viewer window in the dimension boxes
        self.view.widthChanged.connect( self.setWidthPixels )
        self.view.heightChanged.connect( self.setHeightPixels )

        # User changes to spinners are reflected across units,
        # and if the proportionBox is checked, then width updates modify height
        # and vice-versa.
        self.widthBoxPixels.valueChanged.connect( self.changeWidthPixels )
        self.heightBoxPixels.valueChanged.connect( self.changeHeightPixels )
        self.widthBoxInches.valueChanged.connect( self.changeWidthInches )
        self.heightBoxInches.valueChanged.connect( self.changeHeightInches )
        self.dpiBox.valueChanged.connect( self.changeDpi )

        self.output_dir = "HOME"
        self.savetoLabel.setText( self.output_dir )
        self.dirChooserButton.clicked.connect( self.chooseOutputDir )

        self.ratio = 1

    def _updateRatio( self ):
        self.ratio = self.widthBoxInches.value() / max(.00001,self.heightBoxInches.value())

    # "set*" functions are absolute and do not respect the proportionality setting
    def setWidthPixels(self, w):
        with SignalBlocker( self.widthBoxPixels, self.widthBoxInches ):
            self.widthBoxPixels.setValue(w)
            self.widthBoxInches.setValue( w / self.dpiBox.value() )
            self._updateRatio()

    def setHeightPixels(self, h):
        with SignalBlocker( self.heightBoxPixels, self.heightBoxInches ):
            self.heightBoxPixels.setValue(h)
            self.heightBoxInches.setValue( h / self.dpiBox.value() )
            self._updateRatio()

    def setSizePixels( self, w, h ):
        with SignalBlocker( self.widthBoxPixels, self.heightBoxPixels, 
                            self.widthBoxInches, self.heightBoxInches ):
            self.widthBoxPixels.setValue(w)
            self.heightBoxPixels.setValue(h)
            self.widthBoxInches.setValue( w / self.dpiBox.value() )
            self.heightBoxInches.setValue( h / self.dpiBox.value() )
            self._updateRatio()

    def setWidthInches(self, w):
        self.setWidthPixels( w * self.dpiBox.value() )

    def setHeightInches( self, h):
        self.setHeightPixels( h * self.dpiBox.value() )

    # "change*" functions respect the proportionality setting, if it's enabled
    def changeWidthPixels(self, w):
        ratio = self.ratio
        self.widthBoxInches.setValue( w / self.dpiBox.value() )
        if( self.proportionBox.isChecked() ):
            self.setHeightPixels( w / ratio )
        else:
            self._updateRatio()

    def changeHeightPixels(self, h):
        ratio = self.ratio
        self.heightBoxInches.setValue( h / self.dpiBox.value() )
        if( self.proportionBox.isChecked() ):
            self.setWidthPixels( h * ratio )
        else:
            self._updateRatio()

    def changeWidthInches(self, w):
        self.changeWidthPixels( w * self.dpiBox.value() )

    def changeHeightInches(self, h):
        self.changeHeightPixels( h * self.dpiBox.value() )

    def changeDpi(self, d):
        # Dpi changes always change the pixels values and keep the inch values as-is.
        self.setSizePixels( self.widthBoxInches.value() * d, self.heightBoxInches.value() * d)

    def chooseOutputDir( self ):
        self.output_dir = QFileDialog.getExistingDirectory( self, "Choose Screenshot Directory", self.output_dir,
                                                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks )
        self.savetoLabel.setText( self.output_dir )

class ScreenshotMonger:
    def __init__(self, viewer):
        self.pendingScreenshot = None
        self.viewer = viewer

    def register( self, screenshot ):
        print("Registering", screenshot)
        assert( self.pendingScreenshot == None )
        self.pendingScreenshot = screenshot
        screenshot.completed.connect( self.handleCompleted )
        assert( screenshot.isComplete() == False )

    def handleCompleted( self ):
        print("Completed", self.pendingScreenshot.captureId())
        iw = QImageWriter()
        iw.setFormat(str.encode('png'))
        gamma = self.viewer.framegraph.viewport.gamma()
        iw.setGamma( gamma )
        iw.setFileName( "img{}.png".format(self.pendingScreenshot.captureId()) )
        img = self.pendingScreenshot.image()
        print(img.format())
        img2 = QImage(img.bits(), img.width(), img.height(), QImage.Format_ARGB32)
        img3 = img2.convertToFormat( QImage.Format_RGB32 )
        #iw.write( self.pendingScreenshot.image().convertToFormat(QImage.Format_ARGB32_Premultiplied))
        iw.write(img3)

        self.pendingScreenshot.completed.disconnect( self.handleCompleted )
        self.pendingScreenshot = None
        self.viewer.renderSettings().setRenderPolicy(self.viewer.renderSettings().OnDemand)
        self.viewer.framegraph.setOnscreenRendering()

