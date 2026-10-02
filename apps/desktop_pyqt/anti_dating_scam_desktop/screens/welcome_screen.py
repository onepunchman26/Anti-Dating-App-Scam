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
                    "A relationship copilot. Talk about your needs, boundaries and "
                    "ways of relating, then review your private reflection.",
                    "你的恋爱军师。聊聊需要、边界与相处方式，再查看你的私密相处画像。",
                ),
            )
        )
        button = PrimaryButton(bi("Get Started", "开始使用"))
        button.clicked.connect(on_next)
        layout.addWidget(button)
        layout.addStretch()
