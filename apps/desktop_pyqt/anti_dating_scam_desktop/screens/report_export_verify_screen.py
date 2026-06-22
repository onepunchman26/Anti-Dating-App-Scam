from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from anti_dating_scam_desktop.widgets.report_export_verify_page import ReportExportVerifyPage
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ReportExportVerifyScreen(QWidget):
    def __init__(self, legacy_state: dict, on_home, on_back) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(StepHeader("Export or Verify Report"))
        nav = QHBoxLayout()
        home = SecondaryButton("Home")
        home.clicked.connect(on_home)
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        nav.addWidget(home)
        nav.addWidget(back)
        layout.addLayout(nav)
        layout.addWidget(ReportExportVerifyPage(legacy_state))
