#! /usr/bin/env python

import sys
from PySide2.QtWidgets import QApplication
from athena.mainwindow import AthenaWindow

app = QApplication(sys.argv)
window = AthenaWindow( )
sys.exit(app.exec_())
