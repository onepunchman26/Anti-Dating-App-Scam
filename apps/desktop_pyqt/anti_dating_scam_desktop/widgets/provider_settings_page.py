from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.providers.registry import provider_names


class ProviderSettingsPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Provider Settings</h2>"))
        note = QLabel(
            "Provider settings are placeholders in this MVP. No API keys are required "
            "for the mock local demo. API keys are stored locally only; do not commit secrets."
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
        self.api_key.setPlaceholderText("Optional future provider key; not used by mock demo.")
        form.addRow("Provider", self.provider)
        form.addRow("Model name", self.model)
        form.addRow("API key", self.api_key)
        layout.addLayout(form)
        layout.addStretch()

    def _sync(self) -> None:
        self.state["provider_name"] = self.provider.currentText()
        self.state["model_name"] = self.model.text().strip() or "local-rule-based-mvp"
