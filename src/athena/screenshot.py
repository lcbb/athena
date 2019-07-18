import os

from PySide2.QtGui import QImage, QImageWriter
from PySide2.QtWidgets import QDialog

from athena import mainwindow, ATHENA_DIR, viewer


class ScreenshotDialog(QDialog):

    default_ui_path = os.path.join( ATHENA_DIR, 'ui', 'ScreenshotDialog.ui' )

    def __init__( self, parent, view, ui_filepath=default_ui_path ):
        super().__init__(parent)
        mainwindow.UiLoader.populateUI( self, ui_filepath )
        self.view = view
        self.dpiBox.setValue( self.view.screen().physicalDotsPerInch() )
        self.view.widthChanged.connect( self.setWidthPixels )
        self.view.heightChanged.connect( self.setHeightPixels )

        self.unitsBox.currentIndexChanged.connect( self.widthBox.setCurrentIndex )
        self.unitsBox.currentIndexChanged.connect( self.heightBox.setCurrentIndex )

    def setWidthPixels(self, w):
        self.widthBoxPixels.setValue(w)
        self.widthBoxInches.setValue( w / self.dpiBox.value() )

    def setHeightPixels(self, h):
        self.heightBoxPixels.setValue(h)
        self.heightBoxInches.setValue( h / self.dpiBox.value() )

        



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

