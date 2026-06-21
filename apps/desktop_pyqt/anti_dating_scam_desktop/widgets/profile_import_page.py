import json
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.engine.chatgpt_export_parser import ChatGPTExportParser


class ProfileImportPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.parser = ChatGPTExportParser()

        layout = QVBoxLayout(self)
        title = QLabel("<h2>Import My Profile</h2>")
        layout.addWidget(title)

        warning = QLabel(
            "ChatGPT export may contain sensitive data. Import only your own data. "
            "The MVP processes imports locally and does not upload them. ChatGPT "
            "Memory Summary may be incomplete; treat it as one input source, not an "
            "authoritative full self-profile."
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)

        layout.addWidget(QLabel("Manually written self-profile notes"))
        self.manual_notes = QTextEdit()
        self.manual_notes.setPlaceholderText(
            "Paste your own relationship values, boundaries, communication preferences, "
            "and safety concerns."
        )
        self.manual_notes.textChanged.connect(self._sync_text)
        layout.addWidget(self.manual_notes)

        layout.addWidget(QLabel("Pasted ChatGPT Memory Summary"))
        self.memory_summary = QTextEdit()
        self.memory_summary.setPlaceholderText(
            "Paste your own ChatGPT Memory Summary here. It may be incomplete."
        )
        self.memory_summary.textChanged.connect(self._sync_text)
        layout.addWidget(self.memory_summary)

        buttons = QHBoxLayout()
        import_text = QPushButton("Import .txt/.md/.json Notes")
        import_text.clicked.connect(self._import_text_file)
        import_export = QPushButton("Import ChatGPT Export ZIP/JSON")
        import_export.clicked.connect(self._import_chatgpt_export)
        buttons.addWidget(import_text)
        buttons.addWidget(import_export)
        layout.addLayout(buttons)

        self.metadata_output = QTextEdit()
        self.metadata_output.setReadOnly(True)
        self.metadata_output.setPlaceholderText("ChatGPT export metadata will appear here.")
        layout.addWidget(self.metadata_output)

    def _sync_text(self) -> None:
        self.state["manual_notes"] = self.manual_notes.toPlainText()
        self.state["memory_summary"] = self.memory_summary.toPlainText()

    def _import_text_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import local notes",
            "",
            "Text and JSON files (*.txt *.md *.json)",
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        if path.lower().endswith(".json"):
            try:
                parsed = json.loads(text)
                text = json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        self.manual_notes.setPlainText(text)
        self._sync_text()

    def _import_chatgpt_export(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import ChatGPT export locally",
            "",
            "ChatGPT export files (*.zip *.json)",
        )
        if not path:
            return
        summary = self.parser.parse(path).to_dict()
        self.state["chatgpt_export_summary"] = summary
        safe_summary = dict(summary)
        safe_summary["limited_text_snippets"] = [
            f"Snippet {index + 1}: {len(snippet)} characters"
            for index, snippet in enumerate(summary.get("limited_text_snippets", []))
        ]
        self.metadata_output.setPlainText(json.dumps(safe_summary, indent=2, ensure_ascii=False))
