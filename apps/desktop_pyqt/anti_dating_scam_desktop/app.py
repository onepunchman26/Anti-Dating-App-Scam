import sys

from PySide6.QtWidgets import QApplication

from anti_dating_scam_desktop.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AI-SlowMatch")
    window = MainWindow()
    window.resize(1100, 760)
    window.show()
    return app.exec()
