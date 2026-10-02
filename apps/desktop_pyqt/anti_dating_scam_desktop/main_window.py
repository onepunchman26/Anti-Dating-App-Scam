from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam_desktop.app_state import AppState
from anti_dating_scam_desktop.i18n import bi, other_language_label, toggle_language
from anti_dating_scam_desktop.navigation import Navigator
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens.advanced_tools_screen import AdvancedToolsScreen
from anti_dating_scam_desktop.screens.ai_connect_screen import AIConnectScreen
from anti_dating_scam_desktop.screens.assisted_browser_export_screen import (
    AssistedBrowserExportScreen,
)
from anti_dating_scam_desktop.screens.beacon_exchange_screen import BeaconExchangeScreen
from anti_dating_scam_desktop.screens.chatgpt_connect_screen import ChatGPTConnectScreen
from anti_dating_scam_desktop.screens.criteria_interview_screen import CriteriaInterviewScreen
from anti_dating_scam_desktop.screens.criteria_viewer_screen import CriteriaViewerScreen
from anti_dating_scam_desktop.screens.home_screen import HomeScreen
from anti_dating_scam_desktop.screens.import_data_screen import ImportDataScreen
from anti_dating_scam_desktop.screens.interview_chat_screen import InterviewChatScreen
from anti_dating_scam_desktop.screens.policy_consent_screen import PolicyConsentScreen
from anti_dating_scam_desktop.screens.profile_detection_screen import ProfileDetectionScreen
from anti_dating_scam_desktop.screens.profile_generation_screen import ProfileGenerationScreen
from anti_dating_scam_desktop.screens.profile_viewer_screen import ProfileViewerScreen
from anti_dating_scam_desktop.screens.provider_settings_screen import ProviderSettingsScreen
from anti_dating_scam_desktop.screens.reflection_chat_screen import (
    ReflectionChatScreen,
    ReflectionChatState,
)
from anti_dating_scam_desktop.screens.relationship_exchange_screen import (
    RelationshipExchangeScreen,
    RelationshipExchangeState,
)
from anti_dating_scam_desktop.screens.report_export_verify_screen import (
    ReportExportVerifyScreen,
)
from anti_dating_scam_desktop.screens.risk_analysis_screen import RiskAnalysisScreen
from anti_dating_scam_desktop.screens.self_portrait_screen import SelfPortraitScreen
from anti_dating_scam_desktop.screens.self_portrait_viewer_screen import (
    SelfPortraitViewerScreen,
)
from anti_dating_scam_desktop.screens.trust_ladder_screen import TrustLadderScreen
from anti_dating_scam_desktop.screens.welcome_screen import WelcomeScreen
from anti_dating_scam_desktop.style import APP_STYLESHEET
from anti_dating_scam_desktop.workers import has_pending_workers


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(APP_STYLESHEET)
        self.app_state = AppState()
        # Preserve the old tools' mode independently of the new conversation path.
        self.app_state.analysis_mode = "agent"
        self.profile_store = ProfileStore()
        self.app_state.profile_exists = self.profile_store.detect_existing_profile()
        self.app_state.vault_path = self.profile_store.base_dir
        self.app_state.profile_path = self.profile_store.markdown_path
        self.app_state.profile_json_path = self.profile_store.json_path
        self.legacy_state = self.app_state.as_legacy_dict()
        self.reflection_state = ReflectionChatState()
        self.exchange_state = RelationshipExchangeState()

        self._current_screen = "welcome"
        self._pending_language_change = False
        self._close_when_idle = False
        self._lifecycle_timer = QTimer(self)
        self._lifecycle_timer.setInterval(50)
        self._lifecycle_timer.timeout.connect(self._finish_pending_lifecycle)
        self._build()

    # --------------------------------------------------------------- UI shell
    def _build(self) -> None:
        """(Re)build the window shell. Called again when the language changes."""
        history = list(self.navigator._history) if hasattr(self, "navigator") else []
        # Drop the previous shell (and all its screens) so a language rebuild
        # never leaves stale, duplicated widgets or signal connections behind.
        old = self.takeCentralWidget()
        if old is not None:
            old.deleteLater()

        self.setWindowTitle(bi("AI-SlowMatch - Relationship Copilot", "AI-SlowMatch —— 恋爱军师"))
        stack = QStackedWidget()
        self.navigator = Navigator(stack)
        self._add_screens()

        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._make_header())
        outer.addWidget(stack, 1)
        self.setCentralWidget(container)

        target = self._current_screen
        if target not in self.navigator._screens:
            target = "welcome"
        self.navigator._history = [name for name in history if name in self.navigator._screens]
        self.navigator.go(target, remember=False)

    def _make_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("AppHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(24, 12, 20, 12)
        row.setSpacing(10)

        title = QLabel("AI-SlowMatch")
        title.setObjectName("AppHeaderTitle")
        row.addWidget(title)
        tagline = QLabel(bi("Your pace · Your choice", "你的节奏 · 自主选择"))
        tagline.setObjectName("AppHeaderHint")
        row.addWidget(tagline)
        row.addStretch()

        about = QPushButton(bi("About", "关于"))
        about.setObjectName("AboutButton")
        about.clicked.connect(self._about)
        row.addWidget(about)

        lang_label = QLabel(bi("Language", "语言"))
        lang_label.setObjectName("AppHeaderHint")
        row.addWidget(lang_label)
        lang_button = QPushButton(other_language_label())
        lang_button.setObjectName("LanguageButton")
        lang_button.setCursor(Qt.CursorShape.PointingHandCursor)
        lang_button.clicked.connect(self._toggle_language)
        row.addWidget(lang_button)
        return header

    def _about(self) -> None:
        from anti_dating_scam.version import build_info

        info = build_info()
        from importlib.resources import files

        notice = QMessageBox(self)
        notice.setWindowTitle(bi("About AI-SlowMatch", "关于 AI-SlowMatch"))
        notice.setText(
            "\n".join(
                [
                    "AI-SlowMatch " + info["version"],
                    bi("Build: ", "构建：") + info.get("build_id", "source"),
                    bi("Source: ", "源码：") + info.get("git_commit", "")[:12],
                    bi("Development build", "开发版本")
                    if info.get("dirty")
                    else bi("Committed source build", "已提交源码构建"),
                    bi(
                        "Private reflection, not a diagnosis or compatibility verdict.",
                        "私人相处理解，不是诊断或兼容性判决。",
                    ),
                    bi(
                        "Coaching ideas adapted from goutoujunshi (MIT). "
                        "Details include the license.",
                        "部分军师理念改编自 goutoujunshi（MIT），许可全文见详情。",
                    ),
                ]
            )
        )
        notice.setDetailedText(
            "\n\n".join(
                files("anti_dating_scam").joinpath("licenses", name).read_text(encoding="utf-8")
                for name in ("goutoujunshi-MIT.txt", "goutoujunshi-MIT-zh.txt")
            )
        )
        notice.exec()

    def _toggle_language(self) -> None:
        if has_pending_workers(self):
            self._pending_language_change = True
            self._defer_lifecycle()
            return
        self._current_screen = self.navigator.current_name or "welcome"
        toggle_language()
        self._build()

    def _defer_lifecycle(self) -> None:
        self.statusBar().showMessage(
            bi(
                "Finishing the current task before closing or changing language. "
                "You can keep using "
                "the window while it finishes.",
                "当前任务完成后将关闭窗口或切换语言；等待期间窗口仍可操作。",
            )
        )
        self._lifecycle_timer.start()

    def _finish_pending_lifecycle(self) -> None:
        if has_pending_workers(self):
            return
        self._lifecycle_timer.stop()
        self.statusBar().clearMessage()
        if self._close_when_idle:
            self._close_when_idle = False
            self._pending_language_change = False
            self.close()
        elif self._pending_language_change:
            self._pending_language_change = False
            self._toggle_language()

    def closeEvent(self, event) -> None:
        if has_pending_workers(self):
            self._close_when_idle = True
            self._defer_lifecycle()
            event.ignore()
            return
        super().closeEvent(event)

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
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "import_data",
            ImportDataScreen(
                self.app_state,
                self.navigator.bind("self_portrait"),
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
                    "connect_ai": self.navigator.bind("ai_connect"),
                    "reflection_chat": self.navigator.bind("reflection_chat"),
                    "exchange": self.navigator.bind("relationship_exchange"),
                    "understand": self.navigator.bind("self_portrait"),
                    "add_data": self.navigator.bind("import_data"),
                    "self_portrait_view": self.navigator.bind("self_portrait_viewer"),
                    "criteria": self.navigator.bind("criteria_interview"),
                    "risk": self._go_risk,
                    "beacon": self.navigator.bind("beacon_exchange"),
                    "settings": self._go_settings,
                    "advanced": self.navigator.bind("advanced_tools"),
                },
            ),
        )
        self.navigator.add(
            "beacon_exchange",
            BeaconExchangeScreen(
                self.app_state,
                self.profile_store,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "ai_connect",
            ChatGPTConnectScreen(
                self.app_state,
                self.profile_store,
                self.navigator.bind("reflection_chat"),
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "advanced_ai_connect",
            AIConnectScreen(self.app_state, self.profile_store, self._go_home, self.navigator.back),
        )
        self.navigator.add(
            "reflection_chat",
            ReflectionChatScreen(
                self.app_state,
                self.profile_store,
                self.reflection_state,
                self.navigator.bind("ai_connect"),
                self.navigator.back,
                self.navigator.bind("relationship_exchange"),
            ),
        )
        self.navigator.add(
            "relationship_exchange",
            RelationshipExchangeScreen(
                self.app_state,
                self.profile_store,
                self.exchange_state,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "interview_chat",
            InterviewChatScreen(
                self.app_state,
                self.profile_store,
                self.navigator.bind("criteria_viewer"),
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "self_portrait",
            SelfPortraitScreen(
                self.app_state,
                self.profile_store,
                self.navigator.bind("self_portrait_viewer"),
                self.navigator.bind("import_data"),
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "self_portrait_viewer",
            SelfPortraitViewerScreen(
                self.app_state,
                self.profile_store,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "criteria_interview",
            CriteriaInterviewScreen(
                self.app_state,
                self.profile_store,
                self.navigator.bind("criteria_viewer"),
                self.navigator.bind("interview_chat"),
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "criteria_viewer",
            CriteriaViewerScreen(
                self.app_state,
                self.profile_store,
                self.navigator.back,
            ),
        )
        self.navigator.add(
            "advanced_tools",
            AdvancedToolsScreen(
                self.app_state,
                {
                    "risk": self._go_risk,
                    "trust": self._go_trust,
                    "profile": self._go_profile_viewer,
                    "profile_gen": self.navigator.bind("profile_generation"),
                    "report": self._go_report,
                    "browser": self._go_assisted_browser_export,
                    "add_data": self.navigator.bind("import_data"),
                    "portrait": self.navigator.bind("self_portrait"),
                    "portrait_view": self.navigator.bind("self_portrait_viewer"),
                    "criteria": self.navigator.bind("criteria_interview"),
                    "beacon": self.navigator.bind("beacon_exchange"),
                    "providers": self.navigator.bind("advanced_ai_connect"),
                },
                self._go_home,
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
        # Native screens own AppState directly. Pulling an old dict snapshot after
        # a vault switch can revive the previous vault's cleared JSON companion.
        if self.navigator.current_name in {
            "risk",
            "trust",
            "report",
            "settings",
            "assisted_browser_export",
        }:
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
