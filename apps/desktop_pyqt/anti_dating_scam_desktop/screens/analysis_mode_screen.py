from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QVBoxLayout, QWidget

from anti_dating_scam_desktop.widgets.app_card import AppCard
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class AnalysisModeScreen(QWidget):
    def __init__(self, state, on_next, on_back) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                "Choose Analysis Mode",
                "Pick how this prototype should process local exported documents.",
            )
        )
        cards = QHBoxLayout()
        cards.addWidget(
            AppCard(
                "Agent Mode",
                "Use an external coding/AI agent workflow, such as Codex-style assisted "
                "analysis, to help process your local exported documents. You manually "
                "control what files are shared.",
                "Use Agent Mode",
                lambda: self._select("agent", on_next),
                status="Recommended for current prototype.",
            )
        )
        cards.addWidget(
            AppCard(
                "API Mode",
                "Connect your own AI provider API key directly in the app. Future mode "
                "for OpenAI, Anthropic, Gemini, Ollama, or local models.",
                "Configure API Mode",
                lambda: self._select_api(on_next),
                status="Coming soon / placeholder.",
            )
        )
        layout.addLayout(cards)
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        layout.addWidget(back)

    def _select(self, mode: str, on_next) -> None:
        self.state.analysis_mode = mode
        on_next()

    def _select_api(self, on_next) -> None:
        QMessageBox.information(
            self,
            "API Mode placeholder",
            "API Mode is not fully implemented. No real API call will be made unless "
            "provider code is explicitly configured.",
        )
        self._select("api", on_next)
