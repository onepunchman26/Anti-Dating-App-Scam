import json

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from anti_dating_scam.engine.report_generator import ReportGenerator
from anti_dating_scam.engine.scam_risk_analyzer import ScamRiskAnalyzer
from anti_dating_scam_desktop.i18n import bi


class ConversationAnalysisPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.analyzer = ScamRiskAnalyzer()
        self.report_generator = ReportGenerator()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{bi('Conversation Risk Analysis', '对话风险分析')}</h2>"))
        note = QLabel(
            bi(
                "Paste conversation text you are allowed to analyze. Outputs are "
                "uncertainty-aware risk signals, not accusations.",
                "粘贴您有权分析的对话文本。输出的是带有不确定性说明的风险信号，而非指控。",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addWidget(QLabel(bi("Conversation text", "对话文本")))
        self.conversation = QTextEdit()
        layout.addWidget(self.conversation)

        layout.addWidget(QLabel(bi("Optional user notes", "可选的用户备注")))
        self.user_notes = QTextEdit()
        self.user_notes.setMaximumHeight(110)
        layout.addWidget(self.user_notes)

        analyze = QPushButton(bi("Analyze", "分析"))
        analyze.clicked.connect(self._analyze)
        layout.addWidget(analyze)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _analyze(self) -> None:
        if not self.state.get("consent_confirmed"):
            QMessageBox.warning(
                self,
                bi("Consent required", "需要先确认同意"),
                bi(
                    "Please confirm consent on the Consent / Safety tab before analysis.",
                    "请先在「同意与安全」页确认同意，再进行分析。",
                ),
            )
            return
        conversation_text = self.conversation.toPlainText().strip()
        if not conversation_text:
            QMessageBox.information(
                self,
                bi("No text", "没有文本"),
                bi("Paste conversation text before analysis.", "请先粘贴对话文本再进行分析。"),
            )
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
