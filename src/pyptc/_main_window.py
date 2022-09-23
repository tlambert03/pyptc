from __future__ import annotations

from pymmcore_plus import CMMCorePlus
from pymmcore_widgets import ImagePreview, LiveButton, SnapButton, ExposureWidget
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from fonticon_mdi6 import MDI6
from superqt.fonticon import setTextIcon


class CameraSelector(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._mmc = CMMCorePlus.instance()

        lbl = QLabel("Camera:")
        lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._combo = QComboBox()
        self._combo.currentIndexChanged.connect(self._set_camera)

        self._reload_button = QPushButton("")
        self._reload_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._reload_button.clicked.connect(self._reload_cameras)
        setTextIcon(self._reload_button, MDI6.refresh, 22)

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(lbl)
        self.layout().addWidget(self._combo)
        self.layout().addWidget(self._reload_button)

    def _reload_cameras(self) -> None:
        from ._core_utils import load_all_cameras

        self._combo.clear()
        for device in load_all_cameras(self._mmc):
            self._combo.addItem(device.label, device)

    def _set_camera(self, index: int) -> None:
        if device := self._combo.itemData(index):
            self._mmc.setCameraDevice(device.label)


class PTCControls(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.camera_selector = CameraSelector()
        self.snap_button = SnapButton()
        self.live_button = LiveButton()
        self.exposure = ExposureWidget()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.camera_selector)
        self.layout().addWidget(self.exposure)
        self.layout().addWidget(self.snap_button)
        self.layout().addWidget(self.live_button)

        self.setMaximumWidth(300)


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
