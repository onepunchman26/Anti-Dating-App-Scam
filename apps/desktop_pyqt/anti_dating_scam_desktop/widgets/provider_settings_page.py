from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.providers.registry import provider_names
from anti_dating_scam_desktop.i18n import bi


class ProviderSettingsPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{bi('Provider Settings', '提供方设置')}</h2>"))
        note = QLabel(
            bi(
                "Provider settings are placeholders in this MVP. No API keys are required "
                "for the mock local demo. API keys are stored locally only; do not commit secrets.",
                "本 MVP 中的提供方设置仅为占位功能。模拟本地演示不需要任何 API 密钥。"
                "API 密钥仅保存在本地，请勿提交到代码仓库。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        form = QFormLayout()
        self.provider = QComboBox()
        self.provider.addItems(provider_names())
        self.provider.currentTextChanged.connect(self._sync)
        self.model = QLineEdit("local-rule-based-mvp")
        self.model.textChanged.connect(self._sync)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText(
            bi(
                "Optional future provider key; not used by mock demo.",
                "未来可选的提供方密钥；模拟演示不使用此项。",
            )
        )
        form.addRow(bi("Provider", "提供方"), self.provider)
        form.addRow(bi("Model name", "模型名称"), self.model)
        form.addRow(bi("API key", "API 密钥"), self.api_key)
        layout.addLayout(form)
        layout.addStretch()

    def _sync(self) -> None:
        self.state["provider_name"] = self.provider.currentText()
        self.state["model_name"] = self.model.text().strip() or "local-rule-based-mvp"
