from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.app_card import AppCard
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class AnalysisModeScreen(QWidget):
    def __init__(self, state, profile_store, on_next, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                bi("Choose Analysis Mode", "选择分析模式"),
                bi(
                    "Pick how this prototype should process local exported documents.",
                    "选择该原型如何处理本地导出的文档。",
                ),
            )
        )
        cards = QHBoxLayout()
        cards.addWidget(
            AppCard(
                bi("Agent Mode", "代理模式"),
                bi(
                    "Connect a desktop agent (Claude Code / Cowork). The app sets up your "
                    "vault as a shared workspace and writes an AGENTS.md / CLAUDE.md guide, "
                    "so your agent can open the folder and help. You control what is shared.",
                    "连接桌面代理（Claude Code / Cowork）。应用会把您的档案库设置为共享工作区，"
                    "并写入 AGENTS.md / CLAUDE.md 说明文件，让代理可以打开该文件夹来协助您。"
                    "分享哪些内容由您掌控。",
                ),
                bi("Use Agent Mode", "使用代理模式"),
                lambda: self._select("agent", on_next),
                status=bi("Recommended for current prototype.", "当前原型推荐使用。"),
            )
        )
        cards.addWidget(
            AppCard(
                bi("API Mode", "API 模式"),
                bi(
                    "Connect your own AI provider API key directly in the app. Future mode "
                    "for OpenAI, Anthropic, Gemini, Ollama, or local models.",
                    "在应用内直接连接您自己的 AI 提供方 API 密钥。"
                    "未来支持 OpenAI、Anthropic、Gemini、Ollama 或本地模型。",
                ),
                bi("Configure API Mode", "配置 API 模式"),
                lambda: self._select_api(on_next),
                status=bi("Coming soon / placeholder.", "即将推出 / 占位功能。"),
            )
        )
        layout.addLayout(cards)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        layout.addWidget(back)

    def _select(self, mode: str, on_next) -> None:
        self.state.analysis_mode = mode
        if mode == "agent":
            # "Connect" the agent: make sure the vault exists and carries the
            # instruction file a desktop agent (Claude Code / Cowork) can read.
            self.profile_store.create_default_directories()
            self.profile_store.write_agent_instructions()
            if self.state.vault_path is None:
                self.state.vault_path = self.profile_store.base_dir
            QMessageBox.information(
                self,
                bi("Agent workspace ready", "代理工作区已就绪"),
                f"{bi('Vault folder', '档案库文件夹')}:\n{self.profile_store.base_dir}\n\n"
                + bi(
                    "An AGENTS.md / CLAUDE.md guide was written here. Open this folder in "
                    "Claude Code or Cowork to let your agent help with the profile.",
                    "已在此处写入 AGENTS.md / CLAUDE.md 说明文件。在 Claude Code 或 Cowork 中"
                    "打开此文件夹，即可让代理协助处理档案。",
                ),
            )
        on_next()

    def _select_api(self, on_next) -> None:
        QMessageBox.information(
            self,
            bi("API Mode placeholder", "API 模式占位提示"),
            bi(
                "API Mode is not fully implemented. No real API call will be made unless "
                "provider code is explicitly configured.",
                "API 模式尚未完全实现。除非显式配置了提供方代码，否则不会发起真实的 API 调用。",
            ),
        )
        self._select("api", on_next)
