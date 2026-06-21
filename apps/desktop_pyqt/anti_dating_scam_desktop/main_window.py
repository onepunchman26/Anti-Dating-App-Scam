from PySide6.QtWidgets import QMainWindow, QTabWidget

from anti_dating_scam_desktop.widgets.consent_page import ConsentPage
from anti_dating_scam_desktop.widgets.conversation_analysis_page import (
    ConversationAnalysisPage,
)
from anti_dating_scam_desktop.widgets.profile_import_page import ProfileImportPage
from anti_dating_scam_desktop.widgets.profile_view_page import ProfileViewPage
from anti_dating_scam_desktop.widgets.provider_settings_page import ProviderSettingsPage
from anti_dating_scam_desktop.widgets.report_export_verify_page import (
    ReportExportVerifyPage,
)
from anti_dating_scam_desktop.widgets.trust_ladder_page import TrustLadderPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI-SlowMatch - Local Trust Tool")
        self.state = {
            "consent_confirmed": False,
            "manual_notes": "",
            "memory_summary": "",
            "chatgpt_export_summary": None,
            "profile": None,
            "risk_report": None,
            "signed_report": None,
            "provider_name": "Mock",
            "model_name": "local-rule-based-mvp",
        }

        tabs = QTabWidget()
        tabs.addTab(ConsentPage(self.state), "Consent / Safety")
        tabs.addTab(ProfileImportPage(self.state), "Import My Profile")
        tabs.addTab(ProfileViewPage(self.state), "Generate Local Personal Profile")
        tabs.addTab(ConversationAnalysisPage(self.state), "Conversation Risk Analysis")
        tabs.addTab(TrustLadderPage(self.state), "Trust Ladder")
        tabs.addTab(ProviderSettingsPage(self.state), "Provider Settings")
        tabs.addTab(ReportExportVerifyPage(self.state), "Report Export / Verify")
        self.setCentralWidget(tabs)
