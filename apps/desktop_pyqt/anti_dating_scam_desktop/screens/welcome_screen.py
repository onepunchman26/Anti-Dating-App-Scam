from PySide6.QtWidgets import QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class WelcomeScreen(QWidget):
    def __init__(self, on_next) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                bi("AI-SlowMatch", "AI-SlowMatch"),
                bi(
                    "Local relationship trust and anti-scam assistant. Build a local "
                    "profile, review risk signals, and move through trust slowly.",
                    "本地关系信任与反诈骗助手。建立本地档案、查看风险信号，并按节奏慢慢建立信任。",
                ),
            )
        )
        button = PrimaryButton(bi("Get Started", "开始使用"))
        button.clicked.connect(on_next)
        layout.addWidget(button)
        layout.addStretch()
