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
    if isFixedPitch(font): return font
    font.setStyleHint(QFont.Monospace)
    if isFixedPitch(font): return font
    font.setStyleHint(QFont.TypeWriter)
    if isFixedPitch(font): return font
    font.setFamily("courier")
    if isFixedPitch(font): return font
    return font

class LogWindow(QDialog):
    default_ui_path = os.path.join( ATHENA_DIR, 'ui', 'LogWindow.ui' )
    def __init__( self, parent, ui_filepath=default_ui_path ):
        super().__init__(parent)
        mainwindow.UiLoader.populateUI( self, ui_filepath )
        self.font = findMonospaceFont()
        self.textView.setFont(self.font)


    def appendText( self, text ):
        self.textView.appendPlainText( text )
        self.textView.verticalScrollBar().setValue( self.textView.verticalScrollBar().maximum() )

class WriteWrapper:
    '''A file-like wrapper for the log window, useful to pass to an external
    tool that wants to write to a log file (i.e. pdbgen)'''
    def __init__(self, wrapped):
        self.wrapped = wrapped
    def write(self, string):
        stripped = string.strip()
        if(len(stripped) > 0):
            self.wrapped.appendText(stripped)
    def close(self): pass


