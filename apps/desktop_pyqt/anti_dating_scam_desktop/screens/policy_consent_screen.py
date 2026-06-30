from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class PolicyConsentScreen(QWidget):
    def __init__(self, state, on_next, on_back) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                bi("Safety & Consent", "安全与同意"),
                bi("Policy first, before import or analysis.", "先了解政策，再导入或分析。"),
            )
        )
        content = QLabel(
            "<ul>"
            "<li>"
            + bi(
                "This app analyzes only data you choose to provide.",
                "本应用仅分析您主动提供的数据。",
            )
            + "</li>"
            "<li>"
            + bi(
                "Import only your own data, or data you have permission to use.",
                "只导入您自己的数据，或您已获得使用许可的数据。",
            )
            + "</li>"
            "<li>"
            + bi(
                "The app does not judge whether a real person is good or bad.",
                "本应用不会评判某个真实的人是好是坏。",
            )
            + "</li>"
            "<li>"
            + bi(
                "The app does not make legal, criminal, psychological, or medical "
                "determinations.",
                "本应用不会做出法律、刑事、心理或医学方面的判定。",
            )
            + "</li>"
            "<li>"
            + bi("Risk analysis is only decision support.", "风险分析仅作为决策参考，不是结论。")
            + "</li>"
            "<li>"
            + bi(
                "Do not use this app for stalking, doxxing, harassment, revenge, "
                "blackmail, or public shaming.",
                "请勿将本应用用于跟踪、起底（doxxing）、骚扰、报复、勒索或公开羞辱他人。",
            )
            + "</li>"
            "<li>"
            + bi("Your local profile is stored on your computer.", "您的本地档案保存在您自己的电脑上。")
            + "</li>"
            "</ul>"
        )
        content.setWordWrap(True)
        layout.addWidget(content)
        self.checkbox = QCheckBox(
            bi(
                "I understand and agree to use this app for self-protection and "
                "self-reflection only.",
                "我理解并同意，仅将本应用用于自我保护与自我反思。",
            )
        )
        layout.addWidget(self.checkbox)
        self.next_button = PrimaryButton(bi("Next", "下一步"))
        self.next_button.setEnabled(False)
        self.checkbox.stateChanged.connect(self._toggle_next)
        self.next_button.clicked.connect(lambda: self._accept(on_next))
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        layout.addWidget(self.next_button)
        layout.addWidget(back)
        layout.addStretch()

    def _toggle_next(self) -> None:
        self.next_button.setEnabled(self.checkbox.isChecked())

    def _accept(self, on_next) -> None:
        self.state.consent_accepted = True
        on_next()
