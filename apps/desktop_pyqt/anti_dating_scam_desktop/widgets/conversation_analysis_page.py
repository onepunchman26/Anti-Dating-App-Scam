import json

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from anti_dating_scam.engine.report_generator import ReportGenerator
from anti_dating_scam.engine.scam_risk_analyzer import ScamRiskAnalyzer


class ConversationAnalysisPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.analyzer = ScamRiskAnalyzer()
        self.report_generator = ReportGenerator()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Conversation Risk Analysis</h2>"))
        note = QLabel(
            "Paste conversation text you are allowed to analyze. Outputs are "
            "uncertainty-aware risk signals, not accusations."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addWidget(QLabel("Conversation text"))
        self.conversation = QTextEdit()
        layout.addWidget(self.conversation)

        layout.addWidget(QLabel("Optional user notes"))
        self.user_notes = QTextEdit()
        self.user_notes.setMaximumHeight(110)
        layout.addWidget(self.user_notes)

        analyze = QPushButton("Analyze")
        analyze.clicked.connect(self._analyze)
        layout.addWidget(analyze)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _analyze(self) -> None:
        if not self.state.get("consent_confirmed"):
            QMessageBox.warning(
                self,
                "Consent required",
                "Please confirm consent on the Consent / Safety tab before analysis.",
            )
            return
        conversation_text = self.conversation.toPlainText().strip()
        if not conversation_text:
            QMessageBox.information(self, "No text", "Paste conversation text before analysis.")
            return
        analysis = self.analyzer.analyze(
            conversation_text,
            user_notes=self.user_notes.toPlainText(),
            consent_confirmed=True,
        )
        report = self.report_generator.generate_risk_report(
            conversation_text=conversation_text,
            risk_analysis=analysis,
            provider_name=self.state.get("provider_name", "Mock"),
            model_name=self.state.get("model_name", "local-rule-based-mvp"),
        )
        self.state["risk_report"] = report
        self.output.setPlainText(json.dumps(report, indent=2, ensure_ascii=False))
