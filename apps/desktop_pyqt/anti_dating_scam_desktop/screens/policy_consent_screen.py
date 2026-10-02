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
                bi(
                    "You control what you share and when to stop.",
                    "分享什么、何时结束，都由你决定。",
                ),
            )
        )
        content = QLabel(
            "<ul>"
            "<li>"
            + bi(
                "ChatGPT receives only the conversation you review and choose to send. "
                "You may skip questions or end at any time.",
                "ChatGPT 只接收你审核并选择发送的对话。你可以跳过问题或随时结束。",
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
            + bi(
                "Saved reflections stay in ordinary, unencrypted files on your computer. "
                "A cloud-sync folder may upload them.",
                "已保存画像以普通、未加密文件保存在你的电脑上；云同步文件夹可能上传这些文件。",
            )
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
