import sys
import numpy as np
import qdarkstyle
from pymmcore_plus import CMMCorePlus
from qtpy.QtWidgets import QApplication


core = CMMCorePlus.instance()
core.loadSystemConfiguration()
core.setProperty('Camera', 'Mode', 'Noise')

app = QApplication.instance() or QApplication(sys.argv)
app.setStyleSheet(qdarkstyle.load_stylesheet())

# from pyptc._main_window import MainWindow
# window = MainWindow()
# window.show()
# ctrls = window._controls
# hist = ctrls.histogram


from pyptc._ptc import collect_stats, RunningStat
from pyptc._image import Image
window = Image()
window.show()
window[0, 0].set_data(core.snap())
window[1, 0].set_data(core.snap())

def update(img, stats: RunningStat):
    window[0, 0].set_data(stats.mean())
    window[1, 0].set_data(stats.var())
    app.processEvents()

def snap():
    return np.random.poisson(size=(512,512))
stats = collect_stats(snap, n=1000, callback=update)

# app.exec_()