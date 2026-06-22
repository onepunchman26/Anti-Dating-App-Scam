from PySide6.QtWidgets import QVBoxLayout, QWidget

from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class WelcomeScreen(QWidget):
    def __init__(self, on_next) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                "AI-SlowMatch",
                "Local relationship trust and anti-scam assistant. Build a local profile, "
                "review risk signals, and move through trust slowly.",
            )
        )
        button = PrimaryButton("Get Started")
        button.clicked.connect(on_next)
        layout.addWidget(button)
        layout.addStretch()
