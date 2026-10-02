"""Local evidence review; corrections remain separate from canonical reports."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.services.report_review import ReportReviewError, ReportReviewService
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


def _plain(*, readonly: bool = False) -> QPlainTextEdit:
    editor = QPlainTextEdit()
    editor.setReadOnly(readonly)
    return editor


def _topic(value: str) -> str:
    labels = {
        "values": ("Values", "价值观"),
        "wants": ("Wants", "个人期待"),
        "communication": ("Communication", "沟通方式"),
        "boundaries": ("Boundaries", "个人边界"),
        "market_stance": ("Relationship preferences", "关系偏好"),
        "presentation": ("Self-presentation", "自我呈现"),
        "pattern": ("Pattern", "行为模式"),
    }
    return bi(*labels[value]) if value in labels else value


def correction_notice(vault_dir: Path, kind: str) -> str:
    """Persistent reminder beside the original report, including all versions."""
    try:
        count = len(ReportReviewService(vault_dir).list_corrections(kind))
    except (ReportReviewError, OSError, ValueError):
        return bi(
            "Original-report correction history is unavailable. Corrections remain separate "
            "from the selected report.",
            "原报告的更正历史暂不可用。更正记录与已选报告分开保存。",
        )
    if not count:
        return ""
    return bi(
        f"{count} saved correction(s) across report versions. Original reports are unchanged. "
        "These separate notes are not automatically applied to the active report, exports, "
        "or AI requests.",
        f"各报告版本共保存了 {count} 条更正。原报告未改变。这些独立注释不会自动应用到当前"
        "报告、导出内容或 AI 请求。",
    )


class ReportReviewDialog(QDialog):
    """Review report claims using plain text and explicit local-only writes."""

    def __init__(self, vault_dir: Path, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.vault_dir = Path(vault_dir)
        self.service = None
        self.document = None
        self._stale = False
        self.setWindowTitle(bi("Review original evidence & corrections", "复核原报告证据与更正"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "This dialog reviews the original source report, even when a reviewed copy is "
            "selected elsewhere. Review its claims, quoted evidence and source labels. Labels are "
            "not verified identities or links. Corrections are separate local annotations: "
            "they do not change the report and are not automatically applied, shared, sent "
            "to AI, or used as AI evidence. Saving also retains a plaintext copy of the full "
            "original JSON report in reports/review_history, even after regeneration. "
            "Human review is still required.",
            "此窗口始终复核原始源报告，即使其他页面已选择复核副本。请复核原始主张、证据"
            "引文和来源标签。来源标签不是经过验证的身份或链接。"
            "更正是独立的本地注释：不会修改原报告，也不会自动应用、分享、发送给 AI 或"
            "用作 AI 证据。保存时还会在 reports/review_history 中保留完整原始 JSON 报告的"
            "明文副本；重新生成报告后，此副本仍会保留。内容仍需人工审核。",
        )))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        review = QWidget()
        form = QVBoxLayout(review)
        form.addWidget(_label(bi("Select a claim", "选择一条主张")))
        self.claims = QListWidget()
        self.claims.setMaximumHeight(72)
        self.claims.currentRowChanged.connect(self._select_claim)
        form.addWidget(self.claims)
        self.details = _plain(readonly=True)
        form.addWidget(self.details, 1)
        form.addWidget(_label(bi(
            "Your correction (saved separately; up to 8,000 characters)",
            "你的更正（单独保存，最多 8,000 字符）",
        )))
        self.correction = _plain()
        self.correction.setMaximumHeight(85)
        self.correction.textChanged.connect(self._draft_changed)
        form.addWidget(self.correction)
        form.addWidget(_label(bi(
            "Reason for this correction (up to 2,000 characters)",
            "更正理由（最多 2,000 字符）",
        )))
        self.reason = _plain()
        self.reason.setMaximumHeight(65)
        self.reason.textChanged.connect(self._draft_changed)
        form.addWidget(self.reason)
        self.confirm = QCheckBox(bi(
            "Confirm local save of this correction, reason and original report snapshot.",
            "我确认在本地保存这条更正、理由及原始报告快照。",
        ))
        self.confirm.toggled.connect(self._update_save)
        form.addWidget(self.confirm)
        self.tabs.addTab(review, bi("Claim review", "主张复核"))
        self.current_history = _plain(readonly=True)
        self.prior_history = _plain(readonly=True)
        self.tabs.addTab(
            self.current_history, bi("Original source corrections", "原始源报告的更正"),
        )
        self.tabs.addTab(self.prior_history, bi("Prior report versions", "历史报告版本"))
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.refresh_button = SecondaryButton(bi("Refresh report", "刷新报告"))
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        self.revision_button = SecondaryButton(bi("Create reviewed copy", "生成复核副本"))
        self.revision_button.clicked.connect(self._create_reviewed_copy)
        actions.addWidget(self.revision_button)
        self.selection_button = SecondaryButton(bi("Select active report", "选择当前报告"))
        self.selection_button.clicked.connect(self._select_active_report)
        actions.addWidget(self.selection_button)
        actions.addStretch()
        self.save_button = PrimaryButton(bi("Save correction", "保存更正"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        self.close_button = SecondaryButton(bi("Close without saving draft", "关闭且不保存草稿"))
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)
        self.refresh()

    def _create_reviewed_copy(self) -> None:
        from anti_dating_scam_desktop.report_revision_dialog import ReportRevisionDialog

        ReportRevisionDialog(self.vault_dir, self.kind, self).exec()

    def _select_active_report(self) -> None:
        from anti_dating_scam_desktop.report_selection_dialog import ReportSelectionDialog

        ReportSelectionDialog(self.vault_dir, self.kind, self).exec()

    def _draft_changed(self) -> None:
        self.confirm.setChecked(False)
        if self.document is not None and not self._stale:
            self.status.setText(bi(
                "Unsaved draft. Review it, confirm, and select Save correction to keep it.",
                "草稿尚未保存。请复核、确认，再点击「保存更正」以保留内容。",
            ) if self.correction.toPlainText() or self.reason.toPlainText() else "")
        self._update_save()

    def _update_save(self) -> None:
        if not hasattr(self, "save_button"):
            return
        self.save_button.setEnabled(bool(
            self.document is not None
            and not self._stale
            and self.claims.currentRow() >= 0
            and self.correction.toPlainText().strip()
            and self.reason.toPlainText().strip()
            and len(self.correction.toPlainText()) <= 8_000
            and len(self.reason.toPlainText()) <= 2_000
            and self.confirm.isChecked()
        ))

    def refresh(self) -> None:
        """Reload the report without clearing an unsaved correction or reason."""
        has_draft = bool(self.correction.toPlainText() or self.reason.toPlainText())
        self.confirm.setChecked(False)
        self.document = None
        self.claims.clear()
        self.details.clear()
        self.current_history.clear()
        self.prior_history.clear()
        try:
            if self.service is None:
                self.service = ReportReviewService(self.vault_dir)
            self.document = self.service.inspect(self.kind)
        except (ReportReviewError, OSError, ValueError):
            self.status.setText(bi(
                "This report is missing, legacy, or invalid. Regenerate a valid structured "
                "report, then refresh. Existing files and your unsaved draft are preserved.",
                "报告不存在、属于旧格式或内容无效。请重新生成有效的结构化报告，然后刷新。"
                "现有文件和未保存草稿均已保留。",
            ))
            self._update_save()
            return
        self._stale = False
        for claim in self.document.claims:
            self.claims.addItem(f"{_topic(claim.topic)}: {claim.claim}")
        if has_draft:
            self.status.setText(bi(
                "Report refreshed. Your draft is preserved. Select a claim, check the draft "
                "against it, and confirm again before saving.",
                "报告已刷新，草稿已保留。请重新选择主张，对照核实草稿，并再次确认后保存。",
            ))
        elif self.document.claims:
            self.claims.setCurrentRow(0)
            self.status.setText("")
        else:
            self.details.setPlainText(self._caveats())
            self.status.setText(bi(
                "This report has no claims available for correction.",
                "此报告没有可供更正的主张。",
            ))
        self._load_history()
        self._update_save()

    def _caveats(self) -> str:
        return bi("Report caveats", "报告限制说明") + "\n" + "\n".join(
            self.document.caveats if self.document else []
        )

    def _select_claim(self, row: int) -> None:
        self.confirm.setChecked(False)
        if self.document is None or row < 0 or row >= len(self.document.claims):
            self.details.clear()
            self._update_save()
            return
        claim = self.document.claims[row]
        types = {
            "observation": bi("Observation: check against the quote", "观察：请对照引文核实"),
            "inference": bi(
                "Inference: an interpretation, not a direct fact", "推断：解释而非直接事实"
            ),
            "speculation": bi("Speculation: a possibility to verify", "猜测：尚待核实的可能性"),
        }
        confidence = {
            "low": bi("Low: limited support", "低：支持有限"),
            "medium": bi(
                "Medium: some support; uncertainty remains", "中：有一定支持，仍有不确定性"
            ),
            "high": bi(
                "High: stronger support in this material, not proof", "高：材料内支持较强，并非证明"
            ),
        }
        sections = [
            bi("Original claim", "原始主张") + ": " + claim.claim,
            bi("Topic", "主题") + ": " + _topic(claim.topic),
            bi("Type", "类型") + ": " + types.get(claim.type, claim.type),
            bi("Confidence", "置信度") + ": " + confidence.get(claim.confidence, claim.confidence),
            bi("Quoted evidence (verbatim)", "证据引文（原文）"),
        ]
        for evidence in claim.evidence:
            sections.extend([
                bi("Source label", "来源标签") + ": " + evidence.source,
                bi("Quote", "引文") + ": " + evidence.quote,
            ])
        if not claim.evidence:
            sections.append(bi("No quoted evidence is recorded.", "没有记录证据引文。"))
        sections.append(self._caveats())
        sections.append(bi("Claim location", "主张位置") + ": " + claim.path)
        self.details.setPlainText("\n".join(sections))
        self._update_save()

    def _load_history(self) -> bool:
        try:
            records = self.service.list_corrections(self.kind)
        except (ReportReviewError, OSError, ValueError):
            self.status.setText(bi(
                "Correction history could not be read. Existing files have not been changed.",
                "无法读取更正历史。现有文件未被修改。",
            ))
            return False
        current, prior = [], []
        for record in records:
            text = "\n".join([
                bi("Report version", "报告版本") + ": " + record.report_digest,
                bi("Saved at", "保存时间") + ": " + str(record.created_at),
                bi("Claim location", "主张位置") + ": " + record.target_path,
                bi("Original claim", "原始主张") + ": " + record.original_claim,
                bi("Correction", "更正") + ": " + record.correction_text,
                bi("Reason", "理由") + ": " + record.reason,
            ])
            target = current if record.report_digest == self.document.report_digest else prior
            target.append(text)
        empty = bi("No saved corrections.", "尚无已保存的更正。")
        self.current_history.setPlainText("\n\n———\n\n".join(current) or empty)
        self.prior_history.setPlainText("\n\n———\n\n".join(prior) or empty)
        return True

    def _save(self) -> None:
        if not self.save_button.isEnabled():
            return
        claim = self.document.claims[self.claims.currentRow()]
        try:
            self.service.record_correction(
                self.kind,
                expected_digest=self.document.report_digest,
                target_path=claim.path,
                correction_text=self.correction.toPlainText(),
                reason=self.reason.toPlainText(),
                confirmed=self.confirm.isChecked(),
            )
        except (ReportReviewError, OSError, ValueError):
            # Any rejected write requires a fresh inspection, including a stale
            # report. Never echo exception content or discard the user's draft.
            self._stale = True
            self.confirm.setChecked(False)
            self.status.setText(bi(
                "The correction was not saved. The report may have changed or the input may "
                "be invalid. Refresh, review the selected claim and confirm again. Your draft "
                "is preserved.",
                "更正未保存。报告可能已变化，或输入不符合要求。请刷新，复核所选主张后"
                "再次确认。草稿已保留。",
            ))
            self._update_save()
            return
        self.correction.clear()
        self.reason.clear()
        self.confirm.setChecked(False)
        history_ok = self._load_history()
        self.status.setText(bi(
            "Correction saved separately. The original report is unchanged.",
            "更正已单独保存，原报告未改变。",
        ) + ("" if history_ok else " " + bi(
            "History could not be refreshed; reopen this dialog to retry.",
            "历史记录刷新失败，请重新打开此窗口重试。",
        )))
        self._update_save()
