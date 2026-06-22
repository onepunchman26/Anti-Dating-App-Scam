import json

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from anti_dating_scam.profile.mpmd_profile import MPMDProfile
from anti_dating_scam.profile.profile_json import build_profile_json_from_sources
from anti_dating_scam.profile.profile_markdown import profile_to_mpmd_markdown
from anti_dating_scam.reports.schema_validator import validate_document
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileGenerationScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(StepHeader("Generate Local Profile"))
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.output = QTextEdit()
        self.output.setPlaceholderText("Generated MPMD Profile will appear here.")
        layout.addWidget(self.output)
        generate = PrimaryButton("Generate Profile")
        generate.clicked.connect(self._generate)
        save_md = QPushButton("Save as profile.mpm.md")
        save_md.clicked.connect(self._save_markdown)
        save_json = QPushButton("Save as profile.json")
        save_json.clicked.connect(self._save_json)
        home = PrimaryButton("Continue to Home")
        home.clicked.connect(on_home)
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        for button in [generate, save_md, save_json, home, back]:
            layout.addWidget(button)

    def on_enter(self) -> None:
        mode = self.state.analysis_mode or "not selected"
        mode_note = (
            "Agent Mode: you can export/import files locally and ask your coding/AI "
            "agent to improve the profile using only files you explicitly provide."
            if mode == "agent"
            else "API Mode is a placeholder in this MVP; no real API call will be made."
        )
        names = [source.name for source in self.state.import_sources]
        self.summary.setText(
            f"Imported source count: {len(names)}\n"
            f"Sources: {', '.join(names) if names else 'manual text only or none yet'}\n"
            f"Analysis mode: {mode}\n"
            "Privacy warning: review and redact sensitive content before sharing.\n"
            f"{mode_note}"
        )

    def _generate(self) -> None:
        profile_json = build_profile_json_from_sources(
            manual_notes=self.state.manual_notes,
            memory_summary=self.state.memory_summary,
            chatgpt_export_summary=self.state.chatgpt_export_summary,
        )
        validate_document(profile_json, "personal_profile.schema.json")
        markdown = profile_to_mpmd_markdown(MPMDProfile.from_profile_json(profile_json))
        self.state.current_profile_json = profile_json
        self.state.current_profile_markdown = markdown
        self.output.setPlainText(markdown)

    def _save_markdown(self) -> None:
        markdown = self.output.toPlainText() or self.state.current_profile_markdown
        if not markdown:
            QMessageBox.information(self, "No profile", "Generate a profile first.")
            return
        path = self.profile_store.save_markdown_profile(markdown)
        self.state.profile_path = path
        self.state.profile_exists = True
        QMessageBox.information(self, "Saved", f"Saved Markdown Profile to:\n{path}")

    def _save_json(self) -> None:
        profile = self.state.current_profile_json
        if not profile:
            try:
                profile = json.loads(self.output.toPlainText())
            except json.JSONDecodeError:
                QMessageBox.information(self, "No JSON profile", "Generate a profile first.")
                return
        path = self.profile_store.save_json_profile(profile)
        self.state.profile_json_path = path
        self.state.profile_exists = True
        QMessageBox.information(self, "Saved", f"Saved JSON Profile to:\n{path}")
