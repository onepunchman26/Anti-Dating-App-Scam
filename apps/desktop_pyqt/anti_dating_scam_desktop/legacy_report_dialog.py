"""Inspect and archive fixed original report files without conversion or activation."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.services.legacy_reports import LegacyReportError, LegacyReportService
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton

_ERRORS = (LegacyReportError, OSError, ValueError)


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


def _reader() -> QPlainTextEdit:
    reader = QPlainTextEdit()
    reader.setReadOnly(True)
    return reader


def _format(value: str) -> str:
    labels = {
        "self_portrait_v03": ("Legacy portrait 0.3", "旧版画像 0.3"),
        "mate_criteria_legacy_v01": ("Legacy criteria 0.1", "旧版择偶标准 0.1"),
        "current_structured": (
            "Primary JSON matches the current structure; companions need separate checks",
            "主 JSON 符合当前结构；配套文件需另行检查",
        ),
        "markdown_only": ("Markdown only", "仅有 Markdown 文件"),
        "unrecognized": ("Unrecognized format", "无法识别的格式"),
        "missing": ("Original files missing", "原始文件缺失"),
    }
    return bi(*labels.get(value, ("Unrecognized format", "无法识别的格式")))


def _file_label(file) -> str:
    state = bi("missing", "缺失") if not file.present else (
        bi("UTF-8 text", "UTF-8 文本") if file.encoding == "utf8" else bi("binary", "二进制")
    )
    return f"{file.label} — {state} — {file.size_bytes} {bi('bytes', '字节')}"


def _file_text(file, raw: bytes | None = None) -> str:
    if not file.present:
        return bi(
            "This file was absent in this snapshot. No content has been invented.",
            "此文件在该快照中不存在，应用未补造任何内容。",
        )
    if file.encoding != "utf8":
        return bi(
            "This file is not decodable UTF-8 text. Its exact bytes are preserved in the "
            "archive; no text preview or automatic conversion is available.",
            "此文件无法解码为 UTF-8 文本。归档会完整保留原始字节；不提供文字预览，也不会"
            "自动转换。",
        ) + f"\n\nSHA256: {file.sha256}"
    return raw.decode("utf-8") if raw is not None else (file.text or "")


def _summary(preview) -> str:
    return "English\n\n" + preview.review_text_en + "\n\n中文版\n\n" + preview.review_text_zh


def _ledger(preview) -> str:
    types = {
        "object": bi("object", "对象"), "array": bi("array", "数组"),
        "string": bi("string", "字符串"), "number": bi("number", "数值"),
        "boolean": bi("boolean", "布尔值"), "null": bi("null", "空值"),
        "opaque": bi("unparsed content", "未解析内容"),
    }
    return bi(
        "Top-level JSON fields, preserved only; nested values remain in the original files.",
        "顶层 JSON 字段仅作保留；嵌套值仍完整存在于原始文件中。",
    ) + "\n\n" + "\n".join(
        f"{field.file_label} {field.pointer} ({types[field.value_type]}) — "
        + bi("preserved only", "仅保留原文") for field in preview.field_ledger
    )


class LegacyReportDialog(QDialog):
    """Reads and byte-preserving archival saves only; no source or selection writes."""

    def __init__(self, vault_dir: Path, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.vault_dir = Path(vault_dir)
        self.kind = kind
        self.service = None
        self.inspection = None
        self.preview = None
        self.saved_archive = None
        self._current_files = []
        self._saved = []
        self._history_preview = None
        self._history_id = None
        self._stale = False
        self.setWindowTitle(bi("Review legacy files", "复核旧版文件"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Inspect original report files and save an exact-byte archive, including unknown "
            "fields. This preserves files; it does not convert them into a validated report, "
            "invent evidence or translations, activate a report, or restore files. "
            "Original files, cards and the active selection remain unchanged. No AI runs.",
            "检查原始报告文件，并按原始字节归档，包括未知字段。此功能用于保留文件，不会将其"
            "转换为已验证报告、补造证据或翻译、启用报告或恢复文件。原文件、卡片及当前选择"
            "保持不变。此操作不调用 AI。",
        )))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.diagnostics = _reader()
        self.tabs.addTab(self.diagnostics, bi("Findings", "检查结果"))
        originals_tab = QWidget()
        originals_layout = QVBoxLayout(originals_tab)
        originals_layout.addWidget(_label(bi(
            "Literal original content, including unsupported fields. It is not verified "
            "advice. Links, images and file paths are displayed only as text.",
            "下方原样显示文件内容，包括不受支持的字段。内容不代表已验证的建议；链接、图片和"
            "路径均仅作为文字显示。",
        )))
        self.files = QComboBox()
        self.files.currentIndexChanged.connect(self._show_original)
        originals_layout.addWidget(self.files)
        self.original_text = _reader()
        originals_layout.addWidget(self.original_text, 1)
        self.tabs.addTab(originals_tab, bi("Original files", "原始文件"))

        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.preview_text = _reader()
        preview_layout.addWidget(self.preview_text, 1)
        self.field_ledger = _reader()
        self.field_ledger.setMaximumHeight(150)
        preview_layout.addWidget(self.field_ledger)
        self.tabs.addTab(preview_tab, bi("Archive preview", "归档预览"))

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(_label(bi(
            "Saved archives are integrity-checked before display and remain available after "
            "the originals change. They are not active reports or AI evidence.",
            "已保存归档会在显示前检查完整性，原文件变更后仍可查看。归档不是当前报告，也不是"
            "AI 证据。",
        )))
        self.history = QListWidget()
        self.history.setMaximumHeight(80)
        self.history.currentRowChanged.connect(self._open_archive)
        history_layout.addWidget(self.history)
        self.saved_files = QComboBox()
        self.saved_files.currentIndexChanged.connect(self._show_snapshot)
        history_layout.addWidget(self.saved_files)
        self.saved_text = _reader()
        history_layout.addWidget(self.saved_text, 1)
        self.conversion_button = SecondaryButton(bi(
            "Convert supported archived claims", "转换归档中的完整主张"
        ))
        self.conversion_button.clicked.connect(self._convert_archive)
        history_layout.addWidget(self.conversion_button)
        self.tabs.addTab(history_tab, bi("Saved archives", "已保存归档"))
        self.tabs.currentChanged.connect(self._tab_changed)

        self.confirm = QCheckBox(bi(
            "I reviewed the preview and confirm retaining these original file bytes separately.",
            "我已复核预览，并确认单独保留这些原始文件字节。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        layout.addWidget(self.confirm)
        layout.addWidget(_label(bi(
            "Archives are unencrypted local copies in reports/legacy_archives and remain "
            "after report regeneration. Saving does not change or validate their contents.",
            "归档是 reports/legacy_archives 中未加密的本地副本，重新生成报告后仍会保留。"
            "保存不会改写内容，也不表示内容已获验证。",
        )))
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh originals", "刷新原文件"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        self.preview_button = SecondaryButton(bi("Preview archive", "预览归档"))
        self.preview_button.clicked.connect(self._make_preview)
        actions.addWidget(self.preview_button)
        actions.addStretch()
        self.save_button = PrimaryButton(bi("Save separate archive", "保存独立归档"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        self.close_button = SecondaryButton(bi("Close", "关闭"))
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)
        self.refresh()

    def _update_buttons(self) -> None:
        if not hasattr(self, "save_button"):
            return
        ready = (self.inspection is not None and not self._stale
                 and any(file.present for file in self.inspection.files))
        self.preview_button.setEnabled(ready)
        valid = ready and self.preview is not None and self.tabs.currentIndex() == 2
        self.confirm.setEnabled(valid)
        self.save_button.setEnabled(valid and self.confirm.isChecked())

    def _tab_changed(self, _index: int) -> None:
        self.confirm.setChecked(False)
        self._update_buttons()

    def _set_originals(self, inspection) -> None:
        self.files.blockSignals(True)
        self.files.clear()
        self._current_files = inspection.files if inspection is not None else []
        for file in self._current_files:
            self.files.addItem(_file_label(file), file.label)
        self.files.blockSignals(False)
        self._show_original(self.files.currentIndex())

    def _show_original(self, index: int) -> None:
        self.original_text.clear()
        if 0 <= index < len(self._current_files):
            self.original_text.setPlainText(_file_text(self._current_files[index]))

    def refresh(self) -> None:
        self.preview = None
        self.confirm.setChecked(False)
        self.preview_text.clear()
        self.field_ledger.clear()
        self.diagnostics.clear()
        self.inspection = None
        try:
            if self.service is None:
                self.service = LegacyReportService(self.vault_dir)
            self.inspection = self.service.inspect(self.kind)
            self._stale = False
            lines = [
                bi("Detected format", "识别格式") + ": " + _format(self.inspection.format),
                bi("Original file snapshot", "原始文件快照") + ": " + self.inspection.source_digest,
                *(_file_label(file) for file in self.inspection.files),
                bi("Review notes", "复核说明"),
                *(bi(issue.message_en, issue.message_zh) for issue in self.inspection.issues),
            ]
            self.diagnostics.setPlainText("\n\n".join(lines))
            self.status.setText(bi(
                "Inspection only. Preview and explicitly confirm before saving an archive.",
                "当前仅进行检查。保存归档前请先预览并明确确认。",
            ))
        except _ERRORS:
            self._stale = True
            self.status.setText(bi(
                "The original files cannot be read safely. Nothing was changed or archived. "
                "Existing saved archives can still be reviewed when valid.",
                "无法安全读取原文件。应用未更改或归档任何内容；有效的已有归档仍可复核。",
            ))
        self._set_originals(self.inspection)
        self._load_history()
        self._update_buttons()

    def _failure(self) -> None:
        self._stale = True
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "No archive was saved. The original files changed or could not be verified. "
            "The displayed preview is now stale; refresh and preview again before confirming.",
            "归档未保存。原文件已变化或无法校验，当前显示的预览已失效。请刷新并重新预览后"
            "再确认。",
        ))
        self._update_buttons()

    def _make_preview(self) -> None:
        if not self.preview_button.isEnabled():
            return
        try:
            self.preview = self.service.preview_archive(
                self.kind, expected_digest=self.inspection.source_digest,
            )
        except _ERRORS:
            self._failure()
            return
        self._set_originals(self.preview)
        self.preview_text.setPlainText(_summary(self.preview))
        self.field_ledger.setPlainText(_ledger(self.preview))
        self.tabs.setCurrentIndex(2)
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "Preview ready. Read the original files and preservation notes before confirming.",
            "预览已就绪，请阅读原始文件与保留说明后再确认。",
        ))
        self._update_buttons()

    def _load_history(self, selected_id: str | None = None) -> None:
        self._saved = []
        self.history.clear()
        self.saved_files.clear()
        self.saved_text.clear()
        self._history_preview = None
        self._history_id = None
        try:
            if self.service is None:
                self.service = LegacyReportService(self.vault_dir)
            self._saved = self.service.list_archives(self.kind)
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "Saved archives cannot be verified. No unverified content is displayed.",
                "无法校验已保存归档，未显示未经校验的内容。",
            ))
            return
        for saved in self._saved:
            self.history.addItem(saved.created_at + " — " + saved.id)
        if not self._saved:
            self.saved_text.setPlainText(bi("No saved archives.", "尚无已保存归档。"))
        if selected_id is not None:
            for row, saved in enumerate(self._saved):
                if saved.id == selected_id:
                    self.history.setCurrentRow(row)
                    break

    def _open_archive(self, row: int) -> None:
        self.saved_files.clear()
        self.saved_text.clear()
        self._history_preview = None
        self._history_id = None
        if not 0 <= row < len(self._saved):
            return
        try:
            identifier = self._saved[row].id
            self._history_preview = self.service.read_archive(self.kind, identifier)
            self._history_id = identifier
            self.saved_files.addItem(bi("Archive review notes", "归档复核说明"), None)
            for file in self._history_preview.files:
                self.saved_files.addItem(_file_label(file), file.label)
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "This archive cannot be verified. No content was opened.",
                "无法校验此归档，未打开其中内容。",
            ))

    def _show_snapshot(self, index: int) -> None:
        self.saved_text.clear()
        if self._history_preview is None or not 0 <= index <= len(self._history_preview.files):
            return
        if index == 0:
            self.saved_text.setPlainText(
                _summary(self._history_preview) + "\n\n" + _ledger(self._history_preview)
            )
            return
        file = self._history_preview.files[index - 1]
        try:
            raw = self.service.read_snapshot(self.kind, self._history_id, file.label) \
                if file.present else None
            self.saved_text.setPlainText(_file_text(file, raw))
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "The archive snapshot cannot be verified. No unverified file content is shown.",
                "无法校验归档快照，未显示未经校验的文件内容。",
            ))

    def _save(self) -> None:
        if not self.save_button.isEnabled():
            return
        try:
            self.saved_archive = self.service.save_archive(
                self.preview, confirmed=self.confirm.isChecked(),
            )
        except _ERRORS:
            self._failure()
            return
        self.preview = None
        self.confirm.setChecked(False)
        self._load_history(self.saved_archive.id)
        self.tabs.setCurrentIndex(3)
        self.status.setText(bi(
            "Archive saved separately. Original files and the active report are unchanged. "
            "No conversion, activation or restoration occurred.",
            "归档已单独保存，原文件与当前报告未改变。未进行转换、启用或恢复。",
        ))
        self._update_buttons()

    def _convert_archive(self) -> None:
        from anti_dating_scam_desktop.legacy_conversion_dialog import LegacyConversionDialog

        LegacyConversionDialog(
            self.vault_dir, self.kind, self, archive_id=self._history_id,
        ).exec()
