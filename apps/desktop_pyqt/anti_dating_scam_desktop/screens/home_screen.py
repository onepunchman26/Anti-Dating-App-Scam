from PySide6.QtWidgets import QVBoxLayout, QWidget

from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class HomeScreen(QWidget):
    """Minimal hub.

    Self-understanding first: the primary step is reflecting on your *own* data.
    Analyzing a conversation with someone else (scam/risk) is a secondary tool.
    Rule-based tools live behind "Offline tools".
    """

    def __init__(self, state, on_routes: dict[str, callable]) -> None:
        super().__init__()
        self.state = state
        self.on_routes = on_routes
        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 56, 64, 56)
        layout.setSpacing(16)
        layout.addWidget(
            StepHeader(
                bi("AI-SlowMatch", "AI-SlowMatch"),
                bi(
                    "Talk about how you relate. Start and end whenever you choose.",
                    "聊聊你在关系中的相处方式，随时开始，随时结束。",
                ),
            )
        )

        self.vault_status = StatusBanner()
        layout.addWidget(self.vault_status)

        self.connect_button = SecondaryButton(bi("Connect ChatGPT", "连接 ChatGPT"))
        self.connect_button.clicked.connect(on_routes["connect_ai"])
        layout.addWidget(self.connect_button)

        self.chat_button = PrimaryButton(bi("AI Chat", "AI 聊天"))
        self.chat_button.clicked.connect(on_routes["reflection_chat"])
        layout.addWidget(self.chat_button)

        portrait = SecondaryButton(bi("My reflections", "我的相处画像"))
        portrait.clicked.connect(on_routes["reflection_chat"])
        layout.addWidget(portrait)

        exchange = SecondaryButton(bi("Share or compare reflections", "分享或比对相处画像"))
        exchange.setObjectName("home_relationship_exchange")
        exchange.clicked.connect(on_routes.get("exchange", on_routes["advanced"]))
        layout.addWidget(exchange)

        tools = SecondaryButton(bi("More tools", "更多工具"))
        tools.clicked.connect(on_routes["advanced"])
        layout.addWidget(tools)

        layout.addStretch()

    def on_enter(self) -> None:
        vault = self.state.vault_path or bi("not selected", "未选择")
        backend_name = ai_backend.active_name()
        ai_line = (
            f"AI: {backend_name} ✓"
            if backend_name
            else bi("Connect ChatGPT to start chatting.", "连接 ChatGPT 后即可开始聊天。")
        )
        if backend_name:
            self.connect_button.setText(
                f"{bi('AI connection', 'AI 连接')}: {backend_name}"
            )
        else:
            self.connect_button.setText(bi("Connect ChatGPT", "连接 ChatGPT"))
        self.vault_status.set_text(
            f"{ai_line}\n"
            f"{bi('Local folder', '本地文件夹')}: {vault}"
        )
