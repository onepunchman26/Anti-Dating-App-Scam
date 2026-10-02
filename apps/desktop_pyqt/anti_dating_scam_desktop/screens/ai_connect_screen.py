from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam_desktop import ai_backend, ai_settings
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader
from anti_dating_scam_desktop.workers import run_async


class AIConnectScreen(QWidget):
    """Connect a local AI or an external provider with per-request disclosure review.

    Modes: Claude Code agent (isolated reviewed summary), Ollama (local, private
    default), Anthropic API (opt-in cloud; key kept in memory only), or Manual
    (the old copy-paste prompts, always available as fallback).
    """

    def __init__(self, state, profile_store, on_done, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        self.on_done = on_done

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(14)
        layout.addWidget(
            StepHeader(
                bi("Connect Your AI", "连接你的 AI"),
                bi(
                    "Connect once — after that, portraits, interviews, and reports run "
                    "with one click. No more copying prompts.",
                    "只需连接一次——之后画像、访谈和报告都可一键完成，不再需要复制提示词。",
                ),
            )
        )

        self.banner = StatusBanner(
            bi(
                'Easiest: press "Auto-Detect & Connect" — the app finds Claude Code, '
                "Ollama, or an API key by itself.",
                "最简单：点击「自动检测并连接」——应用会自行查找 Claude Code、Ollama 或 API 密钥。",
            )
        )
        layout.addWidget(self.banner)

        self.auto_button = PrimaryButton(bi("Auto-Detect & Connect", "自动检测并连接"))
        self.auto_button.clicked.connect(self._auto_detect)
        layout.addWidget(self.auto_button)

        form = QFormLayout()
        self.mode = QComboBox()
        self._modes = [
            (ai_settings.MODE_AGENT, bi("Claude Code (agent)", "Claude Code（代理）")),
            (ai_settings.MODE_OLLAMA, bi("Ollama (local, private)", "Ollama（本地·私密）")),
            (ai_settings.MODE_ANTHROPIC, bi("Anthropic API (cloud)", "Anthropic API（云端）")),
            (ai_settings.MODE_MANUAL, bi("Manual (copy prompts)", "手动（复制提示词）")),
        ]
        for _value, label in self._modes:
            self.mode.addItem(label)
        self.mode.currentIndexChanged.connect(self._mode_changed)
        form.addRow(bi("Mode", "模式"), self.mode)

        self.explain = QLabel()
        self.explain.setWordWrap(True)
        self.explain.setStyleSheet("color: #5b6172;")
        form.addRow("", self.explain)

        self.ollama_url = QLineEdit()
        self.ollama_model = QLineEdit()
        form.addRow(bi("Ollama URL", "Ollama 地址"), self.ollama_url)
        form.addRow(bi("Ollama model", "Ollama 模型"), self.ollama_model)

        self.anthropic_model = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText(
            bi(
                "Kept in memory only — never saved to disk. ANTHROPIC_API_KEY env "
                "var also works.",
                "仅保存在内存中——绝不写入磁盘。也可使用 ANTHROPIC_API_KEY 环境变量。",
            )
        )
        form.addRow(bi("Anthropic model", "Anthropic 模型"), self.anthropic_model)
        form.addRow(bi("API key", "API 密钥"), self.api_key)
        layout.addLayout(form)

        self.connect_button = SecondaryButton(
            bi("Connect & Test This Mode", "连接并测试所选模式")
        )
        self.connect_button.clicked.connect(self._connect)
        layout.addWidget(self.connect_button)

        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        layout.addWidget(back)
        layout.addStretch()

        self._load_settings()

    # ----------------------------------------------------------------- helpers
    def _load_settings(self) -> None:
        settings = ai_settings.load_settings()
        for index, (value, _label) in enumerate(self._modes):
            if value == settings.mode:
                self.mode.setCurrentIndex(index)
        self.ollama_url.setText(settings.ollama_url)
        self.ollama_model.setText(settings.ollama_model)
        self.anthropic_model.setText(settings.anthropic_model)
        self._mode_changed()

    def _current_mode(self) -> str:
        return self._modes[self.mode.currentIndex()][0]

    def _mode_changed(self) -> None:
        mode = self._current_mode()
        explanations = {
            ai_settings.MODE_AGENT: bi(
                "Uses your installed Claude Code CLI in an isolated workspace with tools disabled. "
                "Review a minimal summary before each request; "
                "the app validates and saves reports. "
                "Your provider may charge for use.",
                "使用已安装的 Claude Code，在禁用工具的隔离工作区运行。"
                "每次请求前审核最小摘要，由应用校验并保存报告；提供方可能收费。",
            ),
            ai_settings.MODE_OLLAMA: bi(
                "Runs a model through a loopback Ollama service on this device, with no cloud "
                "fallback. Ollama and a chat model must already be available.",
                "通过本机回环地址运行 Ollama 模型，不会回退至云端。"
                "需要 Ollama 服务及已安装的聊天模型。",
            ),
            ai_settings.MODE_ANTHROPIC: bi(
                "Cloud API: review and edit the exact disclosure for every task. "
                "The key stays in memory only; the provider may charge for use.",
                "云端 API：每次任务先审核并编辑实际披露内容。"
                "密钥只保存在内存中；提供方可能收费。",
            ),
            ai_settings.MODE_MANUAL: bi(
                "The classic flow: the app prepares prompts, you paste them into your "
                "agent yourself.",
                "经典流程：应用生成提示词，由你自己粘贴到代理中。",
            ),
        }
        self.explain.setText(explanations[mode])
        is_ollama = mode == ai_settings.MODE_OLLAMA
        is_anthropic = mode == ai_settings.MODE_ANTHROPIC
        for widget in (self.ollama_url, self.ollama_model):
            widget.setVisible(is_ollama)
        for widget in (self.anthropic_model, self.api_key):
            widget.setVisible(is_anthropic)

    def _build_backend(self):
        mode = self._current_mode()
        if mode == ai_settings.MODE_AGENT:
            return ai_backend.ClaudeAgentBackend(self.profile_store.base_dir)
        if mode == ai_settings.MODE_OLLAMA:
            return ai_backend.OllamaChatBackend(
                base_url=self.ollama_url.text().strip() or "http://localhost:11434",
                model=self.ollama_model.text().strip() or "llama3.2",
            )
        if mode == ai_settings.MODE_ANTHROPIC:
            return ai_backend.AnthropicChatBackend(
                api_key=self.api_key.text().strip(),
                model=self.anthropic_model.text().strip() or "claude-sonnet-5",
            )
        return None  # manual

    def _auto_detect(self) -> None:
        vault_dir = self.profile_store.base_dir
        self.auto_button.setEnabled(False)
        self.banner.set_text(
            bi(
                "Detecting the local Ollama service and installed models…",
                "正在检测本地 Ollama 服务及已安装模型……",
            )
        )

        def detect():
            return ai_backend.autodetect_backend(vault_dir)

        def done(result) -> None:
            backend, detail = result
            self.auto_button.setEnabled(True)
            if backend is not None:
                ai_backend.set_active(backend)
                self.banner.set_text(f"{bi('Connected', '已连接')}: {detail}")
                self._load_settings()
                self.on_done()
            else:
                self.banner.set_text(
                    f"{bi('Nothing usable found yet', '暂未找到可用后端')}:\n{detail}"
                )

        def err(message: str) -> None:
            self.auto_button.setEnabled(True)
            self.banner.set_text(f"{bi('Detection failed', '检测失败')}: {message}")

        run_async(self, detect, done, err)

    def _connect(self) -> None:
        mode = self._current_mode()
        settings = ai_settings.AISettings(
            mode=mode,
            ollama_url=self.ollama_url.text().strip() or "http://localhost:11434",
            ollama_model=self.ollama_model.text().strip() or "llama3.2",
            anthropic_model=self.anthropic_model.text().strip() or "claude-sonnet-5",
            chosen_by_user=True,
        )
        ai_settings.save_settings(settings)

        try:
            backend = self._build_backend()
        except ai_backend.BackendError as exc:
            self.banner.set_text(str(exc))
            return
        if backend is None:
            ai_backend.set_active(None)
            self.banner.set_text(
                bi(
                    "Manual mode selected. Prompt screens stay available.",
                    "已选择手动模式。提示词界面仍然可用。",
                )
            )
            self.on_done()
            return

        self.connect_button.setEnabled(False)
        self.banner.set_text(bi("Testing connection…", "正在测试连接……"))

        def check():
            return backend.check()

        def ok(result) -> None:
            available, detail = result
            self.connect_button.setEnabled(True)
            if available:
                ai_backend.set_active(backend)
                self.banner.set_text(
                    f"{bi('Connected', '已连接')}: {backend.name}\n{detail}"
                )
                self.on_done()
            else:
                ai_backend.set_active(None)
                self.banner.set_text(f"{bi('Not available', '不可用')}: {detail}")

        def err(message: str) -> None:
            self.connect_button.setEnabled(True)
            ai_backend.set_active(None)
            self.banner.set_text(f"{bi('Connection failed', '连接失败')}: {message}")

        run_async(self, check, ok, err)
