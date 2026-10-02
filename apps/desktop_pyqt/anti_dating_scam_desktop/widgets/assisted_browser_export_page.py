import json
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
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
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox


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
        layout.addWidget(
            QLabel(f"<h2>{bi('Assisted Browser Export', '辅助浏览器导出')}</h2>")
        )
        intro = QLabel(
            bi(
                "User-assisted local automation only. This tool does not bypass login, "
                "CAPTCHA, rate limits, private APIs, cookies, tokens, localStorage, or "
                "sessionStorage. Official exports are preferred when available.",
                "仅进行用户辅助的本地自动化。本工具不会绕过登录、验证码、频率限制、私有 API、"
                "Cookie、令牌、localStorage 或 sessionStorage。如有官方导出，请优先使用。",
            )
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.own_data = WrappedCheckBox(
            bi("I am exporting my own data.", "我导出的是我自己的数据。")
        )
        self.permission = WrappedCheckBox(
            bi(
                "I will not import other people's private data without permission.",
                "未经许可，我不会导入他人的私密数据。",
            )
        )
        self.no_bypass = WrappedCheckBox(
            bi(
                "I understand this tool does not bypass login or CAPTCHA.",
                "我理解本工具不会绕过登录或验证码。",
            )
        )
        self.local_only = WrappedCheckBox(
            bi(
                "I understand exported data stays local unless I explicitly export/share it.",
                "我理解除非我明确导出/分享，导出的数据都保留在本地。",
            )
        )
        self.sensitive = WrappedCheckBox(
            bi(
                "I understand imported chats may contain sensitive information.",
                "我理解导入的聊天可能包含敏感信息。",
            )
        )
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
        form.addRow(bi("Export folder", "导出文件夹"), self.export_folder)
        form.addRow(bi("Max chats per run", "每次运行最多导出对话数"), self.max_chats)
        form.addRow(bi("Delay between exports", "每次导出之间的延迟"), self.delay)
        form.addRow(bi("Extension path, optional", "扩展路径（可选）"), self.extension_path)
        form.addRow(bi("Extension id, optional", "扩展 ID（可选）"), self.extension_id)
        form.addRow(
            bi("Chat list selector, advanced", "对话列表选择器（高级）"), self.chat_list_selector
        )
        form.addRow(
            bi("Export button selector, advanced", "导出按钮选择器（高级）"),
            self.export_button_selector,
        )
        layout.addLayout(form)

        buttons = QGridLayout()
        buttons.setColumnStretch(0, 1)
        buttons.setColumnStretch(1, 1)
        button_specs = [
            (bi("Launch browser", "启动浏览器"), self._launch_browser),
            (bi("I am logged in / ready", "我已登录 / 准备就绪"), self._ready),
            (bi("Capture current visible chat", "捕获当前可见对话"), self._capture_visible_chat),
            (
                bi(
                    "Experimental: Run Chat2file-assisted export",
                    "实验性：运行 Chat2file 辅助导出",
                ),
                self._chat2file_plan,
            ),
            (bi("Pause", "暂停"), self._pause),
            (bi("Stop", "停止"), self._stop),
            (bi("Open export folder", "打开导出文件夹"), self._open_export_folder),
            (
                bi("Import exported files into profile builder", "将导出文件导入档案构建器"),
                self._import_exports,
            ),
        ]
        # Long action labels retain their full wording across both columns.
        positions = [
            (0, 0, 1), (0, 1, 1), (1, 0, 2), (2, 0, 2),
            (3, 0, 1), (3, 1, 1), (4, 0, 2), (5, 0, 2),
        ]
        for (label, handler), (row, column, span) in zip(button_specs, positions, strict=True):
            button = QPushButton(label)
            button.clicked.connect(handler)
            buttons.addWidget(button, row, column, 1, span)
        layout.addLayout(buttons)

        self.status = QLabel(
            bi("Status: waiting for consent checklist.", "状态：等待勾选同意清单。")
        )
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            bi(
                "Session log preview, warnings, and exported file metadata.",
                "会话日志预览、警告，以及导出文件的元数据。",
            )
        )
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
        self.status.setText(
            bi(
                "Status: visible browser launched. Log in manually, then click ready.",
                "状态：可见浏览器已启动。请手动登录后点击「准备就绪」。",
            )
        )

    def _ready(self) -> None:
        if not self._consent_confirmed():
            self._show_error(
                bi("Complete the safety checklist first.", "请先完成安全清单的勾选。")
            )
            return
        self.status.setText(
            bi(
                "Status: user confirmed ready. Automation will stay visible and local.",
                "状态：用户已确认就绪。自动化将保持可见并在本地运行。",
            )
        )

    def _capture_visible_chat(self) -> None:
        if not self.context or not self.context.pages:
            self._show_error(bi("Launch the visible browser first.", "请先启动可见浏览器。"))
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
        self.status.setText(f"{bi('Status: exported', '状态：已导出')} {paths['json'].name}")
        self._render_log()

    def _chat2file_plan(self) -> None:
        try:
            plan = self.chat2file.run(self._config(ExportMode.CHAT2FILE_ASSISTED))
        except BrowserExportError as exc:
            self._show_error(str(exc))
            return
        self.status.setText(
            bi(
                "Status: Chat2file-assisted plan created; no forced automation ran.",
                "状态：已创建 Chat2file 辅助计划；未运行任何强制自动化。",
            )
        )
        self.output.setPlainText(json.dumps(plan, indent=2, ensure_ascii=False))

    def _pause(self) -> None:
        self.chat2file.pause()
        self.status.setText(bi("Status: paused.", "状态：已暂停。"))

    def _stop(self) -> None:
        self.chat2file.stop()
        self.status.setText(bi("Status: stopped.", "状态：已停止。"))

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
            f"{bi('Status: imported', '状态：已导入')} {imported_count} "
            f"{bi('snippets into profile builder state.', '条片段到档案构建器状态中。')}"
        )

    def _show_error(self, message: str) -> None:
        self.session_log.add_error(message)
        QMessageBox.warning(self, bi("Assisted browser export", "辅助浏览器导出"), message)
        self._render_log()

    def _render_log(self) -> None:
        self.output.setPlainText(
            json.dumps(self.session_log.to_dict(), indent=2, ensure_ascii=False)
        )
