from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.conversation_analysis_page import ConversationAnalysisPage
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class RiskAnalysisScreen(QWidget):
    def __init__(self, legacy_state: dict, on_home, on_back) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(
            StepHeader(
                bi("Analyze a Conversation", "分析一段对话"),
                bi("Generate a local Risk Report.", "生成本地风险报告。"),
            )
        )
        nav = QHBoxLayout()
        home = SecondaryButton(bi("Home", "主页"))
        home.clicked.connect(on_home)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        nav.addWidget(home)
        nav.addWidget(back)
        layout.addLayout(nav)
        layout.addWidget(ConversationAnalysisPage(legacy_state))
