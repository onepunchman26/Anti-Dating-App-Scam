from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QGridLayout, QTextEdit, QVBoxLayout, QWidget

from anti_dating_scam.engine.chatgpt_export_parser import ChatGPTExportParser
from anti_dating_scam_desktop.widgets.app_card import AppCard
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class ImportDataScreen(QWidget):
    def __init__(self, state, on_generation, on_assisted_export, on_back) -> None:
        super().__init__()
        self.state = state
        self.parser = ChatGPTExportParser()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                "Import Data to Build Your Local Profile",
                "Choose one or more local sources. Nothing is uploaded by this screen.",
            )
        )
        self.banner = StatusBanner("No sources imported yet.")
        layout.addWidget(self.banner)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Paste Manual Markdown / Notes here.")
        layout.addWidget(self.notes)
        grid = QGridLayout()
        cards = [
            AppCard(
                "Manual Markdown / Notes",
                "Paste above or load a local .md / .txt file.",
                "Import",
                self._import_notes,
            ),
            AppCard(
                "ChatGPT Export ZIP",
                "Load an official local export if available.",
                "Import",
                self._import_chatgpt_export,
            ),
            AppCard(
                "Saved Web AI Chat HTML / JSON",
                "Load exported or saved files from another AI chat platform.",
                "Import",
                self._import_saved_file,
            ),
            AppCard(
                "Assisted Browser Export",
                "Open the user-assisted local browser export screen.",
                "Open",
                on_assisted_export,
            ),
            AppCard(
                "Existing Profile File",
                "Choose an existing .mpm.md or .json profile.",
                "Import",
                self._import_existing_profile,
            ),
        ]
        for index, card in enumerate(cards):
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        next_button = PrimaryButton("Continue to Generate Profile")
        next_button.clicked.connect(on_generation)
        back = SecondaryButton("Back")
        back.clicked.connect(on_back)
        layout.addWidget(next_button)
        layout.addWidget(back)

    def _import_notes(self) -> None:
        text = self.notes.toPlainText().strip()
        if not text:
            path, _ = QFileDialog.getOpenFileName(
                self, "Load Markdown or notes", "", "Notes (*.md *.txt)"
            )
            if not path:
                return
            selected = Path(path)
            text = selected.read_text(encoding="utf-8")
            self.state.import_sources.append(selected)
        self.state.manual_notes = text
        self._update_banner()

    def _import_chatgpt_export(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load ChatGPT export", "", "ChatGPT export (*.zip *.json)"
        )
        if not path:
            return
        selected = Path(path)
        self.state.import_sources.append(selected)
        self.state.chatgpt_export_summary = self.parser.parse(selected).to_dict()
        self._update_banner()

    def _import_saved_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load saved AI chat file", "", "AI chat files (*.html *.htm *.json *.md *.txt)"
        )
        if not path:
            return
        selected = Path(path)
        self.state.import_sources.append(selected)
        self.state.manual_notes += "\n\n" + selected.read_text(encoding="utf-8", errors="ignore")
        self._update_banner()

    def _import_existing_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load existing profile", "", "Profile files (*.mpm.md *.md *.json)"
        )
        if not path:
            return
        selected = Path(path)
        self.state.import_sources.append(selected)
        if selected.suffix == ".json":
            self.state.profile_json_path = selected
        else:
            self.state.profile_path = selected
        self._update_banner()

    def _update_banner(self) -> None:
        self.banner.set_text(f"Imported sources: {len(self.state.import_sources)}")
