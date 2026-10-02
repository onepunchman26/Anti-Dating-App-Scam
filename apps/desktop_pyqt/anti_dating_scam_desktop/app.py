import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from anti_dating_scam import __version__
from anti_dating_scam_desktop import i18n
from anti_dating_scam_desktop.main_window import MainWindow


def _init_language() -> None:
    """Use the saved language if any, otherwise follow the system locale."""
    if i18n.load_saved_language() is not None:
        return
    is_chinese = QLocale.system().language() == QLocale.Language.Chinese
    i18n.set_language("zh" if is_chinese else "en", persist=False)


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AI-SlowMatch")
    app.setApplicationVersion(__version__)
    _init_language()
    window = MainWindow()
    window.resize(1100, 760)
    window.show()
    return app.exec()
