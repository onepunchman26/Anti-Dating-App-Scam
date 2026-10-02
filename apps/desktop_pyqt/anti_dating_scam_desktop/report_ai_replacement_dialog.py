"""Explicit local AI reinterpretation of one disputed claim; never source verification."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.services.report_regeneration import ReportRegenerationService
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import AIReplacementProposal, ReportRevisionService
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox
from anti_dating_scam_desktop.workers import has_pending_workers, run_async


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


def _reader() -> QPlainTextEdit:
    reader = QPlainTextEdit()
    reader.setReadOnly(True)
    return reader


class ReportAIReplacementDialog(QDialog):
    """Only explicit generation and save actions cross their respective boundaries."""

    def __init__(self, vault_dir: Path, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.vault_dir, self.kind = Path(vault_dir), kind
        self.reviews = ReportReviewService(self.vault_dir)
        self.service = ReportRevisionService(self.vault_dir)
        self.regeneration = ReportRegenerationService(self.vault_dir)
        self.document = self.prepared = self.generated_proposal = self.preview = None
        self.saved_revision = None
        self._records = {}
        self._loading = self._busy = self._stale = self._discard_reply = False
        self._close_when_idle = False
        self._reviewed_backend = None
        self._reviewed_recipient = None
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(20)
        self._idle_timer.timeout.connect(self._finish_worker)
        self.setWindowTitle(bi("AI-assisted reinterpretation", "AI 辅助重新解释"))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Reinterpret one disputed claim using its stored quotations only. This does not "
            "verify original sources or regenerate the full report. AI-assisted wording stays "
            "an unverified, low-confidence speculation, even after editing.",
            "仅使用已保存引文重新解释一条争议主张。此功能不会核验原始来源或重新生成整份报告。"
            "AI 辅助表述即使经过编辑，也始终标注为未经验证、低置信度的推测。",
        )))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        choices, choices_layout = self._tab(bi("1. Choose correction", "1. 选择更正"))
        choices_layout.addWidget(_label(bi(
            "Select a saved correction from the original source report. No model runs when "
            "you open this dialog or review a request.",
            "选择原始源报告的一条已保存更正。打开此窗口或查看请求时不会调用模型。",
        )))
        self.corrections = QListWidget()
        self.corrections.setMaximumHeight(110)
        self.corrections.currentRowChanged.connect(self._selection_changed)
        choices_layout.addWidget(self.corrections)
        self.details = _reader()
        choices_layout.addWidget(self.details, 1)
        self.prepare_button = SecondaryButton(bi("Review exact AI request", "查看完整 AI 请求"))
        self.prepare_button.clicked.connect(self._prepare)
        choices_layout.addWidget(self.prepare_button)

        request_tab, request_layout = self._tab(bi("2. Review request", "2. 复核请求"))
        self.recipient = _label("")
        request_layout.addWidget(self.recipient)
        request_layout.addWidget(_label(bi(
            "Complete application request below: instructions, selected claim, saved correction, "
            "stored quotes and output format. The correction is an annotation, not evidence. "
            "Only your connected local Ollama model is allowed; no remote API or agent CLI.",
            "下方为完整应用请求：指令、所选主张、已保存更正、已存引文及输出格式。"
            "更正仅为批注，并非证据。只允许当前连接的本地 Ollama 模型，"
            "不使用远程 API 或代理命令行。",
        )))
        self.request_text = _reader()
        request_layout.addWidget(self.request_text, 1)
        self.generate_consent = WrappedCheckBox(bi(
            "I reviewed this exact request and allow one local generation. A successful reply "
            "will replace the bilingual draft below; nothing will be saved automatically.",
            "我已复核此完整请求，同意执行一次本地生成。成功回复会替换下方双语草稿；不会自动保存任何内容。",
        ))
        self.generate_consent.toggled.connect(self._update_buttons)
        request_layout.addWidget(self.generate_consent)
        self.generate_button = PrimaryButton(bi("Generate one suggestion", "生成一条建议"))
        self.generate_button.setAutoDefault(False)
        self.generate_button.clicked.connect(self._generate)
        request_layout.addWidget(self.generate_button)

        draft_tab, draft_layout = self._tab(bi("3. Edit suggestion", "3. 编辑建议"))
        draft_layout.addWidget(_label(bi(
            "Review both languages, up to 4,000 characters each. Editing retains AI-assisted "
            "attribution. Quotes remain unchanged; relevance and translation need human review.",
            "请复核两种语言，每项最多 4,000 字符。编辑后仍保留 AI 辅助标注。引文保持原样；"
            "引文是否支持表述及翻译准确性仍需人工复核。",
        )))
        draft_layout.addWidget(_label(bi("Suggestion — English", "建议——英文")))
        self.text_en = QPlainTextEdit()
        self.text_en.textChanged.connect(self._draft_changed)
        draft_layout.addWidget(self.text_en, 1)
        draft_layout.addWidget(_label(bi("Suggestion — Simplified Chinese", "建议——简体中文")))
        self.text_zh = QPlainTextEdit()
        self.text_zh.textChanged.connect(self._draft_changed)
        draft_layout.addWidget(self.text_zh, 1)

        preview_tab, preview_layout = self._tab(bi("4. Full preview", "4. 完整预览"))
        preview_layout.addWidget(_label(bi(
            "Save a separate plaintext copy, original snapshots and the selected correction. "
            "Original reports, cards and active selection stay unchanged. This copy remains "
            "after regeneration. Other findings are not reanalyzed; derived summaries and "
            "consistency findings or fictional candidates are omitted.",
            "保存独立明文副本、原始快照及所选更正。原报告、卡片及当前选择保持不变；"
            "重新生成后此副本仍会保留。其他发现不会重新分析；衍生摘要与一致性发现或虚构候选人会被移除。",
        )))
        self.preview_text = _reader()
        preview_layout.addWidget(self.preview_text, 1)
        self.confirm = WrappedCheckBox(bi(
            "I reviewed the full bilingual copy and confirm saving it separately, with its "
            "original snapshots and correction record. Saving does not activate it.",
            "我已复核完整双语副本，同意将其连同原始快照及更正记录单独保存。保存不会启用此副本。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        preview_layout.addWidget(self.confirm)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QGridLayout()
        self.refresh_button = SecondaryButton(bi("Refresh source", "刷新源报告"))
        self.refresh_button.clicked.connect(self.refresh)
        self.preview_button = SecondaryButton(bi("Preview separate copy", "预览独立副本"))
        self.preview_button.clicked.connect(self._make_preview)
        self.save_button = PrimaryButton(bi("Save separate copy", "保存独立副本"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        self.close_button = SecondaryButton(bi("Cancel", "取消"))
        self.close_button.clicked.connect(self.reject)
        for column, button in enumerate((self.refresh_button, self.preview_button,
                                          self.save_button, self.close_button)):
            actions.addWidget(button, 0, column)
        layout.addLayout(actions)
        self.refresh()

    def _tab(self, title):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.tabs.addTab(widget, title)
        return widget, layout

    def _selected_record(self):
        item = self.corrections.currentItem()
        return self._records.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _proposal(self):
        if self.generated_proposal is None:
            return None
        try:
            return AIReplacementProposal.model_validate({
                **self.generated_proposal.model_dump(),
                "text_en": self.text_en.toPlainText(), "text_zh": self.text_zh.toPlainText(),
            })
        except ValueError:
            return None

    def _update_buttons(self, *_args):
        if not hasattr(self, "save_button"):
            return
        ready = self.document is not None and not self._stale and not self._busy
        self.corrections.setEnabled(not self._busy)
        self.refresh_button.setEnabled(not self._busy)
        self.prepare_button.setEnabled(ready and self._selected_record() is not None)
        self.text_en.setReadOnly(self._busy)
        self.text_zh.setReadOnly(self._busy)
        can_generate = ready and self.prepared is not None and self._reviewed_backend is not None
        self.generate_consent.setEnabled(can_generate and self.tabs.currentIndex() == 1)
        self.generate_button.setEnabled(bool(can_generate and self.generate_consent.isChecked()
                                             and self.tabs.currentIndex() == 1))
        proposal = self._proposal()
        self.preview_button.setEnabled(ready and proposal is not None)
        valid = bool(ready and proposal is not None and self.preview is not None
                     and self.preview.proposal == proposal and self.tabs.currentIndex() == 3)
        self.confirm.setEnabled(valid)
        self.save_button.setEnabled(valid and self.confirm.isChecked())

    def _invalidate_preview(self):
        self.preview = None
        self.confirm.setChecked(False)
        self.preview_text.clear()

    def _invalidate_request(self):
        self.prepared = self.generated_proposal = None
        self._reviewed_backend = self._reviewed_recipient = None
        self.request_text.clear()
        self.recipient.clear()
        self.generate_consent.setChecked(False)
        self._invalidate_preview()

    def _tab_changed(self, _index):
        self.generate_consent.setChecked(False)
        self.confirm.setChecked(False)
        self._update_buttons()

    def _draft_changed(self):
        if not self._loading:
            self._invalidate_preview()
            self._update_buttons()

    def _selection_changed(self, _row):
        if self._loading:
            return
        self._invalidate_request()
        record = self._selected_record()
        self.details.setPlainText("" if record is None else "\n\n".join([
            bi("Original claim", "原始主张") + ": " + record.original_claim,
            bi("Correction — annotation only", "更正——仅为批注") + ": " + record.correction_text,
            bi("Reason", "理由") + ": " + record.reason,
        ]))
        self.status.setText(bi(
            "Draft retained. Review a fresh request for this selection before generating.",
            "草稿已保留。生成前请查看此选择对应的新请求。",
        ))
        self._update_buttons()

    def refresh(self):
        if self._busy:
            return
        previous = self._selected_record()
        self._invalidate_request()
        self._loading = True
        self.document = None
        self.corrections.clear()
        self.details.clear()
        self._records = {}
        try:
            self.document = self.reviews.inspect(self.kind)
            records = self.reviews.list_corrections(self.kind, self.document.report_digest)
            self._records = {record.id: record for record in records}
            for record in records:
                item = QListWidgetItem(" ".join(record.original_claim.split())[:150])
                item.setData(Qt.ItemDataRole.UserRole, record.id)
                self.corrections.addItem(item)
            self._stale = False
            self.status.setText(bi(
                "Select a saved correction; review its request before any local AI call.",
                "请选择已保存的更正；任何本地 AI 调用前均需复核对应请求。",
            ) if records else bi(
                "No current corrections. Save one in original evidence review first. "
                "Draft retained.",
                "当前没有更正记录。请先在原报告证据复核中保存更正。草稿已保留。",
            ))
        except Exception:
            self._failure()
        finally:
            self._loading = False
        if previous:
            for row in range(self.corrections.count()):
                if self.corrections.item(row).data(Qt.ItemDataRole.UserRole) == previous.id:
                    self.corrections.setCurrentRow(row)
                    break
        self._update_buttons()

    def _failure(self):
        self._stale = True
        self._invalidate_preview()
        self.generate_consent.setChecked(False)
        self.status.setText(bi(
            "Nothing saved or applied. The source, correction or request could not be verified. "
            "Your draft is retained. Refresh, review a new request and try again.",
            "未保存或应用任何内容。无法校验源报告、更正或请求。草稿已保留。"
            "请刷新、复核新请求后重试。",
        ))
        self._update_buttons()

    def _prepare(self):
        if not self.prepare_button.isEnabled():
            return
        self._invalidate_request()
        try:
            self.prepared = self.regeneration.prepare(
                self.kind, self._selected_record().id,
                expected_digest=self.document.report_digest,
            )
            self.request_text.setPlainText(self.prepared.request.model_dump_json(indent=2))
            backend = ai_backend.get_active()
            if isinstance(backend, OllamaChatBackend):
                self._reviewed_recipient = backend.recipient
                self._reviewed_backend = backend
                self.recipient.setText(bi("Local recipient: ", "本地接收方：") + backend.recipient)
            else:
                self.recipient.setText(bi(
                    "Connect a local Ollama model first, then review the request again.",
                    "请先连接本地 Ollama 模型，再重新复核请求。",
                ))
            self.tabs.setCurrentIndex(1)
            self.status.setText(bi(
                "Request ready; no model call made.", "请求已就绪，尚未调用模型。",
            ))
        except Exception:
            self._failure()
        self._update_buttons()

    def _request_still_current(self, prepared, backend, recipient):
        record = self._selected_record()
        if (record is None or self.prepared != prepared or ai_backend.get_active() is not backend
                or backend.recipient != recipient):
            return False
        fresh = self.regeneration.prepare(
            self.kind, record.id, expected_digest=self.document.report_digest,
        )
        return fresh == prepared

    def _generate(self):
        if not self.generate_button.isEnabled():
            return
        prepared, backend, recipient = (
            self.prepared, self._reviewed_backend, self._reviewed_recipient,
        )
        try:
            if not self._request_still_current(prepared, backend, recipient):
                self._failure()
                return
        except Exception:
            self._failure()
            return
        self._busy, self._discard_reply = True, False
        self._invalidate_preview()
        self.generate_consent.setChecked(False)
        self._update_buttons()
        self.status.setText(bi(
            "Generating locally. Cancel discards the reply and waits for the worker to finish.",
            "正在本地生成。取消将丢弃回复，并等待后台任务结束。",
        ))

        self._pending_request = (prepared, backend, recipient)
        service = self.regeneration
        run_async(self, lambda: service.generate(prepared, backend, confirmed=True),
                  self._generation_completed, self._generation_failed)
        self._idle_timer.start()

    @Slot(object)
    def _generation_completed(self, proposal):
        if self._discard_reply:
            return
        prepared, backend, recipient = self._pending_request
        try:
            if not self._request_still_current(prepared, backend, recipient):
                self._failure()
                return
            proposal = AIReplacementProposal.model_validate(proposal)
            if (proposal.correction_id != prepared.correction_id
                    or proposal.context_digest != prepared.context_digest
                    or proposal.request_digest != prepared.request_digest):
                self._failure()
                return
            self.generated_proposal = proposal
            self._loading = True
            self.text_en.setPlainText(proposal.text_en)
            self.text_zh.setPlainText(proposal.text_zh)
            self._loading = False
            self.tabs.setCurrentIndex(2)
            self.status.setText(bi(
                "Unsaved AI-assisted suggestion. Review and edit both languages, then preview.",
                "尚未保存的 AI 辅助建议。请复核并编辑双语内容，再生成完整预览。",
            ))
        except Exception:
            self._loading = False
            self._failure()

    @Slot(str)
    def _generation_failed(self, _private_error):
        if not self._discard_reply:
            self.status.setText(bi(
                "Local generation failed or returned an invalid suggestion. No reply was "
                "applied; your draft is retained. Review the request before retrying.",
                "本地生成失败或返回无效建议。未应用回复，草稿已保留。重试前请重新复核请求。",
            ))

    def _finish_worker(self):
        if has_pending_workers(self):
            return
        self._idle_timer.stop()
        self._busy = False
        self._update_buttons()
        if self._close_when_idle:
            self._close_when_idle = False
            super().reject()

    def reject(self):
        if self._busy or has_pending_workers(self):
            self._discard_reply = self._close_when_idle = True
            self.generate_consent.setChecked(False)
            self.status.setText(bi(
                "Cancelled: the reply will be discarded. Waiting safely for the local worker; "
                "your existing draft is unchanged.",
                "已取消：回复将被丢弃。正在安全等待本地后台任务结束；现有草稿未改变。",
            ))
            return
        super().reject()

    def closeEvent(self, event):
        if self._busy or has_pending_workers(self):
            self.reject()
            event.ignore()
            return
        super().closeEvent(event)

    def _make_preview(self):
        if not self.preview_button.isEnabled():
            return
        try:
            if not self._request_still_current(
                self.prepared, self._reviewed_backend, self._reviewed_recipient,
            ):
                self._failure()
                return
            self.preview = self.service.preview_ai_replacement(
                self.kind, self._proposal(), expected_digest=self.document.report_digest,
            )
            self.preview_text.setPlainText(self.preview.detailed_markdown or self.preview.markdown)
            self.tabs.setCurrentIndex(3)
            self.confirm.setChecked(False)
            self.status.setText(bi(
                "Full bilingual preview only. Review it before explicitly saving a separate copy.",
                "当前仅为完整双语预览。请复核后明确确认保存独立副本。",
            ))
        except Exception:
            self._failure()
        self._update_buttons()

    def _save(self):
        if not self.save_button.isEnabled():
            return
        try:
            self.saved_revision = self.service.save_ai_replacement(
                self.preview, confirmed=self.confirm.isChecked(),
            )
        except Exception:
            self._failure()
            return
        self.accept()
