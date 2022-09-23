from __future__ import annotations

from pymmcore_widgets import ImagePreview
from ._widgets import PTCControls
from qtpy.QtWidgets import QHBoxLayout, QMainWindow, QWidget


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("PyPTC")

        self._image = ImagePreview()
        self._controls = PTCControls(self)

        central = QWidget()
        central.setLayout(QHBoxLayout())
        central.layout().addWidget(self._image)
        central.layout().addWidget(self._controls)
        self.setCentralWidget(central)

        self.resize(900, 600)
