from PySide6.QtWidgets import QMainWindow, QStackedWidget

from anti_dating_scam_desktop.app_state import AppState
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.navigation import Navigator
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens.analysis_mode_screen import AnalysisModeScreen
from anti_dating_scam_desktop.screens.assisted_browser_export_screen import (
    AssistedBrowserExportScreen,
)
from anti_dating_scam_desktop.screens.home_screen import HomeScreen
from anti_dating_scam_desktop.screens.import_data_screen import ImportDataScreen
from anti_dating_scam_desktop.screens.policy_consent_screen import PolicyConsentScreen
from anti_dating_scam_desktop.screens.profile_detection_screen import ProfileDetectionScreen
from anti_dating_scam_desktop.screens.profile_generation_screen import ProfileGenerationScreen
from anti_dating_scam_desktop.screens.profile_viewer_screen import ProfileViewerScreen
from anti_dating_scam_desktop.screens.provider_settings_screen import ProviderSettingsScreen
from anti_dating_scam_desktop.screens.report_export_verify_screen import (
    ReportExportVerifyScreen,
)
from anti_dating_scam_desktop.screens.risk_analysis_screen import RiskAnalysisScreen
from anti_dating_scam_desktop.screens.trust_ladder_screen import TrustLadderScreen
from anti_dating_scam_desktop.screens.welcome_screen import WelcomeScreen
from anti_dating_scam_desktop.style import APP_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(bi("AI-SlowMatch - Local Trust Tool", "AI-SlowMatch —— 本地信任工具"))
        self.setStyleSheet(APP_STYLESHEET)
        self.app_state = AppState()
        self.profile_store = ProfileStore()
        self.app_state.profile_exists = self.profile_store.detect_existing_profile()
        self.app_state.profile_path = self.profile_store.markdown_path
        self.app_state.profile_json_path = self.profile_store.json_path
        self.legacy_state = self.app_state.as_legacy_dict()

        stack = QStackedWidget()
        self.navigator = Navigator(stack)
        self._add_screens()
        self.setCentralWidget(stack)
        self.navigator.go("welcome", remember=False)

    def _add_screens(self) -> None:
        self.navigator.add("welcome", WelcomeScreen(self.navigator.bind("policy")))
        self.navigator.add(
            "policy",
            PolicyConsentScreen(
                self.app_state,
                self._after_policy,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "profile_detection",
            ProfileDetectionScreen(
                self.app_state,
                self.profile_store,
                self._go_home,
                self.navigator.bind("import_data"),
                self.navigator.bind("analysis_mode"),
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "analysis_mode",
            AnalysisModeScreen(
                self.app_state,
                self.profile_store,
                self.navigator.bind("import_data"),
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "import_data",
            ImportDataScreen(
                self.app_state,
                self.navigator.bind("profile_generation"),
                self._go_assisted_browser_export,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "profile_generation",
            ProfileGenerationScreen(
                self.app_state,
                self.profile_store,
                self._go_home,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "home",
            HomeScreen(
                self.app_state,
                {
                    "risk": self._go_risk,
                    "trust": self._go_trust,
                    "profile": self._go_profile_viewer,
                    "report": self._go_report,
                    "import": self.navigator.bind("analysis_mode"),
                    "settings": self._go_settings,
                    "browser": self._go_assisted_browser_export,
                },
            ),
        )
        self.navigator.add(
            "risk",
            RiskAnalysisScreen(self.legacy_state, self._go_home, self.navigator.back),
        )
        self.navigator.add(
            "trust",
            TrustLadderScreen(self.legacy_state, self._go_home, self.navigator.back),
        )
        self.navigator.add(
            "profile_viewer",
            ProfileViewerScreen(
                self.app_state,
                self.profile_store,
                self._go_home,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "report",
            ReportExportVerifyScreen(self.legacy_state, self._go_home, self.navigator.back),
        )
        self.navigator.add(
            "settings",
            ProviderSettingsScreen(self.legacy_state, self._go_home, self.navigator.back),
        )
        self.navigator.add(
            "assisted_browser_export",
            AssistedBrowserExportScreen(
                self.legacy_state,
                self._go_home,
                self.navigator.back,
            ),
        )

    def _after_policy(self) -> None:
        self.legacy_state["consent_confirmed"] = self.app_state.consent_accepted
        self.navigator.go("profile_detection")

    def _sync_legacy_from_app_state(self) -> None:
        self.legacy_state["consent_confirmed"] = self.app_state.consent_accepted
        self.legacy_state["manual_notes"] = self.app_state.manual_notes
        self.legacy_state["memory_summary"] = self.app_state.memory_summary
        self.legacy_state["chatgpt_export_summary"] = self.app_state.chatgpt_export_summary
        self.legacy_state["profile"] = self.app_state.current_profile_json
        self.legacy_state["provider_name"] = self.app_state.provider_name
        self.legacy_state["model_name"] = self.app_state.model_name

    def _sync_app_state_from_legacy(self) -> None:
        self.app_state.sync_from_legacy_dict(self.legacy_state)

    def _go_home(self) -> None:
        self._sync_app_state_from_legacy()
        self.navigator.go("home")

    def _go_risk(self) -> None:
        self._sync_legacy_from_app_state()
        self.navigator.go("risk")

    def _go_trust(self) -> None:
        self._sync_legacy_from_app_state()
        self.navigator.go("trust")

    def _go_profile_viewer(self) -> None:
        self._sync_app_state_from_legacy()
        self.navigator.go("profile_viewer")

    def _go_report(self) -> None:
        self._sync_legacy_from_app_state()
        self.navigator.go("report")

    def _go_settings(self) -> None:
        self._sync_legacy_from_app_state()
        self.navigator.go("settings")

    def _go_assisted_browser_export(self) -> None:
        self._sync_legacy_from_app_state()
        self.navigator.go("assisted_browser_export")
