from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget


class ConsentPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Consent / Safety</h2>"))
        notice = QLabel(
            "<ul>"
            "<li>This tool only analyzes text you choose to provide.</li>"
            "<li>Do not import other people's private data without permission.</li>"
            "<li>This tool is not legal, criminal, psychological, or medical judgment.</li>"
            "<li>A risk report is only decision support.</li>"
            "<li>A signature only proves report integrity, not real-world truth.</li>"
            "</ul>"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        self.checkbox = QCheckBox("I understand and consent to local analysis.")
        self.checkbox.stateChanged.connect(self._update_consent)
        layout.addWidget(self.checkbox)
        layout.addStretch()

    def _update_consent(self) -> None:
        self.state["consent_confirmed"] = self.checkbox.isChecked()
