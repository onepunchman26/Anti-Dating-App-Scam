"""Explicit, local-only creation and verified reading of separate reviewed copies."""

from __future__ import annotations

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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.services.report_review import ReportReviewError, ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionError, ReportRevisionService
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton

_ERRORS = (ReportReviewError, ReportRevisionError, OSError, ValueError)


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


def _reader() -> QPlainTextEdit:
    reader = QPlainTextEdit()
    reader.setReadOnly(True)
    return reader


class ReportRevisionDialog(QDialog):
    """Selections and previews are transient; only Save invokes persistence."""

    def __init__(self, vault_dir: Path, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.vault_dir = Path(vault_dir)
        self.kind = kind
        self.reviews = None
        self.service = None
        self.document = None
        self.preview = None
        self._stale = False
        self._loading = False
        self._records = {}
        self._saved = []
        self._unavailable = {}
        self.setWindowTitle(bi("Create reviewed copy", "生成复核副本"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Withdraw disputed claims from the original source report using its saved corrections, "
            "even when another copy is selected in the app. "
            "Withdrawal previews run no AI and add no replacement facts. "
            "The separate plaintext copy "
            "does not replace the active report or change cards, AI inputs, or correction "
            "notes. Saving also retains full original source snapshots and selected "
            "correction records as plaintext. Other content is not reanalyzed and still "
            "needs human review.",
            "从原始源报告已保存的更正中选择要撤回的争议主张，即使应用当前已选择其他副本。"
            "撤回预览不调用 AI，也不添加替代"
            "事实。生成的独立明文副本不会替换当前报告，也不会改变卡片、AI 输入或更正记录。"
            "保存时还会保留完整原始源文件快照及所选更正记录的明文副本。其他内容不会重新"
            "分析，仍需人工复核。",
        )))
        self.scope = _label(bi(
            "Portrait copies also omit all consistency findings, headlines and summaries.",
            "画像副本还会移除所有一致性分析记录、概括标题及摘要。",
        ) if kind == "self_portrait" else bi(
            "Criteria copies also omit all fictional candidate profiles.",
            "择偶标准副本还会移除所有虚构候选人档案。",
        ))
        layout.addWidget(self.scope)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        choices = QWidget()
        form = QVBoxLayout(choices)
        form.addWidget(_label(bi(
            "Choose saved corrections. Each selected original claim will be withdrawn.",
            "选择已保存的更正；每条选中更正所对应的原始主张将被撤回。",
        )))
        self.replacement_button = SecondaryButton(bi(
            "Rewrite one disputed claim", "改写一条争议主张",
        ))
        self.replacement_button.clicked.connect(self._create_replacement)
        form.addWidget(self.replacement_button)
        self.ai_replacement_button = SecondaryButton(bi(
            "Ask local AI about one disputed claim", "请本地 AI 重新解释一条争议主张",
        ))
        self.ai_replacement_button.clicked.connect(self._create_ai_replacement)
        form.addWidget(self.ai_replacement_button)
        self.full_regeneration_button = SecondaryButton(bi(
            "Regenerate a full report from original excerpts", "根据原始摘录重新生成完整报告",
        ))
        self.full_regeneration_button.clicked.connect(self._create_full_regeneration)
        form.addWidget(self.full_regeneration_button)
        self.corrections = QListWidget()
        self.corrections.itemChanged.connect(self._selection_changed)
        self.corrections.currentRowChanged.connect(self._show_correction)
        form.addWidget(self.corrections, 1)
        self.correction_details = _reader()
        form.addWidget(self.correction_details, 1)
        self.unavailable = _reader()
        self.unavailable.setMaximumHeight(80)
        self.unavailable.hide()
        form.addWidget(self.unavailable)
        self.tabs.addTab(choices, bi("Choose withdrawals", "选择撤回内容"))

        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.preview_status = _label(bi("No preview yet.", "尚未生成预览。"))
        preview_layout.addWidget(self.preview_status)
        self.removed = _reader()
        self.removed.setMaximumHeight(95)
        preview_layout.addWidget(self.removed)
        self.preview_text = _reader()
        preview_layout.addWidget(self.preview_text, 1)
        self.tabs.addTab(preview_tab, bi("Full bilingual preview", "完整双语预览"))

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(_label(bi(
            "Saved copies are verified before display. They can belong to earlier report "
            "versions and remain separate from the current report.",
            "已保存副本会在显示前经过完整性校验。它们可能属于较早的报告版本，始终与当前"
            "报告分开保存。",
        )))
        self.history = QListWidget()
        self.history.setMaximumHeight(100)
        self.history.currentRowChanged.connect(self._open_saved)
        history_layout.addWidget(self.history)
        self.saved_text = _reader()
        history_layout.addWidget(self.saved_text, 1)
        self.tabs.addTab(history_tab, bi("Saved copies", "已保存副本"))

        self.confirm = QCheckBox(bi(
            "Confirm saving the copy, original snapshots and selected correction records.",
            "确认保存此复核副本、原始源文件快照及所选更正记录。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        layout.addWidget(self.confirm)
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh", "刷新"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        self.selection_button = SecondaryButton(bi("Select active report", "选择当前报告"))
        self.selection_button.clicked.connect(self._select_active_report)
        actions.addWidget(self.selection_button)
        self.preview_button = SecondaryButton(bi(
            "Preview selected withdrawals", "预览所选撤回内容"
        ))
        self.preview_button.clicked.connect(self._make_preview)
        actions.addWidget(self.preview_button)
        actions.addStretch()
        self.save_button = PrimaryButton(bi("Save reviewed copy", "保存复核副本"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        self.close_button = SecondaryButton(bi("Close", "关闭"))
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.refresh()

    def _create_replacement(self) -> None:
        from anti_dating_scam_desktop.report_replacement_dialog import ReportReplacementDialog

        self.confirm.setChecked(False)
        dialog = ReportReplacementDialog(self.vault_dir, self.kind, self)
        dialog.exec()
        if dialog.saved_revision is not None:
            history_ok = self._load_history(dialog.saved_revision.id)
            self.status.setText(bi(
                "Proposed copy saved separately; find it under Saved copies. Withdrawal "
                "selections and the active report are unchanged.",
                "提议副本已单独保存，可在「已保存副本」中查看。撤回选择及当前报告未改变。",
            ) if history_ok else bi(
                "Proposed copy was saved, but history could not refresh. Reopen this dialog "
                "to retry. Withdrawal selections and the active report are unchanged.",
                "提议副本已保存，但历史记录刷新失败，请重新打开此窗口重试。撤回选择及当前"
                "报告未改变。",
            ))

    def _select_active_report(self) -> None:
        from anti_dating_scam_desktop.report_selection_dialog import ReportSelectionDialog

        ReportSelectionDialog(self.vault_dir, self.kind, self).exec()

    def _create_ai_replacement(self) -> None:
        from anti_dating_scam_desktop.report_ai_replacement_dialog import ReportAIReplacementDialog

        self.confirm.setChecked(False)
        dialog = ReportAIReplacementDialog(self.vault_dir, self.kind, self)
        dialog.exec()
        if dialog.saved_revision is not None:
            history_ok = self._load_history(dialog.saved_revision.id)
            self.status.setText(bi(
                "AI-assisted copy saved separately; find it under Saved copies. It has not "
                "been activated. Withdrawal selections are unchanged.",
                "AI 辅助副本已单独保存，可在「已保存副本」中查看。副本未启用，撤回选择未改变。",
            ) if history_ok else bi(
                "AI-assisted copy saved, but history could not refresh. Reopen this dialog "
                "to retry. The active report and withdrawal selections are unchanged.",
                "AI 辅助副本已保存，但历史记录刷新失败。请重新打开此窗口重试。"
                "当前报告及撤回选择未改变。",
            ))

    def _create_full_regeneration(self) -> None:
        from anti_dating_scam_desktop.report_full_regeneration_dialog import (
            ReportFullRegenerationDialog,
        )

        self.confirm.setChecked(False)
        dialog = ReportFullRegenerationDialog(self.vault_dir, self.kind, self)
        dialog.exec()
        if dialog.saved_revision is not None:
            history_ok = self._load_history(dialog.saved_revision.id)
            self.status.setText(bi(
                "Regenerated copy saved separately; find it under Saved copies. It has not "
                "been activated. Withdrawal selections are unchanged.",
                "重新生成的副本已单独保存，可在「已保存副本」中查看。副本未启用，撤回选择未改变。",
            ) if history_ok else bi(
                "Regenerated copy saved, but history could not refresh. Reopen this dialog "
                "to retry. The active report and withdrawal selections are unchanged.",
                "重新生成的副本已保存，但历史记录刷新失败。请重新打开此窗口重试。"
                "当前报告及撤回选择未改变。",
            ))

    def _tab_changed(self, _index: int) -> None:
        self.confirm.setChecked(False)
        self._update_buttons()

    def selected_ids(self) -> list[str]:
        return [
            self.corrections.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.corrections.count())
            if self.corrections.item(i).checkState() == Qt.CheckState.Checked
        ]

    def _update_buttons(self) -> None:
        if not hasattr(self, "save_button"):
            return
        selected = self.selected_ids()
        ready = self.document is not None and not self._stale and bool(selected)
        self.preview_button.setEnabled(ready)
        valid_preview = bool(
            ready and self.preview is not None
            and set(selected) == set(self.preview.correction_ids)
            and self.tabs.currentIndex() == 1
        )
        self.confirm.setEnabled(valid_preview)
        self.save_button.setEnabled(valid_preview and self.confirm.isChecked())

    def _invalidate_preview(self) -> None:
        self.preview = None
        self.confirm.setChecked(False)
        self.removed.clear()
        self.preview_text.clear()
        self.preview_status.setText(bi(
            "Selection changed or refreshed. Generate a new preview before saving.",
            "选择已变更或刷新。保存前请重新生成预览。",
        ))

    def _selection_changed(self, _item=None) -> None:
        if self._loading:
            return
        self._invalidate_preview()
        if not self._stale:
            self.status.setText(bi(
                "Selection is not saved. Preview it, review the full copy, then confirm.",
                "选择尚未保存。请先生成预览，复核完整副本后再确认。",
            ))
        self._update_buttons()

    def _show_correction(self, row: int) -> None:
        if row < 0 or self._loading:
            self.correction_details.clear()
            return
        record = self._records[self.corrections.item(row).data(Qt.ItemDataRole.UserRole)]
        self.correction_details.setPlainText("\n\n".join([
            bi("Original claim to withdraw", "拟撤回的原始主张") + ": " + record.original_claim,
            bi("Saved correction (not a replacement fact)", "已保存的更正（不是替代事实）")
            + ": " + record.correction_text,
            bi("Reason", "理由") + ": " + record.reason,
            bi("Saved at", "保存时间") + ": " + record.created_at,
        ]))

    def refresh(self) -> None:
        selected = set(self.selected_ids()) | set(self._unavailable)
        previous = {**self._unavailable, **self._records}
        self._invalidate_preview()
        self._loading = True
        self.document = None
        self.corrections.clear()
        self.correction_details.clear()
        self._records = {}
        try:
            if self.service is None:
                self.service = ReportRevisionService(self.vault_dir)
            if self.reviews is None:
                self.reviews = ReportReviewService(self.vault_dir)
            document = self.reviews.inspect(self.kind)
            records = self.reviews.list_corrections(self.kind, document.report_digest)
            self.document = document
            self._records = {record.id: record for record in records}
            for record in records:
                item = QListWidgetItem(" ".join(record.original_claim.split())[:150])
                item.setData(Qt.ItemDataRole.UserRole, record.id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked if record.id in selected else Qt.CheckState.Unchecked
                )
                self.corrections.addItem(item)
            self._stale = False
            self.status.setText(bi(
                "Review your selections and generate a new preview.",
                "请核对选择并生成新的预览。",
            ) if records else bi(
                "No saved corrections apply to this original source version. Save a correction "
                "in Review original evidence & corrections first. Saved copies remain available.",
                "此原始源报告版本没有已保存的更正。请先在「复核原报告证据与更正」中保存更正。"
                "已有复核副本仍可查看。",
            ))
        except _ERRORS:
            self._stale = True
            self.status.setText(bi(
                "The original source report or corrections cannot be verified. Regenerate a valid "
                "structured report if needed, then refresh. Existing files remain unchanged.",
                "无法校验原始源报告或更正记录。必要时请重新生成有效的结构化报告，再刷新。"
                "现有文件未改变。",
            ))
        finally:
            self._loading = False
        self._unavailable = {
            key: previous[key] for key in selected - set(self._records) if key in previous
        }
        self.unavailable.setPlainText(bi(
            "Previous selections retained for reference only; they are not eligible for "
            "this original source version:\n",
            "以下先前选择仅为参考而保留，不能用于此原始源报告版本：\n",
        ) + "\n".join(record.original_claim for record in self._unavailable.values()))
        self.unavailable.setVisible(bool(self._unavailable))
        if self.corrections.count():
            self.corrections.setCurrentRow(0)
        self._load_history()
        self._update_buttons()

    def _failure(self) -> None:
        self._stale = True
        self.confirm.setChecked(False)
        self.preview_status.setText(bi(
            "This preview is not valid for saving. Refresh and create a new preview.",
            "此预览当前不能保存。请刷新并重新生成预览。",
        ))
        self.status.setText(bi(
            "No copy was saved. Source files may have changed or be invalid. Your selection "
            "is preserved; refresh and review it again. A complete valid bilingual "
            "localization file is required for the preview.",
            "副本未保存。源文件可能已变化或无效。已保留选择，请刷新并重新复核。"
            "预览需要完整有效的双语映射文件。",
        ))
        self._update_buttons()

    def _make_preview(self) -> None:
        if not self.preview_button.isEnabled():
            return
        try:
            preview = self.service.preview_withdrawals(
                self.kind, self.selected_ids(), expected_digest=self.document.report_digest,
            )
        except _ERRORS:
            self._failure()
            return
        self.preview = preview
        self.confirm.setChecked(False)
        self.removed.setPlainText(bi("Claims to withdraw", "将撤回的主张") + "\n" + "\n".join(
            f"{claim.path}: {claim.claim}" for claim in preview.removed_claims
        ))
        self.preview_text.setPlainText(preview.detailed_markdown or preview.markdown)
        self.preview_status.setText(bi(
            "Unsaved full bilingual copy. Read the withdrawals and the report before confirming.",
            "尚未保存的完整双语副本。请先阅读撤回列表与报告，再确认。",
        ))
        self.status.setText(bi("Preview ready; nothing has been saved.", "预览已就绪，尚未保存。"))
        self.tabs.setCurrentIndex(1)
        self._update_buttons()

    def _load_history(self, selected_id: str | None = None) -> bool:
        self._saved = []
        self.history.clear()
        self.saved_text.clear()
        try:
            if self.service is None:
                self.service = ReportRevisionService(self.vault_dir)
            self._saved = self.service.list_revisions(self.kind)
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "Saved copies cannot be verified. No unverified content is displayed.",
                "无法校验已保存副本，未显示任何未经校验的内容。",
            ))
            return False
        for record in self._saved:
            self.history.addItem(record.created_at + " — " + record.id)
        if not self._saved:
            self.saved_text.setPlainText(bi("No saved reviewed copies.", "尚无已保存的复核副本。"))
        if selected_id:
            for row, record in enumerate(self._saved):
                if record.id == selected_id:
                    self.history.setCurrentRow(row)
                    break
        return True

    def _open_saved(self, row: int) -> None:
        self.saved_text.clear()
        if row < 0 or row >= len(self._saved):
            return
        try:
            saved = self.service.read_revision(self.kind, self._saved[row].id)
        except _ERRORS:
            self.saved_text.setPlainText(bi(
                "This saved copy cannot be verified. Its content has not been opened.",
                "无法校验此副本，未打开其内容。",
            ))
            return
        self.saved_text.setPlainText(saved.detailed_markdown or saved.markdown)

    def _save(self) -> None:
        if not self.save_button.isEnabled():
            return
        try:
            saved = self.service.save_withdrawals(self.preview, confirmed=self.confirm.isChecked())
        except _ERRORS:
            self._failure()
            return
        self.preview = None
        self.confirm.setChecked(False)
        self.preview_status.setText(bi(
            "This preview has been saved separately. Create a new preview before another save.",
            "此预览已单独保存。再次保存前请重新生成预览。",
        ))
        history_ok = self._load_history(saved.id)
        self.tabs.setCurrentIndex(2)
        self.status.setText(bi(
            "Reviewed copy saved separately. The active report and corrections are unchanged.",
            "复核副本已单独保存。当前报告及更正记录未改变。",
        ) + ("" if history_ok else " " + bi(
            "Saved history could not be refreshed; reopen this dialog to retry.",
            "已保存历史刷新失败，请重新打开此窗口重试。",
        )))
        self._update_buttons()
