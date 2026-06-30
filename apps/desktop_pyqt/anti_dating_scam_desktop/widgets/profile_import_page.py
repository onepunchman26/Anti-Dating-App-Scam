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
from anti_dating_scam_desktop.i18n import bi


class ProfileImportPage(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self.parser = ChatGPTExportParser()

        layout = QVBoxLayout(self)
        title = QLabel(f"<h2>{bi('Import My Profile', '导入我的档案')}</h2>")
        layout.addWidget(title)

        warning = QLabel(
            bi(
                "ChatGPT export may contain sensitive data. Import only your own data. "
                "The MVP processes imports locally and does not upload them. ChatGPT "
                "Memory Summary may be incomplete; treat it as one input source, not an "
                "authoritative full self-profile.",
                "ChatGPT 导出文件可能包含敏感数据，请只导入您自己的数据。"
                "本 MVP 在本地处理导入内容，不会上传。ChatGPT 记忆摘要可能并不完整，"
                "请将其视为一项输入来源，而非权威、完整的自我档案。",
            )
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)

        layout.addWidget(QLabel(bi("Manually written self-profile notes", "手写的自我档案笔记")))
        self.manual_notes = QTextEdit()
        self.manual_notes.setPlaceholderText(
            bi(
                "Paste your own relationship values, boundaries, communication preferences, "
                "and safety concerns.",
                "粘贴您自己的关系价值观、边界、沟通偏好以及安全方面的顾虑。",
            )
        )
        self.manual_notes.textChanged.connect(self._sync_text)
        layout.addWidget(self.manual_notes)

        layout.addWidget(QLabel(bi("Pasted ChatGPT Memory Summary", "已粘贴的 ChatGPT 记忆摘要")))
        self.memory_summary = QTextEdit()
        self.memory_summary.setPlaceholderText(
            bi(
                "Paste your own ChatGPT Memory Summary here. It may be incomplete.",
                "在此粘贴您自己的 ChatGPT 记忆摘要，内容可能并不完整。",
            )
        )
        self.memory_summary.textChanged.connect(self._sync_text)
        layout.addWidget(self.memory_summary)

        buttons = QHBoxLayout()
        import_text = QPushButton(bi("Import .txt/.md/.json Notes", "导入 .txt/.md/.json 笔记"))
        import_text.clicked.connect(self._import_text_file)
        import_export = QPushButton(
            bi("Import ChatGPT Export ZIP/JSON", "导入 ChatGPT 导出 ZIP/JSON")
        )
        import_export.clicked.connect(self._import_chatgpt_export)
        buttons.addWidget(import_text)
        buttons.addWidget(import_export)
        layout.addLayout(buttons)

        self.metadata_output = QTextEdit()
        self.metadata_output.setReadOnly(True)
        self.metadata_output.setPlaceholderText(
            bi("ChatGPT export metadata will appear here.", "ChatGPT 导出元数据将显示在此处。")
        )
        layout.addWidget(self.metadata_output)

    def _sync_text(self) -> None:
        self.state["manual_notes"] = self.manual_notes.toPlainText()
        self.state["memory_summary"] = self.memory_summary.toPlainText()

    def _import_text_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            bi("Import local notes", "导入本地笔记"),
            "",
            "Text and JSON files (*.txt *.md *.json)",
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, bi("Import failed", "导入失败"), str(exc))
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
            bi("Import ChatGPT export locally", "在本地导入 ChatGPT 导出文件"),
            "",
            "ChatGPT export files (*.zip *.json)",
        )
        if not path:
            return
        summary = self.parser.parse(path).to_dict()
        self.state["chatgpt_export_summary"] = summary
        safe_summary = dict(summary)
        safe_summary["limited_text_snippets"] = [
            f"{bi('Snippet', '片段')} {index + 1}: {len(snippet)} {bi('characters', '字符')}"
            for index, snippet in enumerate(summary.get("limited_text_snippets", []))
        ]
        self.metadata_output.setPlainText(json.dumps(safe_summary, indent=2, ensure_ascii=False))
