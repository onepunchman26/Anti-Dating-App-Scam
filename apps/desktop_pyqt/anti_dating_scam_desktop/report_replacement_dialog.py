"""One explicitly proposed interpretation in a separate, evidence-bound reviewed copy."""

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
from anti_dating_scam.services.report_revisions import (
    ReplacementProposal,
    ReportRevisionError,
    ReportRevisionService,
)
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton

_ERRORS = (ReportReviewError, ReportRevisionError, OSError, ValueError)


def _label(text: str) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    return widget


def _reader() -> QPlainTextEdit:
    widget = QPlainTextEdit()
    widget.setReadOnly(True)
    return widget


class ReportReplacementDialog(QDialog):
    """Transient drafts are never evidence, source edits or an active-report selection."""

    def __init__(self, vault_dir: Path, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.vault_dir = Path(vault_dir)
        self.kind = kind
        self.service = None
        self.reviews = None
        self.document = None
        self.preview = None
        self.saved_revision = None
        self._records = {}
        self._previous_record = None
        self._loading = False
        self._stale = False
        self.setWindowTitle(bi("Rewrite one disputed claim", "改写一条争议主张"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Propose one interpretation of the original report's existing evidence. The copy "
            "labels it as your unverified proposal, with speculation and low confidence. "
            "Quotes, sources, topic and report group remain unchanged. No AI runs. Original "
            "reports, correction notes, cards and the active report stay unchanged.",
            "仅针对原报告已有证据提出一条解释。副本会明确标注为你提出的未验证解释，并固定为"
            "推测、低置信度。引文、来源、主题及报告分组保持原样。此操作不调用 AI；原报告、"
            "更正记录、卡片及当前使用的报告均不改变。",
        )))
        layout.addWidget(_label(bi(
            "The copy also removes all consistency findings, optional headlines and summaries. "
            "Other content is not reanalyzed; factual support and translation still need review.",
            "副本还会移除所有一致性发现、可选标题及摘要。其他内容不会重新分析；证据支持程度"
            "与翻译准确性仍需人工复核。",
        ) if kind == "self_portrait" else bi(
            "The copy also removes all fictional candidate profiles and recorded choices. "
            "Other content is not reanalyzed; factual support and translation still need review.",
            "副本还会移除所有虚构候选档案及其中的选择记录。其他内容不会重新分析；证据支持"
            "程度与翻译准确性仍需人工复核。",
        )))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        evidence_tab = QWidget()
        evidence_layout = QVBoxLayout(evidence_tab)
        evidence_layout.addWidget(_label(bi(
            "Choose one saved correction for the current original source version.",
            "选择当前原始源报告版本的一条已保存更正。",
        )))
        self.corrections = QListWidget()
        self.corrections.setMaximumHeight(100)
        self.corrections.currentRowChanged.connect(self._selection_changed)
        evidence_layout.addWidget(self.corrections)
        self.details = _reader()
        evidence_layout.addWidget(self.details, 1)
        self.tabs.addTab(evidence_tab, bi("Original claim and evidence", "原主张与证据"))

        draft_tab = QWidget()
        draft_layout = QVBoxLayout(draft_tab)
        draft_layout.addWidget(_label(bi(
            "Write both versions yourself, up to 4,000 characters each. Existing correction "
            "text is not copied into this proposal or treated as evidence.",
            "请自行填写两种语言的表述，每项最多 4,000 字符。已保存的更正文字不会自动填入"
            "此提议，也不会被当作证据。",
        )))
        draft_layout.addWidget(_label(bi("Your proposed wording — English", "你提议的表述——英文")))
        self.text_en = QPlainTextEdit()
        self.text_en.textChanged.connect(self._draft_changed)
        draft_layout.addWidget(self.text_en, 1)
        draft_layout.addWidget(_label(bi(
            "Your proposed wording — Simplified Chinese", "你提议的表述——简体中文",
        )))
        self.text_zh = QPlainTextEdit()
        self.text_zh.textChanged.connect(self._draft_changed)
        draft_layout.addWidget(self.text_zh, 1)
        self.tabs.addTab(draft_tab, bi("Bilingual proposal", "双语提议"))

        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.comparison = _reader()
        self.comparison.setMaximumHeight(130)
        preview_layout.addWidget(self.comparison)
        self.preview_text = _reader()
        preview_layout.addWidget(self.preview_text, 1)
        self.tabs.addTab(preview_tab, bi("Full bilingual preview", "完整双语预览"))
        self.tabs.currentChanged.connect(self._tab_changed)

        self.confirm = QCheckBox(bi(
            "Save this separate copy, full original snapshots and selected correction record.",
            "确认保存此独立副本、完整原始快照及所选更正记录。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        layout.addWidget(self.confirm)
        layout.addWidget(_label(bi(
            "Saved content is plaintext and retained after regeneration. Saving does not "
            "activate the copy; choose it separately in Select active report if wanted.",
            "保存内容为明文，重新生成报告后仍会保留。保存不会启用副本；如需使用，请另行通过"
            "「选择当前报告」进行确认。",
        )))
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh source", "刷新源报告"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        self.preview_button = SecondaryButton(bi("Preview proposed copy", "预览提议副本"))
        self.preview_button.clicked.connect(self._make_preview)
        actions.addWidget(self.preview_button)
        actions.addStretch()
        self.save_button = PrimaryButton(bi("Save separate copy", "保存独立副本"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        self.close_button = SecondaryButton(bi("Cancel", "取消"))
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)
        self.refresh()

    def _selected_record(self):
        item = self.corrections.currentItem()
        return self._records.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _proposal(self):
        record = self._selected_record()
        if record is None:
            return None
        try:
            return ReplacementProposal(
                correction_id=record.id,
                text_en=self.text_en.toPlainText(), text_zh=self.text_zh.toPlainText(),
            )
        except ValueError:
            return None

    def _update_buttons(self) -> None:
        if not hasattr(self, "save_button"):
            return
        proposal = self._proposal()
        ready = self.document is not None and not self._stale and proposal is not None
        self.preview_button.setEnabled(ready)
        valid = bool(ready and self.preview is not None and self.preview.proposal == proposal
                     and self.tabs.currentIndex() == 2)
        self.confirm.setEnabled(valid)
        self.save_button.setEnabled(valid and self.confirm.isChecked())

    def _invalidate_preview(self) -> None:
        self.preview = None
        self.confirm.setChecked(False)
        self.comparison.clear()
        self.preview_text.clear()

    def _tab_changed(self, _index: int) -> None:
        self.confirm.setChecked(False)
        self._update_buttons()

    def _draft_changed(self) -> None:
        if self._loading:
            return
        self._invalidate_preview()
        if not self._stale:
            self.status.setText(bi(
                "Draft only. Choose a current correction and enter both languages before "
                "previewing (English letters; at least two Chinese characters).",
                "当前仅为草稿。请选择当前版本的更正，并填写两种语言后再预览"
                "（英文需含英文字母；中文至少含两个汉字）。",
            ))
        self._update_buttons()

    def _selection_changed(self, _row: int) -> None:
        if self._loading:
            return
        self._invalidate_preview()
        record = self._selected_record()
        self.details.clear()
        if record is not None:
            self._previous_record = record
            claim = next(
                claim for claim in self.document.claims if claim.path == record.target_path
            )
            claim_type = {
                "observation": bi("Observation", "观察"),
                "inference": bi("Inference", "推断"),
                "speculation": bi("Speculation", "推测"),
            }[claim.type]
            confidence = {
                "low": bi("Low", "低"), "medium": bi("Medium", "中"), "high": bi("High", "高"),
            }[claim.confidence]
            parts = [
                bi("Original claim", "原始主张") + ": " + claim.claim,
                bi("Original type / confidence", "原类型 / 置信度")
                + ": " + claim_type + " / " + confidence,
                bi("Saved correction (annotation only)", "已保存的更正（仅为批注）")
                + ": " + record.correction_text,
                bi("Correction reason", "更正理由") + ": " + record.reason,
                bi("Original evidence retained verbatim", "完整保留的原始证据"),
            ]
            for evidence in claim.evidence:
                parts.extend([
                    bi("Source label (not a link)", "来源标签（不是链接）")
                    + ": " + evidence.source,
                    bi("Quotation", "引文") + ": " + evidence.quote,
                ])
            self.details.setPlainText("\n\n".join(parts))
        if not self._stale:
            self.status.setText(bi(
                "Selection changed. Draft wording is retained for your review against this "
                "claim; create a new preview before confirming.",
                "选择已变更。草稿表述已保留，请对照此主张重新复核；确认前需要生成新预览。",
            ))
        self._update_buttons()

    def refresh(self) -> None:
        previous = self._selected_record() or self._previous_record
        self._invalidate_preview()
        self._loading = True
        self.document = None
        self.corrections.clear()
        self.details.clear()
        self._records = {}
        try:
            if self.reviews is None:
                self.reviews = ReportReviewService(self.vault_dir)
            if self.service is None:
                self.service = ReportRevisionService(self.vault_dir)
            document = self.reviews.inspect(self.kind)
            records = self.reviews.list_corrections(self.kind, document.report_digest)
            self.document = document
            self._records = {record.id: record for record in records}
            for record in records:
                item = QListWidgetItem(" ".join(record.original_claim.split())[:150])
                item.setData(Qt.ItemDataRole.UserRole, record.id)
                self.corrections.addItem(item)
            self._stale = False
            self.status.setText(bi(
                "Choose one correction, write both versions, then preview. Nothing is saved.",
                "请选择一条更正，填写双语表述后预览。当前未保存任何内容。",
            ) if records else bi(
                "No current original-source corrections. Save a correction in the original "
                "evidence review first. Your draft is retained.",
                "当前原始源报告没有更正记录。请先在原报告证据复核中保存更正，草稿已保留。",
            ))
        except _ERRORS:
            self._stale = True
            self.status.setText(bi(
                "The original report or correction history cannot be verified. Existing files "
                "and your draft are preserved; refresh after repairing or regenerating it.",
                "无法校验原报告或更正历史。现有文件与草稿均已保留，请修复或重新生成后刷新。",
            ))
        finally:
            self._loading = False
        if previous is not None:
            self._previous_record = previous
            for row in range(self.corrections.count()):
                if self.corrections.item(row).data(Qt.ItemDataRole.UserRole) == previous.id:
                    self.corrections.setCurrentRow(row)
                    break
            else:
                self.details.setPlainText(bi(
                    "The previously selected correction is not eligible for this source "
                    "version. It is retained below for reference only; select a current "
                    "correction explicitly before previewing.",
                    "先前所选更正不适用于此源报告版本。下方仅保留原主张供参考；预览前请明确"
                    "选择当前版本的更正。",
                ) + "\n\n" + previous.original_claim)
        self._update_buttons()

    def _failure(self) -> None:
        self._stale = True
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "No copy was saved. The source, translations or correction may have changed or "
            "be invalid. Your choice and wording are retained; refresh and preview again.",
            "副本未保存。源报告、译文或更正可能已变化或无效。已保留选择与表述；请刷新后"
            "重新预览。",
        ))
        self._update_buttons()

    def _make_preview(self) -> None:
        if not self.preview_button.isEnabled():
            return
        try:
            self.preview = self.service.preview_replacement(
                self.kind, self._proposal(), expected_digest=self.document.report_digest,
            )
        except _ERRORS:
            self._failure()
            return
        self.comparison.setPlainText("\n\n".join([
            bi("Original claim", "原始主张") + ": " + self.preview.removed_claims[0].claim,
            bi("User proposal — English", "用户提议——英文") + ": " + self.preview.proposal.text_en,
            bi("User proposal — Chinese", "用户提议——中文") + ": " + self.preview.proposal.text_zh,
            bi("Fixed label: speculation; low confidence; unverified user interpretation.",
               "固定标签：推测、低置信度、用户提出的未验证解释。"),
        ]))
        self.preview_text.setPlainText(self.preview.detailed_markdown or self.preview.markdown)
        self.tabs.setCurrentIndex(2)
        self.confirm.setChecked(False)
        self.status.setText(bi(
            "Unsaved preview. Review both languages and the unchanged citations before confirming.",
            "尚未保存的预览。请复核双语内容及保持原样的引文后再确认。",
        ))
        self._update_buttons()

    def _save(self) -> None:
        if not self.save_button.isEnabled():
            return
        try:
            self.saved_revision = self.service.save_replacement(
                self.preview, confirmed=self.confirm.isChecked(),
            )
        except _ERRORS:
            self._failure()
            return
        self.accept()
