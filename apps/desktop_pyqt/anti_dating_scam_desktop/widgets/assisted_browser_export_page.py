import json
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.browser_export.chat2file_assistant import Chat2FileAssistant
from anti_dating_scam.browser_export.errors import BrowserExportError
from anti_dating_scam.browser_export.export_models import BrowserExportConfig, ExportMode
from anti_dating_scam.browser_export.export_session_log import ExportSessionLog
from anti_dating_scam.browser_export.playwright_runner import PlaywrightBrowserRunner
from anti_dating_scam.browser_export.visible_text_extractor import VisibleTextExtractor


class AssistedBrowserExportPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.runner = PlaywrightBrowserRunner()
        self.extractor = VisibleTextExtractor()
        self.chat2file = Chat2FileAssistant()
        self.session_log = ExportSessionLog(ExportMode.VISIBLE_PAGE_EXPORT)
        self.playwright = None
        self.context = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Assisted Browser Export</h2>"))
        intro = QLabel(
            "User-assisted local automation only. This tool does not bypass login, "
            "CAPTCHA, rate limits, private APIs, cookies, tokens, localStorage, or "
            "sessionStorage. Official exports are preferred when available."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.own_data = QCheckBox("I am exporting my own data.")
        self.permission = QCheckBox(
            "I will not import other people's private data without permission."
        )
        self.no_bypass = QCheckBox("I understand this tool does not bypass login or CAPTCHA.")
        self.local_only = QCheckBox(
            "I understand exported data stays local unless I explicitly export/share it."
        )
        self.sensitive = QCheckBox("I understand imported chats may contain sensitive information.")
        for checkbox in [
            self.own_data,
            self.permission,
            self.no_bypass,
            self.local_only,
            self.sensitive,
        ]:
            layout.addWidget(checkbox)

        form = QFormLayout()
        self.export_folder = QLineEdit("local_exports/browser_exports")
        self.max_chats = QSpinBox()
        self.max_chats.setRange(1, 100)
        self.max_chats.setValue(10)
        self.delay = QDoubleSpinBox()
        self.delay.setRange(0.5, 60.0)
        self.delay.setValue(2.0)
        self.extension_path = QLineEdit()
        self.extension_id = QLineEdit()
        self.chat_list_selector = QLineEdit()
        self.export_button_selector = QLineEdit()
        form.addRow("Export folder", self.export_folder)
        form.addRow("Max chats per run", self.max_chats)
        form.addRow("Delay between exports", self.delay)
        form.addRow("Extension path, optional", self.extension_path)
        form.addRow("Extension id, optional", self.extension_id)
        form.addRow("Chat list selector, advanced", self.chat_list_selector)
        form.addRow("Export button selector, advanced", self.export_button_selector)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        button_specs = [
            ("Launch browser", self._launch_browser),
            ("I am logged in / ready", self._ready),
            ("Capture current visible chat", self._capture_visible_chat),
            ("Experimental: Run Chat2file-assisted export", self._chat2file_plan),
            ("Pause", self._pause),
            ("Stop", self._stop),
            ("Open export folder", self._open_export_folder),
            ("Import exported files into profile builder", self._import_exports),
        ]
        for label, handler in button_specs:
            button = QPushButton(label)
            button.clicked.connect(handler)
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.status = QLabel("Status: waiting for consent checklist.")
        layout.addWidget(self.status)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Session log preview, warnings, and exported file metadata.")
        layout.addWidget(self.output)

    def _consent_confirmed(self) -> bool:
        return all(
            checkbox.isChecked()
            for checkbox in [
                self.own_data,
                self.permission,
                self.no_bypass,
                self.local_only,
                self.sensitive,
            ]
        )

    def _config(self, mode: ExportMode) -> BrowserExportConfig:
        extension_path = self.extension_path.text().strip()
        export_folder = self.export_folder.text().strip() or "local_exports/browser_exports"
        return BrowserExportConfig(
            consent_confirmed=self._consent_confirmed(),
            mode=mode,
            export_folder=Path(export_folder),
            max_chats_per_run=self.max_chats.value(),
            delay_between_exports_seconds=self.delay.value(),
            extension_path=Path(extension_path) if extension_path else None,
            extension_id=self.extension_id.text().strip() or None,
            chat_list_selector=self.chat_list_selector.text().strip() or None,
            export_button_selector=self.export_button_selector.text().strip() or None,
        )

    def _launch_browser(self) -> None:
        try:
            self.playwright, self.context = self.runner.launch_visible_context(
                self._config(ExportMode.VISIBLE_PAGE_EXPORT)
            )
        except BrowserExportError as exc:
            self._show_error(str(exc))
            return
        self.status.setText("Status: visible browser launched. Log in manually, then click ready.")

    def _ready(self) -> None:
        if not self._consent_confirmed():
            self._show_error("Complete the safety checklist first.")
            return
        self.status.setText("Status: user confirmed ready. Automation will stay visible and local.")

    def _capture_visible_chat(self) -> None:
        if not self.context or not self.context.pages:
            self._show_error("Launch the visible browser first.")
            return
        try:
            config = self._config(ExportMode.VISIBLE_PAGE_EXPORT)
            page = self.context.pages[-1]
            export = self.extractor.extract_from_sync_playwright_page(page)
            paths = self.extractor.save_export(export, config.export_folder)
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.session_log.add_file(paths["json"])
        self.session_log.add_file(paths["markdown"])
        self.status.setText(f"Status: exported {paths['json'].name}")
        self._render_log()

    def _chat2file_plan(self) -> None:
        try:
            plan = self.chat2file.run(self._config(ExportMode.CHAT2FILE_ASSISTED))
        except BrowserExportError as exc:
            self._show_error(str(exc))
            return
        self.status.setText("Status: Chat2file-assisted plan created; no forced automation ran.")
        self.output.setPlainText(json.dumps(plan, indent=2, ensure_ascii=False))

    def _pause(self) -> None:
        self.chat2file.pause()
        self.status.setText("Status: paused.")

    def _stop(self) -> None:
        self.chat2file.stop()
        self.status.setText("Status: stopped.")

    def _open_export_folder(self) -> None:
        folder = Path(self.export_folder.text().strip() or "local_exports/browser_exports")
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def _import_exports(self) -> None:
        folder = Path(self.export_folder.text().strip() or "local_exports/browser_exports")
        files = sorted(folder.glob("visible_page_export_*.json"))
        snippets: list[str] = []
        for file_path in files[:20]:
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for chunk in payload.get("chunks", [])[:5]:
                text = chunk.get("text", "")
                if text:
                    snippets.append(text[:500])
        self.state["chatgpt_export_summary"] = {
            "source_path": str(folder),
            "conversations_count": len(files),
            "messages_count": len(snippets),
            "date_range": {"start": None, "end": None},
            "limited_text_snippets": snippets[:20],
            "warnings": [
                (
                    "Imported visible-page exports may be incomplete and should be "
                    "reviewed by the user."
                )
            ],
            "errors": [],
        }
        imported_count = len(snippets[:20])
        self.status.setText(
            f"Status: imported {imported_count} snippets into profile builder state."
        )

    def _show_error(self, message: str) -> None:
        self.session_log.add_error(message)
        QMessageBox.warning(self, "Assisted browser export", message)
        self._render_log()

    def _render_log(self) -> None:
        self.output.setPlainText(
            json.dumps(self.session_log.to_dict(), indent=2, ensure_ascii=False)
        )
