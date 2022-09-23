def main():
    import sys

    import qdarkstyle
    from pymmcore_plus import CMMCorePlus
    from qtpy.QtWidgets import QApplication

    from pyptc._main_window import MainWindow

    core = CMMCorePlus.instance()
    core.loadSystemConfiguration()
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    window = MainWindow()
    window.show()

    app.exec_()

main()