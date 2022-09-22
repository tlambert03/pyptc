from contextlib import contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING

from pymmcore_plus import DeviceType, RemoteMMCore
from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    import napari.viewer

from ._core_utils import load_cameras

reload_icon = QIcon(str(Path(__file__).parent / "icons" / "sync-alt.svg"))
camera_icon = QIcon(str(Path(__file__).parent / "icons" / "camera.svg"))
video_icon = QIcon(str(Path(__file__).parent / "icons" / "video.svg"))
cog_icon = QIcon(str(Path(__file__).parent / "icons" / "cog.svg"))


@contextmanager
def signals_blocked(obj):
    obj.blockSignals(True)
    try:
        yield
    finally:
        obj.blockSignals(False)


class MainWindow(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer" = None, parent=None) -> None:
        super().__init__(parent)
        self._viewer = viewer
        self.setLayout(QVBoxLayout())
        self._core = RemoteMMCore()
        self._core.events.propertiesChanged.connect(lambda *e: print("propchange", e))
        self._timer = QTimer()
        self._timer.timeout.connect(self.update_viewer)

        # widgets
        self._cameras = QComboBox()
        self._reload_camera_btn = QPushButton()
        self._reload_camera_btn.setFixedWidth(25)
        self._reload_camera_btn.setIcon(reload_icon)
        self._snap_btn = QPushButton("Snap")
        self._snap_btn.setIcon(camera_icon)
        self._live_btn = QPushButton("Live")
        self._live_btn.setIcon(video_icon)
        self._exposure = QSpinBox()
        self._exposure.setRange(1, 10000)
        self._exposure.setValue(50)
        self._settings_btn = QPushButton()
        self._settings_btn.setIcon(cog_icon)
        self._settings_btn.setFixedWidth(25)
        self._status = QLabel()

        # connections
        self._cameras.currentTextChanged.connect(self._on_camera_change)
        self._reload_camera_btn.clicked.connect(self._reload_cameras)
        self._snap_btn.clicked.connect(self._on_snap)
        self._live_btn.clicked.connect(self._toggle_live)
        self._settings_btn.clicked.connect(self._show_settings)
        self._exposure.editingFinished.connect(self._on_exposure_changed)

        @self._core.events.exposureChanged.connect
        def _on_exchange(label, e):
            self._exposure.setValue(e)

        # layout
        row = QHBoxLayout()
        row.addWidget(self._cameras)
        row.addWidget(self._reload_camera_btn)
        self.layout().addLayout(row)

        row = QHBoxLayout()
        label = QLabel("exposure (ms):")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row.addWidget(label)
        row.addWidget(self._exposure)
        row.addWidget(self._settings_btn)
        self.layout().addLayout(row)

        row = QHBoxLayout()
        row.addWidget(self._snap_btn)
        row.addWidget(self._live_btn)
        self.layout().addLayout(row)
        self.layout().addWidget(self._status)

        self._reload_cameras()
        self._cameras.setCurrentText("DemoCamera-DCam")

    def _on_exposure_changed(self):
        mid_seq = self._core.isSequenceRunning()
        if mid_seq:
            self._stop_live()
        self._core.setExposure(self._exposure.value())
        if mid_seq:
            self._start_live()

    def _show_settings(self):
        from ._props_widget import device_widget

        self.dw = device_widget(self._core, self._core.getCameraDevice())
        self.dw.show()

    def _on_snap(self):
        self._stop_live()
        self.update_viewer()

    def _start_live(self):
        self._timer.start(self._exposure.value())
        self._live_btn.setText("Stop")

    def _stop_live(self):
        self._core.stopSequenceAcquisition()
        self._timer.stop()
        self._live_btn.setText("Live")

    def _toggle_live(self, event=None):
        self._start_live() if not self._timer.isActive() else self._stop_live()

    def update_viewer(self, data=None):

        if data is None:
            try:
                self._core.snapImage()
                data = self._core.getImage()
            except RuntimeError:
                return
        layer_name = "PTC preview"
        try:
            self._viewer.layers[layer_name].data = data
        except KeyError:
            self._viewer.add_image(data, name=layer_name)

    def _reload_cameras(self):
        self._core.unloadAllDevices()
        with signals_blocked(self._cameras):
            self._cameras.clear()
            load_cameras(self._core)
            for label in self._core.getLoadedDevicesOfType(DeviceType.Camera):
                self._cameras.addItem(label)

    def _on_camera_change(self, label):
        if not label:
            return

        with suppress(RuntimeError):
            self._core.initializeDevice(label)

        self._core.setCameraDevice(label)
        try:
            self._core.snapImage()
        except RuntimeError as e:
            self._status.setText(str(e))
            QTimer.singleShot(5000, self._status.clear)
