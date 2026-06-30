from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.assisted_browser_export_page import AssistedBrowserExportPage
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class AssistedBrowserExportScreen(QWidget):
    def __init__(self, legacy_state: dict, on_home, on_back) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(StepHeader(bi("Assisted Browser Export", "辅助浏览器导出")))
        nav = QHBoxLayout()
        home = SecondaryButton(bi("Home", "主页"))
        home.clicked.connect(on_home)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        nav.addWidget(home)
        nav.addWidget(back)
        layout.addLayout(nav)
        layout.addWidget(AssistedBrowserExportPage(legacy_state))
