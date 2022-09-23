import sys
import numpy as np
import qdarkstyle
from pymmcore_plus import CMMCorePlus
from qtpy.QtWidgets import QApplication

from pyptc._main_window import MainWindow

core = CMMCorePlus.instance()
core.loadSystemConfiguration()
app = QApplication.instance() or QApplication(sys.argv)
app.setStyleSheet(qdarkstyle.load_stylesheet())

window = MainWindow()
ctrls = window._controls
hist = ctrls.histogram

window.show()

# app.exec_()