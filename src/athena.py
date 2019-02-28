#! /usr/bin/env python
import sys

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow, QApplication, QLabel, QStatusBar
from PySide2.QtCore import QFile

class AthenaWindow(QMainWindow):
    def __init__( self, ui_file_path ):
        super( AthenaWindow, self).__init__(None)
        ui_file = QFile( ui_file_path )
        ui_file.open( QFile.ReadOnly)

        ui_loader = QUiLoader()
        self.ui = ui_loader.load(ui_file)
        ui_file.close()

        self.statusMsg = QLabel("Ready.")
        self.ui.statusBar().addWidget(self.statusMsg)

        self.ui.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AthenaWindow('ui/AthenaMainWindow.ui')
    sys.exit(app.exec_())
