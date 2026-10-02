"""Preview and save only already-supported legacy claims; selection stays separate."""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QListWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.services.legacy_conversions import (
    LegacyConversionError,
    LegacyConversionService,
)
from anti_dating_scam.services.legacy_reports import LegacyReportError, LegacyReportService
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.legacy_report_dialog import _label, _reader
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton

_ERRORS = (LegacyConversionError, LegacyReportError, OSError, ValueError)


def _review(preview) -> str:
    heading = bi(
        f"Supported claims copied: {preview.converted_count}. Other content stays archived.",
        f"已复制完整受支持主张：{preview.converted_count} 条。其他内容仍保留在归档中。",
    )
    issues = "\n\n".join(bi(issue.message_en, issue.message_zh) for issue in preview.issues)
    ledger = "\n\n".join(
        f"{field.file_label} {field.pointer}\n" + bi(field.reason_en, field.reason_zh)
        for field in preview.field_ledger
    )
    return heading + "\n\n" + issues + "\n\n" + ledger


class LegacyConversionDialog(QDialog):
    """No model calls, inferred metadata, original writes or automatic activation."""

    def __init__(self, vault_dir: Path, kind: str, parent=None, *, archive_id=None) -> None:
        super().__init__(parent)
        self.vault_dir = Path(vault_dir)
        self.kind = kind
        self.service = None
        self.archive_service = None
        self.preview = None
        self.saved_conversion = None
        self._archives = []
        self._saved = []
        self._stale = False
        self.setWindowTitle(bi("Convert supported archived claims", "转换归档中的完整主张"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Choose an archive and review exactly what can be copied. Only claims with "
            "complete existing evidence, uncertainty and English/Chinese text qualify. "
            "Unsupported fields remain in the archive. No evidence or translations are "
            "invented. Saving does not activate this read-only partial report; correction "
            "tools still target the original generated report. No AI runs.",
            "选择归档并复核可以复制的内容。只有已有证据、不确定性及完整中英文内容的主张"
            "符合条件；不支持的字段仍保留在归档中。应用不会编造证据或翻译。另存部分报告"
            "不会自动启用。转换副本只供阅读，更正工具仍针对原始生成报告。此处不调用 AI。",
        )))
        self.archives = QListWidget()
        self.archives.setMaximumHeight(85)
        self.archives.currentRowChanged.connect(self._archive_changed)
        layout.addWidget(self.archives)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.review_text = _reader()
        self.tabs.addTab(self.review_text, bi("Copied and archived fields", "复制与归档字段"))
        self.report_text = _reader()
        self.tabs.addTab(self.report_text, bi("Partial report preview", "部分报告预览"))
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history = QListWidget()
        self.history.setMaximumHeight(75)
        self.history.currentRowChanged.connect(self._open_saved)
        history_layout.addWidget(self.history)
        self.saved_text = _reader()
        history_layout.addWidget(self.saved_text, 1)
        self.tabs.addTab(history_tab, bi("Saved conversions", "已保存转换"))
        self.tabs.currentChanged.connect(self._tab_changed)
        self.confirm = QCheckBox(bi(
            "I reviewed the copied claims and omissions and confirm saving this partial report.",
            "我已复核复制的主张与未转换内容，确认保存这份部分报告。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        layout.addWidget(self.confirm)
        layout.addWidget(_label(bi(
            "Originals, archives, cards and the active selection remain unchanged. Copies are "
            "unencrypted local files. To use a saved copy, select and confirm it separately.",
            "原文件、归档、卡片及当前选择保持不变。副本是未加密的本地文件。使用已保存副本"
            "需要另行选择与确认。",
        )))
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh archives", "刷新归档"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        self.preview_button = SecondaryButton(bi("Preview conversion", "预览转换"))
        self.preview_button.clicked.connect(self._make_preview)
        actions.addWidget(self.preview_button)
        self.selection_button = SecondaryButton(bi("Select active report", "选择当前报告"))
        self.selection_button.clicked.connect(self._select_report)
        actions.addWidget(self.selection_button)
        actions.addStretch()
        self.save_button = PrimaryButton(bi("Save separate copy", "保存独立副本"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        self.close_button = SecondaryButton(bi("Close", "关闭"))
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)
        self.refresh(archive_id)

    def _update_buttons(self) -> None:
        if not hasattr(self, "save_button"):
            return
        self.preview_button.setEnabled(
            self.service is not None and self.archives.currentRow() >= 0 and not self._stale
        )
        valid = (self.preview is not None and self.preview.eligible and not self._stale
                 and self.tabs.currentIndex() != 2)
        self.confirm.setEnabled(valid)
        self.save_button.setEnabled(valid and self.confirm.isChecked())

    def _archive_changed(self, _row: int) -> None:
        self.preview = None
        if hasattr(self, "confirm"):
            self.confirm.setChecked(False)
            self.review_text.clear()
            self.report_text.clear()
        self._update_buttons()

    def _tab_changed(self, _index: int) -> None:
        self.confirm.setChecked(False)
        self._update_buttons()

    def refresh(self, selected_id=None) -> None:
        if not isinstance(selected_id, str):
            row = self.archives.currentRow()
            selected_id = self._archives[row].id if 0 <= row < len(self._archives) else None
        self.preview = None
        self.confirm.setChecked(False)
        self.archives.clear()
        self._archives = []
        self.review_text.clear()
        self.report_text.clear()
        try:
            self.service = LegacyConversionService(self.vault_dir)
            self.archive_service = LegacyReportService(self.vault_dir)
            self._archives = self.archive_service.list_archives(self.kind)
            self._stale = False
            for archive in self._archives:
                self.archives.addItem(archive.created_at + " — " + archive.id[:12])
            for row, archive in enumerate(self._archives):
                if archive.id == selected_id:
                    self.archives.setCurrentRow(row)
                    break
            self.status.setText(bi(
                "Choose an archive and preview. Create an archive in Review legacy files if "
                "none is listed. Its source must still match the original files.",
                "请选择归档并预览。列表为空时，可在「复核旧版文件」中创建归档；归档的来源"
                "必须仍与原文件一致。",
            ))
        except _ERRORS:
            self._stale = True
            self.status.setText(bi(
                "Archives could not be verified. Nothing was converted or changed.",
                "无法校验归档，未转换或更改任何内容。",
            ))
        self._load_history()
        self._update_buttons()

    def _failed(self) -> None:
        self._stale = True
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "The archive or source changed, or could not be verified. Nothing was saved. "
            "Your displayed preview is stale; refresh and preview again before confirming.",
            "归档或来源已变化，或无法校验，未保存任何内容。当前预览已失效；请刷新并重新"
            "预览后再确认。",
        ))
        self._update_buttons()

    def _make_preview(self) -> None:
        if not self.preview_button.isEnabled():
            return
        try:
            self.preview = self.service.preview_conversion(
                self.kind, self._archives[self.archives.currentRow()].id,
            )
        except _ERRORS:
            self._failed()
            return
        self.review_text.setPlainText(_review(self.preview))
        self.report_text.setPlainText(
            self.preview.detailed_markdown or self.preview.markdown or bi(
                "No current report can be created from this archive.",
                "无法从此归档创建当前格式报告。",
            )
        )
        self.tabs.setCurrentIndex(0)
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "Review copied claims, all omissions and the complete partial report before saving.",
            "保存前请复核复制的主张、全部未转换内容及完整的部分报告。",
        ) if self.preview.eligible else bi(
            "No complete supported claim can be converted. Saving is disabled. Keep this "
            "archive for review; create a new report from original user material when ready.",
            "没有完整受支持主张可转换，无法保存转换。请保留归档供复核，准备好后可基于"
            "用户原始材料重新生成报告。",
        ))
        self._update_buttons()

    def _load_history(self, selected_id=None) -> None:
        self._saved = []
        self.history.clear()
        self.saved_text.clear()
        try:
            if self.service is None:
                self.service = LegacyConversionService(self.vault_dir)
            self._saved = self.service.list_conversions(self.kind)
            for record in self._saved:
                self.history.addItem(record.created_at + " — " + record.id[:12])
            if not self._saved:
                self.saved_text.setPlainText(bi("No saved conversions.", "尚无已保存转换。"))
            for row, record in enumerate(self._saved):
                if record.id == selected_id:
                    self.history.setCurrentRow(row)
                    break
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "Saved conversions cannot be verified. No unverified content is displayed.",
                "无法校验已保存转换，未显示未经校验的内容。",
            ))

    def _open_saved(self, row: int) -> None:
        self.saved_text.clear()
        if not 0 <= row < len(self._saved):
            return
        try:
            preview = self.service.read_conversion(self.kind, self._saved[row].id)
            self.saved_text.setPlainText(
                _review(preview) + "\n\n" + (preview.detailed_markdown or preview.markdown)
            )
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "This conversion cannot be verified. No content was opened.",
                "无法校验此转换，未打开其中内容。",
            ))

    def _save(self) -> None:
        if not self.save_button.isEnabled():
            return
        try:
            self.saved_conversion = self.service.save_conversion(
                self.preview, confirmed=self.confirm.isChecked(),
            )
        except _ERRORS:
            self._failed()
            return
        self.preview = None
        self.confirm.setChecked(False)
        self._load_history(self.saved_conversion.id)
        self.tabs.setCurrentIndex(2)
        self.status.setText(bi(
            "Partial report saved separately. It has not been activated. To use it, open "
            "Select active report, preview the saved copy and confirm that separate choice.",
            "部分报告已单独保存，尚未启用。使用前请打开「选择当前报告」，预览已保存副本"
            "并另行确认选择。",
        ))
        self._update_buttons()

    def _select_report(self) -> None:
        from anti_dating_scam_desktop.report_selection_dialog import ReportSelectionDialog

        ReportSelectionDialog(self.vault_dir, self.kind, self).exec()
