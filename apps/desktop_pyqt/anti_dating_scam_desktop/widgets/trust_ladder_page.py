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
from anti_dating_scam_desktop.i18n import bi


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
        layout.addWidget(QLabel(f"<h2>{bi('Trust Ladder', '信任阶梯')}</h2>"))
        layout.addWidget(QLabel(bi("Current stage", "当前阶段")))
        self.stage = QComboBox()
        self.stage.addItems(self.STAGES)
        layout.addWidget(self.stage)

        layout.addWidget(QLabel(bi("Recent events", "近期事件")))
        self.events = QTextEdit()
        layout.addWidget(self.events)

        layout.addWidget(QLabel(bi("Boundary concerns", "边界相关顾虑")))
        self.boundaries = QTextEdit()
        self.boundaries.setMaximumHeight(110)
        layout.addWidget(self.boundaries)

        self.money_or_sensitive = QCheckBox(
            bi(
                "Money, private images, or sensitive data was requested",
                "对方要求过金钱、私密照片或其他敏感数据",
            )
        )
        self.identity_verified = QCheckBox(
            bi(
                "Identity was verified through safe, consent-based methods",
                "已通过安全、双方同意的方式核实过身份",
            )
        )
        layout.addWidget(self.money_or_sensitive)
        layout.addWidget(self.identity_verified)

        evaluate = QPushButton(bi("Evaluate", "评估"))
        evaluate.clicked.connect(self._evaluate)
        layout.addWidget(evaluate)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def _evaluate(self) -> None:
        if not self.state.get("consent_confirmed"):
            QMessageBox.warning(
                self,
                bi("Consent required", "需要先确认同意"),
                bi(
                    "Please confirm consent on the Consent / Safety tab before evaluation.",
                    "请先在「同意与安全」页确认同意，再进行评估。",
                ),
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
