from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class PolicyConsentScreen(QWidget):
    def __init__(self, state, on_next, on_back) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(StepHeader("Safety & Consent", "Policy first, before import or analysis."))
        content = QLabel(
            "<ul>"
            "<li>This app analyzes only data you choose to provide.</li>"
            "<li>Import only your own data, or data you have permission to use.</li>"
            "<li>The app does not judge whether a real person is good or bad.</li>"
            "<li>The app does not make legal, criminal, psychological, or medical "
            "determinations.</li>"
            "<li>Risk analysis is only decision support.</li>"
            "<li>Do not use this app for stalking, doxxing, harassment, revenge, "
            "blackmail, or public shaming.</li>"
            "<li>Your local profile is stored on your computer.</li>"
            "</ul>"
        )
        content.setWordWrap(True)
        layout.addWidget(content)
        self.checkbox = QCheckBox(
            "I understand and agree to use this app for self-protection and self-reflection only."
        )
        layout.addWidget(self.checkbox)
        self.next_button = PrimaryButton("Next")
        self.next_button.setEnabled(False)
        self.checkbox.stateChanged.connect(self._toggle_next)
        self.next_button.clicked.connect(lambda: self._accept(on_next))
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        layout.addWidget(self.next_button)
        layout.addWidget(back)
        layout.addStretch()

    def _toggle_next(self) -> None:
        self.next_button.setEnabled(self.checkbox.isChecked())

    def _accept(self, on_next) -> None:
        self.state.consent_accepted = True
        on_next()
