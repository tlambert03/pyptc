from __future__ import annotations

from typing import TYPE_CHECKING, Optional, cast

from pymmcore_plus import CMMCorePlus
from qtpy.QtWidgets import QVBoxLayout, QWidget
from vispy import scene


if TYPE_CHECKING:
    import numpy as np


class ImageView(scene.widgets.ViewBox):
    def __init__(self, *args, **kwargs):
        self.image = scene.visuals.Image(cmap="grays")
        super().__init__(*args, **kwargs)
        self.camera = scene.PanZoomCamera(aspect=1)
        self.add(self.image)

    def set_data(self, img: np.ndarray) -> None:
        self.image.set_data(img)
        self.camera.set_range(margin=0)
        self.autoscale()

    def autoscale(self) -> None:
        img = self.image._data
        clim = (img.min(), img.max())
        self.image.clim = clim

    @property
    def cmap(self) -> np.ndarray:
        return self.image.cmap

    @cmap.setter
    def cmap(self, value: str) -> None:
        self.image.cmap = value


class Image(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        camera="panzoom",
        size=(512, 512),
        data=None,
    ):
        super().__init__(parent)
        self._mmc = CMMCorePlus.instance()

        self._canvas = scene.SceneCanvas(keys="interactive", show=True, size=size)
        self._grid = self._canvas.central_widget.add_grid()
        self._grid._default_class = ImageView

        if data is not None:
            self[0, 0].set_data(data)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._canvas.native)

    def __getitem__(self, key: tuple[int, int]) -> ImageView:
        return self._grid[key]

    def autoscale(self) -> None:
        for (*_, wdg) in self._grid._grid_widgets.values():
            wdg.autoscale()

    @property
    def cmap(self) -> np.ndarray:
        return self[0, 0].cmap

    @cmap.setter
    def cmap(self, value: str) -> None:
        self[0, 0].cmap = value
