"""Deliberate, version-bound selection of an original report or reviewed copy."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QVBoxLayout,
)

from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam.services.legacy_conversions import (
    LegacyConversionError,
    LegacyConversionService,
)
from anti_dating_scam.services.report_revisions import ReportRevisionError, ReportRevisionService
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


def active_report_label(report) -> str:
    if getattr(report, "target_kind", None) == "legacy_review_only":
        return bi("Current report: legacy review only; AI references disabled",
                  "当前报告：仅复核旧文件；已停用 AI 报告参考")
    if getattr(report, "target_kind", None) == "legacy_conversion":
        return bi("Current report: partial legacy conversion", "当前报告：旧格式部分转换") \
            + " " + report.conversion_id[:12]
    if report is None or report.selection_version == "0" * 64:
        return bi("Current report: original (default)", "当前报告：原报告（默认）")
    if report.revision_id is None:
        return bi("Current report: explicitly selected original", "当前报告：已明确选择的原报告")
    return bi("Current report: reviewed copy", "当前报告：复核副本") + " " + report.revision_id[:12]


def active_report_error() -> str:
    return bi(
        "The selected report cannot be verified. No report is displayed. Use Select active "
        "report to review the original or another copy. No automatic fallback occurred.",
        "无法校验已选报告，当前不显示报告。请通过「选择当前报告」复核原报告或其他副本。"
        "应用未自动切换到其他报告。",
    )


def review_only_label() -> str:
    return bi(
        "Legacy review only: no report is active and report references to AI are disabled. "
        "Use Review legacy files for original content, or deliberately select a valid report.",
        "当前仅复核旧文件：没有已启用报告，AI 报告参考已停用。可通过「复核旧版文件」"
        "查看原内容，或明确选择一份有效报告。",
    )


def show_verified_report(parent, title: str, text: str) -> None:
    """Show an already verified snapshot without links, caches or free path opening."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(940, 700)
    layout = QVBoxLayout(dialog)
    reader = QPlainTextEdit()
    reader.setReadOnly(True)
    reader.setPlainText(text)
    layout.addWidget(reader)
    close = SecondaryButton(bi("Close", "关闭"))
    close.clicked.connect(dialog.reject)
    layout.addWidget(close)
    dialog.exec()


class ReportSelectionDialog(QDialog):
    def __init__(self, vault_dir: Path, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.vault_dir = Path(vault_dir)
        self.kind = kind
        self.service = None
        self.selection = None
        self.preview = None
        self._needs_refresh = False
        self.setWindowTitle(bi("Select active report", "选择当前报告"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Preview the exact report before choosing it. This changes the report used by "
            "the app without overwriting original files or cards. A selected portrait can be "
            "used as unverified AI interview context, never as your original testimony. "
            "External sending still requires disclosure review. No AI request is made here.",
            "请先预览实际报告，再选择使用。此操作改变应用使用的报告，不会覆盖原始文件或"
            "卡片。已选画像可用于 AI 访谈中的未验证参考，但不能当作你的原始陈述。"
            "对外发送仍需披露审核。此窗口不会发起 AI 请求。",
        )))
        self.current = _label("")
        layout.addWidget(self.current)
        self.choices = QListWidget()
        self.choices.setMaximumHeight(110)
        self.choices.currentRowChanged.connect(self._choice_changed)
        layout.addWidget(self.choices)
        self.reader = QPlainTextEdit()
        self.reader.setReadOnly(True)
        layout.addWidget(self.reader, 1)
        self.confirm = QCheckBox(bi(
            "I reviewed this preview and confirm using this report in the app.",
            "我已复核此预览，并确认在应用中使用这份报告。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        layout.addWidget(self.confirm)
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh choices", "刷新可选报告"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        self.preview_button = SecondaryButton(bi("Preview selected report", "预览所选报告"))
        self.preview_button.clicked.connect(self._make_preview)
        actions.addWidget(self.preview_button)
        actions.addStretch()
        self.use_button = PrimaryButton(bi("Use this report", "使用这份报告"))
        self.use_button.setAutoDefault(False)
        self.use_button.clicked.connect(self._apply)
        actions.addWidget(self.use_button)
        close = SecondaryButton(bi("Cancel", "取消"))
        close.clicked.connect(self.reject)
        self.cancel_button = close
        actions.addWidget(close)
        layout.addLayout(actions)
        self.refresh()

    def _update_buttons(self) -> None:
        if not hasattr(self, "use_button"):
            return
        ready = (self.selection is not None and self.choices.currentRow() >= 0
                 and not self._needs_refresh)
        self.preview_button.setEnabled(ready)
        valid = ready and self.preview is not None
        self.confirm.setEnabled(valid)
        self.use_button.setEnabled(valid and self.confirm.isChecked())

    def _choice_changed(self, _row: int) -> None:
        self.preview = None
        self.reader.clear()
        if hasattr(self, "confirm"):
            self.confirm.setChecked(False)
            item = self.choices.currentItem()
            choice = item.data(Qt.ItemDataRole.UserRole) if item else None
            review_only = isinstance(choice, (tuple, list)) and choice[0] == "review_only"
            self.confirm.setText(bi(
                "I reviewed this preview and confirm disabling active report references.",
                "我已复核此预览，并确认停用当前报告参考。",
            ) if review_only else bi(
                "I reviewed this preview and confirm using this report in the app.",
                "我已复核此预览，并确认在应用中使用这份报告。",
            ))
            self.use_button.setText(bi(
                "Disable report references", "停用报告参考",
            ) if review_only else bi("Use this report", "使用这份报告"))
            if not self._needs_refresh:
                self.status.setText(bi(
                    "Preview your choice before confirming. Nothing has changed.",
                    "请先预览再确认，当前选择尚未改变。",
                ))
        self._update_buttons()

    def refresh(self) -> None:
        old_item = self.choices.currentItem()
        had_choice = old_item is not None
        old_id = old_item.data(Qt.ItemDataRole.UserRole) if old_item else None
        self.choices.clear()
        self.selection = None
        self.preview = None
        self.confirm.setChecked(False)
        try:
            if self.service is None:
                self.service = ActiveReportService(self.vault_dir)
            self.selection = self.service.get_selection(self.kind)
        except (ActiveReportError, OSError, ValueError):
            self._needs_refresh = True
            self.current.setText(bi("Selection history unavailable", "选择记录不可用"))
            self.status.setText(bi(
                "The selection history cannot be verified and needs repair. Nothing was "
                "changed or reset. Existing reports remain on disk.",
                "无法校验选择历史，需要修复。应用未更改或重置选择，现有报告仍保留在磁盘中。",
            ))
            self._update_buttons()
            return
        self._needs_refresh = False
        self.current.setText(active_report_label(self.selection))
        original = QListWidgetItem(bi("Original report / restore original", "原报告 / 恢复原报告"))
        original.setData(Qt.ItemDataRole.UserRole, None)
        self.choices.addItem(original)
        self.status.setText(bi(
            "Choose a report, then preview it. Restoring the original also requires confirmation.",
            "请选择报告并预览。恢复原报告也需要明确确认。",
        ))
        try:
            records = ReportRevisionService(self.vault_dir).list_revisions(self.kind)
            for record in records:
                item = QListWidgetItem(
                    bi("Reviewed copy", "复核副本") + " — " + record.created_at
                    + " — " + record.id[:12]
                )
                item.setData(Qt.ItemDataRole.UserRole, record.id)
                self.choices.addItem(item)
        except (ReportRevisionError, OSError, ValueError):
            self.status.setText(bi(
                "Reviewed copies could not be verified. You can still preview the original "
                "to restore it; the selected report has not changed.",
                "无法校验复核副本。仍可预览原报告并确认恢复；当前选择尚未改变。",
            ))
        try:
            conversions = LegacyConversionService(self.vault_dir).list_conversions(self.kind)
            for record in conversions:
                item = QListWidgetItem(
                    bi("Partial legacy conversion", "旧格式部分转换") + " — "
                    + record.created_at + " — " + record.id[:12]
                )
                item.setData(Qt.ItemDataRole.UserRole, ("conversion", record.id))
                self.choices.addItem(item)
        except (LegacyConversionError, OSError, ValueError):
            self.status.setText(bi(
                "Converted copies could not be verified. Other choices remain available; "
                "no selection was changed.",
                "无法校验转换副本；其他选项仍可使用，当前选择未改变。",
            ))
        review_only = QListWidgetItem(bi(
            "Legacy review only / disable active report references",
            "仅复核旧文件 / 停用当前报告参考",
        ))
        review_only.setData(Qt.ItemDataRole.UserRole, ("review_only", None))
        self.choices.addItem(review_only)
        if had_choice:
            for row in range(self.choices.count()):
                if self.choices.item(row).data(Qt.ItemDataRole.UserRole) == old_id:
                    self.choices.setCurrentRow(row)
                    break
        self._update_buttons()

    def _failed(self) -> None:
        self._needs_refresh = True
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "The report or selection changed, or could not be verified. Nothing was selected. "
            "Your choice is retained; refresh and preview again before confirming. Copies from "
            "an older source cannot be activated. Select a valid report or choose legacy "
            "review only to disable active report references.",
            "报告或选择记录已变化，或无法校验。未应用新选择，已保留你的选择意向。"
            "请刷新并重新预览后再确认。基于旧版源报告的副本无法启用；请选择有效报告，或"
            "选择仅复核旧文件以停用当前报告参考。",
        ))
        self._update_buttons()

    def _make_preview(self) -> None:
        if not self.preview_button.isEnabled():
            return
        try:
            choice = self.choices.currentItem().data(Qt.ItemDataRole.UserRole)
            expected = {"expected_selection_version": self.selection.selection_version}
            if isinstance(choice, (tuple, list)) and choice[0] == "conversion":
                self.preview = self.service.preview_conversion_selection(
                    self.kind, choice[1], **expected,
                )
            elif isinstance(choice, (tuple, list)) and choice[0] == "review_only":
                self.preview = self.service.preview_legacy_review_only(self.kind, **expected)
            else:
                self.preview = self.service.preview_selection(self.kind, choice, **expected)
        except (ActiveReportError, OSError, ValueError):
            self._failed()
            return
        self.reader.setPlainText(self.preview.detailed_markdown or self.preview.markdown)
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "Preview ready. The active report has not changed.",
            "预览已就绪，当前使用的报告尚未改变。",
        ))
        self._update_buttons()

    def _apply(self) -> None:
        if not self.use_button.isEnabled():
            return
        try:
            choice = self.choices.currentItem().data(Qt.ItemDataRole.UserRole)
            if isinstance(choice, (tuple, list)) and choice[0] == "conversion":
                self.service.select_conversion(self.preview, confirmed=self.confirm.isChecked())
            elif isinstance(choice, (tuple, list)) and choice[0] == "review_only":
                self.service.select_review_only(self.preview, confirmed=self.confirm.isChecked())
            else:
                self.service.select(self.preview, confirmed=self.confirm.isChecked())
        except (ActiveReportError, OSError, ValueError):
            self._failed()
            return
        self.accept()
