import json

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QTextEdit, QVBoxLayout, QWidget

from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileViewerScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(StepHeader("View / Edit Local Profile"))
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        self.editor = QTextEdit()
        layout.addWidget(self.editor)
        nav = QHBoxLayout()
        save_md = SecondaryButton("Save Markdown Profile")
        save_md.clicked.connect(self._save_markdown)
        show_json = SecondaryButton("Show JSON Companion")
        show_json.clicked.connect(self._show_json)
        home = SecondaryButton("Home")
        home.clicked.connect(on_home)
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        for button in [save_md, show_json, home, back]:
            nav.addWidget(button)
        layout.addLayout(nav)

    def on_enter(self) -> None:
        text = self.state.current_profile_markdown
        if not text and self.profile_store.markdown_path.exists():
            text = self.profile_store.load_markdown_profile()
            self.state.current_profile_markdown = text
        self.editor.setPlainText(text or "No Markdown Profile loaded yet.")
        self.path_label.setText(f"Markdown Profile path: {self.state.profile_path}")

    def _save_markdown(self) -> None:
        path = self.profile_store.save_markdown_profile(self.editor.toPlainText())
        self.state.profile_path = path
        self.state.current_profile_markdown = self.editor.toPlainText()
        self.state.profile_exists = True
        QMessageBox.information(self, "Saved", f"Saved profile.mpm.md to:\n{path}")

    def _show_json(self) -> None:
        profile = self.state.current_profile_json
        if not profile and self.profile_store.json_path.exists():
            profile = self.profile_store.load_json_profile()
        self.editor.setPlainText(json.dumps(profile or {}, indent=2, ensure_ascii=False))
