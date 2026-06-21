import json

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.engine.trust_ladder_engine import TrustLadderEngine


class TrustLadderPage(QWidget):
    STAGES = [
        "UNKNOWN_STRANGER",
        "LOW_PRESSURE_CHAT",
        "REPEATED_CONSISTENT_INTERACTION",
        "BOUNDARY_RESPECT_VERIFIED",
        "SAFETY_CHECKED_OFFLINE_MEETING",
        "DEEPER_RELATIONSHIP_EXPLORATION",
    ]

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.engine = TrustLadderEngine()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Trust Ladder</h2>"))
        layout.addWidget(QLabel("Current stage"))
        self.stage = QComboBox()
        self.stage.addItems(self.STAGES)
        layout.addWidget(self.stage)

        layout.addWidget(QLabel("Recent events"))
        self.events = QTextEdit()
        layout.addWidget(self.events)

        layout.addWidget(QLabel("Boundary concerns"))
        self.boundaries = QTextEdit()
        self.boundaries.setMaximumHeight(110)
        layout.addWidget(self.boundaries)

        self.money_or_sensitive = QCheckBox(
            "Money, private images, or sensitive data was requested"
        )
        self.identity_verified = QCheckBox(
            "Identity was verified through safe, consent-based methods"
        )
        layout.addWidget(self.money_or_sensitive)
        layout.addWidget(self.identity_verified)

        evaluate = QPushButton("Evaluate")
        evaluate.clicked.connect(self._evaluate)
        layout.addWidget(evaluate)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _evaluate(self) -> None:
        if not self.state.get("consent_confirmed"):
            QMessageBox.warning(
                self,
                "Consent required",
                "Please confirm consent on the Consent / Safety tab before evaluation.",
            )
            return
        result = self.engine.evaluate(
            current_stage=self.stage.currentText(),
            recent_events=self.events.toPlainText(),
            boundary_concerns=self.boundaries.toPlainText(),
            money_or_sensitive_requested=self.money_or_sensitive.isChecked(),
            identity_verified=self.identity_verified.isChecked(),
            consent_confirmed=True,
        )
        self.output.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))
