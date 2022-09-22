from napari_plugin_engine import napari_hook_implementation


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    from pyptc._main_window import MainWindow

    return MainWindow, {'name': 'Photon Transfer Curve'}