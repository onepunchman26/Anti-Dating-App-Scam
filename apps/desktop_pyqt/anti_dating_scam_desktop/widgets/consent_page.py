from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi


class ConsentPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{bi('Consent / Safety', '同意与安全')}</h2>"))
        notice = QLabel(
            "<ul>"
            "<li>"
            + bi(
                "This tool only analyzes text you choose to provide.",
                "本工具仅分析您主动提供的文本。",
            )
            + "</li>"
            "<li>"
            + bi(
                "Do not import other people's private data without permission.",
                "请勿在未获得许可的情况下导入他人的隐私数据。",
            )
            + "</li>"
            "<li>"
            + bi(
                "This tool is not legal, criminal, psychological, or medical judgment.",
                "本工具不构成法律、刑事、心理或医学方面的判断。",
            )
            + "</li>"
            "<li>"
            + bi("A risk report is only decision support.", "风险报告仅作为决策参考。")
            + "</li>"
            "<li>"
            + bi(
                "A signature only proves report integrity, not real-world truth.",
                "签名仅证明报告内容完整未被篡改，不证明现实世界的真相。",
            )
            + "</li>"
            "</ul>"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        self.checkbox = QCheckBox(
            bi("I understand and consent to local analysis.", "我理解并同意进行本地分析。")
        )
        self.checkbox.stateChanged.connect(self._update_consent)
        layout.addWidget(self.checkbox)
        layout.addStretch()

    def _update_consent(self) -> None:
        self.state["consent_confirmed"] = self.checkbox.isChecked()
