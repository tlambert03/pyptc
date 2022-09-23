"""
code from my napari histogram PR
"""
from typing import cast
from vispy.plot import Fig, PlotWidget
from vispy import scene, visuals
from qtpy.QtWidgets import QWidget, QHBoxLayout
import numpy as np


class PanZoom1DCamera(scene.cameras.PanZoomCamera):
    def __init__(self, axis: int=1, *args, **kwargs):
        self.axis = axis
        super().__init__(*args, **kwargs)

    def zoom(self, factor, center=None):
        if np.isscalar(factor):
            factor = [factor, factor]
        factor[self.axis] = 1
        return super().zoom(factor, center=center)

    def pan(self, pan):
        pan[self.axis] = 0
        self.rect = self.rect + pan

AXIS_KWARGS = {
    'text_color': 'k',
    'axis_color': 'k',
    'tick_color': 'k',
    'tick_width': 1,
    'tick_font_size': 8,
    'tick_label_margin': 12,
    'axis_label_margin': 50,
    'minor_tick_length': 2,
    'major_tick_length': 5,
    'axis_width': 1,
    'axis_font_size': 9,
}

class _PlotWidget(PlotWidget):
    show_yaxis: bool = True
    show_xaxis: bool = True
    lock_axis: int | None = 1

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def _configure_2d(self, fg_color=None):
        if self._configured:
            return

        #         c0        c1      c2      c3      c4      c5         c6
        #     +---------+-------+-------+-------+-------+---------+---------+
        #  r0 |         |                       | title |         |         |
        #     |         +-----------------------+-------+---------+         |
        #  r1 |         |                       | cbar  |         |         |
        #     | ------- +-------+-------+-------+-------+---------+ ------- |
        #  r2 | padding | cbar  | ylabel| yaxis |  view | cbar    | padding |
        #     | ------- +-------+-------+-------+-------+---------+ ------- |
        #  r3 |         |                       | xaxis |         |         |
        #     |         +-----------------------+-------+---------+         |
        #  r4 |         |                       | xlabel|         |         |
        #     |         +-----------------------+-------+---------+         |
        #  r5 |         |                       | cbar  |         |         |
        #     |---------+-----------------------+-------+---------+---------|
        #  r6 |                                 |padding|                   |
        #     +---------+-----------------------+-------+---------+---------+

        # PADDING
        self.padding_right = self.grid.add_widget(None, row=2, col=6)
        self.padding_right.width_min = 1
        self.padding_right.width_max = 5
        self.padding_bottom = self.grid.add_widget(None, row=6, col=4)
        self.padding_bottom.height_min = 1
        self.padding_bottom.height_max = 3

        # TITLE
        self.title_widget = self.grid.add_widget(self.title, row=0, col=4)
        self.title_widget.height_min = self.title_widget.height_max = (
            30 if self.title.text else 5
        )

        # COLORBARS
        self.cbar_top = self.grid.add_widget(None, row=1, col=4)
        self.cbar_top.height_max = 0
        self.cbar_left = self.grid.add_widget(None, row=2, col=1)
        self.cbar_left.width_max = 0
        self.cbar_right = self.grid.add_widget(None, row=2, col=5)
        self.cbar_right.width_max = 0
        self.cbar_bottom = self.grid.add_widget(None, row=5, col=4)
        self.cbar_bottom.height_max = 0

        # Y AXIS
        self.yaxis = scene.AxisWidget(orientation='left', **AXIS_KWARGS)
        self.yaxis_widget = self.grid.add_widget(self.yaxis, row=2, col=3)
        if self.show_yaxis:
            self.yaxis_widget.width_max = 30
            self.ylabel_widget = self.grid.add_widget(
                self.ylabel, row=2, col=2
            )
            # self.ylabel_widget.width_max = 10 if self.ylabel.text else 1 
            self.ylabel_widget.width_max = 1 
            self.padding_left = self.grid.add_widget(None, row=2, col=0)
            self.padding_left.width_max = 10
        else:
            self.yaxis.visible = False
            self.yaxis.width_max = 1
            self.padding_left = self.grid.add_widget(
                None, row=2, col=0, col_span=3
            )
            self.padding_left.width_max = 5

        self.padding_left.width_min = 1
        # X AXIS
        self.xaxis = scene.AxisWidget(orientation='bottom', **AXIS_KWARGS)
        self.xaxis_widget = self.grid.add_widget(self.xaxis, row=3, col=4)
        self.xaxis_widget.height_max = 20 if self.show_xaxis else 0
        self.xlabel_widget = self.grid.add_widget(self.xlabel, row=4, col=4)
        # self.xlabel_widget.height_max = 10 if self.xlabel.text else 0
        self.xlabel_widget.height_max = 0

        # VIEWBOX (this has to go last, see vispy #1748)
        self.view = self.grid.add_view(
            row=2, col=4, border_color=None, bgcolor=None
        )

        if self.lock_axis is not None:
            self.view.camera = PanZoom1DCamera(self.lock_axis)
        else:
            self.view.camera = 'panzoom'
        self.camera = self.view.camera

        self._configured = True
        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)

class HistogramVisual(visuals.MeshVisual):
    """Visual that calculates and displays a histogram of data

    Parameters
    ----------
    data : array-like
        Data to histogram. Currently only 1D data is supported.
    bins : int | array-like
        Number of bins, or bin edges.
    color : instance of Color
        Color of the histogram.
    orientation : {'h', 'v'}
        Orientation of the histogram.
    """
    _bins: int

    def __init__(self, data, bins=10, color="w", orientation="h"):
        if not isinstance(orientation, str) or orientation not in ("h", "v"):
            raise ValueError('orientation must be "h" or "v", not %s' % (orientation,))
        self._orientation = orientation
        self._bins = bins
        rr, tris = self._calc_hist(data, bins)
        visuals.MeshVisual.__init__(self, rr, tris, color=color)

    def _calc_hist(
        self, data: np.ndarray, bins: int | None
    ) -> tuple[np.ndarray, np.ndarray]:
        if bins is not None:
            self._bins = bins
        data = np.asarray(data)
        if data.ndim != 1:
            raise ValueError("Only 1D data currently supported")

        X, Y = (0, 1) if self._orientation == "h" else (1, 0)
        # do the histogramming
        data, bin_edges = np.histogram(data, self._bins)
        # construct our vertices
        rr = np.zeros((3 * len(bin_edges) - 2, 3), np.float32)
        rr[:, X] = np.repeat(bin_edges, 3)[1:-1]
        rr[1::3, Y] = data
        rr[2::3, Y] = data
        bin_edges.astype(np.float32)
        # and now our tris
        tris = np.zeros((2 * len(bin_edges) - 2, 3), np.uint32)
        offsets = 3 * np.arange(len(bin_edges) - 1, dtype=np.uint32)[:, np.newaxis]
        tri_1 = np.array([0, 2, 1])
        tri_2 = np.array([2, 0, 3])
        tris[::2] = tri_1 + offsets
        tris[1::2] = tri_2 + offsets
        return rr, tris

    def set_data(self, data: np.ndarray, bins: int | None = None) -> None:
        rr, tris = self._calc_hist(data, bins)
        super().set_data(vertices=rr, faces=tris)


HistogramNode = scene.visuals.create_visual_node(HistogramVisual)


class Histogram(QWidget):
    def __init__(self, data=None, bins=100, parent: QWidget | None = None):
        super().__init__(parent)
        from pymmcore_plus import CMMCorePlus
        self._mmc = CMMCorePlus.instance()
        self._mmc.events.imageSnapped.connect(self.set_data)

        self._fig = Fig()
        self._fig._grid._default_class = _PlotWidget

        self._plot = cast(PlotWidget, self._fig[0, 0])
        self._plot._configure_2d()

        if data is None:
            data = np.random.rand(100)

        self._hist = HistogramNode(data, bins=bins, color="k")
        self._plot.view.add(self._hist)
        self._plot.view.camera.set_range(margin=0)

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._fig.native)
        self.setMaximumHeight(200)

    def set_data(self, data: np.ndarray) -> None:
        self._hist.set_data(data.ravel())
        self.autoscale()
    
    def autoscale(self):
        verts = self._hist._meshdata.get_vertices()
        x0, y0, _ = np.min(verts, axis=0)
        x1, y1, _ = np.max(verts, axis=0)
        self._plot.view.camera.set_range(x=(x0, x1), y=(y0, y1), margin=0)


    @property
    def bins(self) -> int:
        return self._hist._bins
    
    @bins.setter
    def bins(self, value: int) -> None:
        self._hist._bins = value
