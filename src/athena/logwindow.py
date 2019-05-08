import os

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, QStatusBar, QFileDialog, QWidget, QSizePolicy, QColorDialog, QStackedWidget, QTreeWidget, QTreeWidgetItem, QHeaderView, QDialog
from PySide2.QtGui import QKeySequence, QPixmap, QIcon, QColor, QFont, QFontInfo
from PySide2.QtCore import QFile, Qt, Signal

from athena import mainwindow, ATHENA_DIR

# Function to find some kind of monospace font in Qt
# Thanks to the answer at https://stackoverflow.com/questions/18896933/qt-qfont-selection-of-a-monospace-font-doesnt-work

def findMonospaceFont():
    def isFixedPitch(font):
        return QFontInfo(font).fixedPitch()
    font = QFont('monospace')
    print('mono')
    if isFixedPitch(font): return font
    print('hint')
    font.setStyleHint(QFont.Monospace)
    if isFixedPitch(font): return font
    print('hint')
    font.setStyleHint(QFont.TypeWriter)
    if isFixedPitch(font): return font
    print('courier')
    font.setFamily("courier")
    if isFixedPitch(font): return font
    print('fail')
    return font


class LogWindow(QDialog):
    default_ui_path = os.path.join( ATHENA_DIR, 'ui', 'LogWindow.ui' )
    def __init__( self, ui_filepath=default_ui_path ):
        super().__init__(None)
        mainwindow.UiLoader.populateUI( self, ui_filepath )
        self.font = findMonospaceFont()
        self.textView.setFont(self.font)


    def appendText( self, text ):
        self.textView.appendPlainText( text )
        self.textView.verticalScrollBar().setValue( self.textView.verticalScrollBar().maximum() )


