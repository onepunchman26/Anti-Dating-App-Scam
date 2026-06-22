from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget

from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ProfileDetectionScreen(QWidget):
    def __init__(self, state, profile_store, on_home, on_import, on_mode, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        self.on_home = on_home
        self.on_import = on_import
        self.on_mode = on_mode
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(StepHeader("Local Profile Detection"))
        self.status = StatusBanner()
        layout.addWidget(self.status)
        self.detail = QLabel()
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)

        self.continue_button = PrimaryButton("Continue with Existing Profile")
        self.continue_button.clicked.connect(self._continue_existing)
        self.update_button = SecondaryButton("Import More Data / Update Profile")
        self.update_button.clicked.connect(on_mode)
        self.choose_button = SecondaryButton("Choose Another Profile File")
        self.choose_button.clicked.connect(self._choose_profile)
        self.create_button = PrimaryButton("Create My Local Profile")
        self.create_button.clicked.connect(on_mode)
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        for button in [
            self.continue_button,
            self.update_button,
            self.choose_button,
            self.create_button,
            back,
        ]:
            layout.addWidget(button)
        layout.addStretch()

    def on_enter(self) -> None:
        self.profile_store.create_default_directories()
        exists = self.profile_store.detect_existing_profile()
        self.state.profile_exists = exists
        self.state.profile_path = self.profile_store.markdown_path
        self.state.profile_json_path = self.profile_store.json_path
        if exists:
            self.status.set_text("Existing Local Profile Found")
            self.detail.setText(
                f"Markdown Profile: {self.profile_store.markdown_path}\n"
                f"JSON Profile: {self.profile_store.json_path}"
            )
            self.continue_button.show()
            self.update_button.show()
            self.choose_button.show()
            self.create_button.hide()
        else:
            self.status.set_text("No Local Profile Found")
            self.detail.setText(
                "AI-SlowMatch uses a local profile to personalize reflection and risk "
                "education. You can create one from your own notes or exported AI chats."
            )
            self.continue_button.hide()
            self.update_button.hide()
            self.choose_button.hide()
            self.create_button.show()

    def _continue_existing(self) -> None:
        if self.profile_store.markdown_path.exists():
            self.state.current_profile_markdown = self.profile_store.load_markdown_profile()
        if self.profile_store.json_path.exists():
            self.state.current_profile_json = self.profile_store.load_json_profile()
        self.on_home()

    def _choose_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose profile.mpm.md or profile.json",
            str(Path.home()),
            "Profile files (*.mpm.md *.md *.json)",
        )
        if not path:
            return
        selected = Path(path)
        if selected.suffix == ".json":
            self.state.profile_json_path = selected
            self.state.current_profile_json = self.profile_store.load_json_profile(selected)
        else:
            self.state.profile_path = selected
            self.state.current_profile_markdown = self.profile_store.load_markdown_profile(selected)
        self.state.profile_exists = True
        self.on_home()
