"""Explicit full-report regeneration from pasted excerpts, with separate immutable saving."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.services.report_full_regeneration import FullReportRegenerationService
from anti_dating_scam.services.report_full_regeneration_contract import (
    FullRegenerationProposal,
    RegenerationExcerpt,
)
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionService
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox
from anti_dating_scam_desktop.workers import has_pending_workers, run_async


def _label(text):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


def _reader():
    reader = QPlainTextEdit()
    reader.setReadOnly(True)
    return reader


class ReportFullRegenerationDialog(QDialog):
    """Inputs stay in memory until a separately confirmed copy saves its snapshots."""

    def __init__(self, vault_dir: Path, kind: str, parent=None):
        super().__init__(parent)
        self.vault_dir, self.kind = Path(vault_dir), kind
        self.reviews = ReportReviewService(self.vault_dir)
        self.service = ReportRevisionService(self.vault_dir)
        self.regeneration = FullReportRegenerationService(self.vault_dir)
        self.document = self.prepared = self.generated_proposal = self.preview = None
        self.saved_revision = None
        self._records = {}
        self._excerpts = [""]
        self._loading = self._busy = self._stale = self._discard_reply = False
        self._close_when_idle = False
        self._reviewed_backend = self._reviewed_recipient = self._pending_request = None
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(20)
        self._idle_timer.timeout.connect(self._finish_worker)
        self.setWindowTitle(bi(
            "Regenerate a full report from excerpts", "根据摘录重新生成完整报告",
        ))
        self.resize(940, 700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(bi(
            "Create a new report from your pasted original excerpts and selected correction "
            "context. AI output stays provisional and unverified. Saving makes a separate "
            "copy; your original report and active selection remain unchanged.",
            "根据你粘贴的原始摘录及所选更正背景生成新报告。AI 输出始终是未经核实的暂定解释。"
            "保存会生成独立副本；原报告及当前选择保持不变。",
        )))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        inputs = self._tab(bi("1. Corrections and excerpts", "1. 更正与摘录"))
        inputs.addWidget(_label(bi(
            "Choose 1–10 saved corrections. They provide context, not new evidence.",
            "选择 1–10 条已保存的更正。更正仅提供背景，不是新证据。",
        )))
        self.corrections = QListWidget()
        self.corrections.setMinimumHeight(55)
        self.corrections.setMaximumHeight(90)
        self.corrections.itemChanged.connect(self._inputs_changed)
        self.corrections.currentRowChanged.connect(self._show_correction)
        inputs.addWidget(self.corrections)
        self.correction_details = _reader()
        self.correction_details.setMinimumHeight(45)
        self.correction_details.setMaximumHeight(65)
        inputs.addWidget(self.correction_details)
        inputs.addWidget(_label(bi(
            "Paste 1–5 original excerpts: at most 12,000 characters each, 24,000 in total. "
            "Do not paste AI reports. Source IDs follow the excerpt order; no files are scanned.",
            "粘贴 1–5 段原始摘录：每段最多 12,000 字符，总计最多 24,000 字符。"
            "请勿粘贴 AI 报告。来源编号按摘录顺序分配；不会扫描文件。",
        )))
        excerpt_actions = QHBoxLayout()
        self.excerpt_selector = QComboBox()
        self.excerpt_selector.currentIndexChanged.connect(self._show_excerpt)
        excerpt_actions.addWidget(self.excerpt_selector, 1)
        self.add_excerpt_button = SecondaryButton(bi("Add excerpt", "添加摘录"))
        self.add_excerpt_button.clicked.connect(self._add_excerpt)
        excerpt_actions.addWidget(self.add_excerpt_button)
        self.remove_excerpt_button = SecondaryButton(bi("Remove excerpt", "移除此摘录"))
        self.remove_excerpt_button.clicked.connect(self._remove_excerpt)
        excerpt_actions.addWidget(self.remove_excerpt_button)
        inputs.addLayout(excerpt_actions)
        self.excerpt_text = QPlainTextEdit()
        self.excerpt_text.setMinimumHeight(70)
        self.excerpt_text.setPlaceholderText(bi(
            "Paste your own original notes or statements here. Nothing is imported automatically.",
            "在此粘贴你自己的原始笔记或陈述。不会自动导入任何内容。",
        ))
        self.excerpt_text.textChanged.connect(self._excerpt_edited)
        inputs.addWidget(self.excerpt_text, 1)
        self.input_counts = _label("")
        inputs.addWidget(self.input_counts)
        self.original_consent = WrappedCheckBox(bi(
            "I confirm these excerpts are my own original notes or statements, not generated "
            "reports. The app cannot verify authorship, truth or quotation relevance.",
            "我确认这些摘录是我自己的原始笔记或陈述，而非生成的报告。"
            "应用无法核验作者身份、真实性或引文是否支持结论。",
        ))
        self.original_consent.toggled.connect(self._attestation_changed)
        inputs.addWidget(self.original_consent)

        request_layout = self._tab(bi("2. Review exact request", "2. 复核完整请求"))
        self.recipient = _label("")
        request_layout.addWidget(self.recipient)
        request_layout.addWidget(_label(bi(
            "Review the complete instructions, excerpts, correction context and output format. "
            "Only the connected local Ollama model can receive this request. No remote API "
            "or agent CLI is used; no model runs until you confirm below.",
            "请复核完整指令、摘录、更正背景及输出格式。此请求仅可发送给当前连接的本地 Ollama 模型。"
            "不使用远程 API 或代理命令行；下方明确确认之前不会调用模型。",
        )))
        self.request_text = _reader()
        request_layout.addWidget(self.request_text, 1)
        self.generate_consent = WrappedCheckBox(bi(
            "I reviewed this exact request and allow one local generation. Nothing will be "
            "saved or activated automatically.",
            "我已复核此完整请求，同意执行一次本地生成。不会自动保存或启用任何内容。",
        ))
        self.generate_consent.toggled.connect(self._update_buttons)
        request_layout.addWidget(self.generate_consent)
        self.generate_button = PrimaryButton(bi("Generate full report", "生成完整报告"))
        self.generate_button.setAutoDefault(False)
        self.generate_button.clicked.connect(self._generate)
        request_layout.addWidget(self.generate_button)

        preview_layout = self._tab(bi("3. Full bilingual preview", "3. 完整双语预览"))
        preview_layout.addWidget(_label(bi(
            "Review the full English and Chinese copy, including evidence and uncertainty. "
            "Structure and exact quotes do not establish correct reasoning, source authenticity "
            "or translation quality. To change it, edit the excerpts and prepare a new request.",
            "请复核完整中英文副本，包括证据与不确定性。结构和精确引文不能证明推理正确、来源真实"
            "或翻译准确。若需修改，请编辑摘录并准备新请求。",
        )))
        self.preview_text = _reader()
        preview_layout.addWidget(self.preview_text, 1)
        self.confirm = WrappedCheckBox(bi(
            "I reviewed both languages and confirm saving this separate plaintext copy, pasted "
            "excerpts, original snapshots and selected corrections. It remains in history; "
            "saving does not activate it.",
            "我已复核两种语言，同意将此独立明文副本、粘贴的摘录、原始快照及所选更正一并保存。"
            "这些内容会保留在历史中；保存不会启用副本。",
        ))
        self.confirm.toggled.connect(self._update_buttons)
        preview_layout.addWidget(self.confirm)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.status = _label("")
        layout.addWidget(self.status)
        actions = QGridLayout()
        self.refresh_button = SecondaryButton(bi("Refresh source", "刷新源报告"))
        self.refresh_button.clicked.connect(self.refresh)
        self.prepare_button = SecondaryButton(bi("Review exact AI request", "查看完整 AI 请求"))
        self.prepare_button.clicked.connect(self._prepare)
        self.save_button = PrimaryButton(bi("Save separate copy", "保存独立副本"))
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._save)
        self.close_button = SecondaryButton(bi("Cancel", "取消"))
        self.close_button.clicked.connect(self.reject)
        for column, button in enumerate((self.refresh_button, self.prepare_button,
                                        self.save_button, self.close_button)):
            actions.addWidget(button, 0, column)
        layout.addLayout(actions)
        self._reload_excerpt_selector(0)
        self.refresh()

    def _tab(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.tabs.addTab(page, title)
        return layout

    def selected_ids(self):
        return [
            self.corrections.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.corrections.count())
            if self.corrections.item(row).checkState() == Qt.CheckState.Checked
        ]

    def _typed_excerpts(self):
        return [RegenerationExcerpt(text=text) for text in self._excerpts]

    def _valid_inputs(self):
        return (1 <= len(self.selected_ids()) <= 10 and 1 <= len(self._excerpts) <= 5
                and all(text.strip() and len(text) <= 12_000 for text in self._excerpts)
                and sum(map(len, self._excerpts)) <= 24_000)

    def _update_buttons(self, *_args):
        if not hasattr(self, "save_button"):
            return
        ready = self.document is not None and not self._stale and not self._busy
        for widget in (self.corrections, self.refresh_button, self.excerpt_selector,
                       self.original_consent):
            widget.setEnabled(not self._busy)
        self.excerpt_text.setReadOnly(self._busy)
        self.add_excerpt_button.setEnabled(not self._busy and len(self._excerpts) < 5)
        self.remove_excerpt_button.setEnabled(not self._busy and len(self._excerpts) > 1)
        self.prepare_button.setEnabled(
            ready and self._valid_inputs() and self.original_consent.isChecked(),
        )
        can_generate = bool(ready and self.prepared is not None
                            and self._reviewed_backend is not None
                            and self.tabs.currentIndex() == 1)
        self.generate_consent.setEnabled(can_generate)
        self.generate_button.setEnabled(can_generate and self.generate_consent.isChecked())
        can_save = bool(ready and self.preview is not None and self.tabs.currentIndex() == 2)
        self.confirm.setEnabled(can_save)
        self.save_button.setEnabled(can_save and self.confirm.isChecked())
        self.input_counts.setText(bi(
            f"{len(self.selected_ids())}/10 corrections · {len(self._excerpts)}/5 excerpts · "
            f"{sum(map(len, self._excerpts))}/24,000 characters",
            f"已选 {len(self.selected_ids())}/10 条更正 · {len(self._excerpts)}/5 段摘录 · "
            f"共 {sum(map(len, self._excerpts))}/24,000 字符",
        ))

    def _invalidate_request(self):
        self.prepared = self.generated_proposal = self.preview = None
        self._reviewed_backend = self._reviewed_recipient = None
        self.request_text.clear()
        self.recipient.clear()
        self.preview_text.clear()
        self.generate_consent.setChecked(False)
        self.confirm.setChecked(False)

    def _inputs_changed(self, *_args):
        if self._loading:
            return
        self._invalidate_request()
        self.original_consent.setChecked(False)
        self.status.setText(bi(
            "Inputs retained. Review the excerpts and prepare a new request before generating.",
            "输入已保留。请复核摘录并准备新请求后再生成。",
        ))
        self._update_buttons()

    def _attestation_changed(self, checked):
        if not checked and not self._loading:
            self._invalidate_request()
        self._update_buttons()

    def _excerpt_edited(self):
        if self._loading:
            return
        index = self.excerpt_selector.currentIndex()
        if 0 <= index < len(self._excerpts):
            self._excerpts[index] = self.excerpt_text.toPlainText()
        self._inputs_changed()

    def _reload_excerpt_selector(self, index):
        self._loading = True
        self.excerpt_selector.clear()
        self.excerpt_selector.addItems([f"S{row + 1:03d}" for row in range(len(self._excerpts))])
        self.excerpt_selector.setCurrentIndex(index)
        self.excerpt_text.setPlainText(self._excerpts[index])
        self._loading = False

    def _show_excerpt(self, index):
        if self._loading or not 0 <= index < len(self._excerpts):
            return
        self._loading = True
        self.excerpt_text.setPlainText(self._excerpts[index])
        self._loading = False

    def _add_excerpt(self):
        if self._busy or len(self._excerpts) >= 5:
            return
        self._excerpts.append("")
        self._reload_excerpt_selector(len(self._excerpts) - 1)
        self._inputs_changed()

    def _remove_excerpt(self):
        if self._busy or len(self._excerpts) <= 1:
            return
        index = self.excerpt_selector.currentIndex()
        self._excerpts.pop(index)
        self._reload_excerpt_selector(min(index, len(self._excerpts) - 1))
        self._inputs_changed()

    def _show_correction(self, row):
        record = self._records.get(self.corrections.item(row).data(Qt.ItemDataRole.UserRole)) \
            if row >= 0 else None
        self.correction_details.setPlainText("" if record is None else "\n\n".join([
            bi("Original claim", "原始主张") + ": " + record.original_claim,
            bi("Correction — context only", "更正——仅为背景") + ": " + record.correction_text,
            bi("Reason", "理由") + ": " + record.reason,
        ]))

    def _tab_changed(self, _index):
        self.generate_consent.setChecked(False)
        self.confirm.setChecked(False)
        self._update_buttons()

    def refresh(self):
        if self._busy:
            return
        selected = set(self.selected_ids())
        self._invalidate_request()
        self.original_consent.setChecked(False)
        self._loading = True
        self.document = None
        self.corrections.clear()
        self.correction_details.clear()
        self._records = {}
        try:
            self.document = self.reviews.inspect(self.kind)
            records = self.reviews.list_corrections(self.kind, self.document.report_digest)
            self._records = {record.id: record for record in records}
            for record in records:
                item = QListWidgetItem(" ".join(record.original_claim.split())[:150])
                item.setData(Qt.ItemDataRole.UserRole, record.id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if record.id in selected
                                   else Qt.CheckState.Unchecked)
                self.corrections.addItem(item)
            self._stale = False
            self.status.setText(bi(
                "Pasted excerpts retained. Select current corrections and confirm original notes.",
                "粘贴的摘录已保留。请选择当前更正并确认这些是原始笔记。",
            ) if records else bi(
                "No current corrections. Save one in original evidence review first. "
                "Your pasted excerpts are retained.",
                "当前没有更正记录。请先在原报告证据复核中保存更正。粘贴的摘录已保留。",
            ))
            if selected - set(self._records):
                self.status.setText(bi(
                    "Some prior corrections no longer match this source version. Pasted excerpts "
                    "remain; explicitly choose current corrections before preparing again.",
                    "部分先前更正不再对应此源版本。粘贴的摘录仍保留；请明确选择当前更正后再准备请求。",
                ))
        except Exception:
            self._failure()
        finally:
            self._loading = False
        self._update_buttons()

    def _failure(self):
        self._stale = True
        self._invalidate_request()
        self.status.setText(bi(
            "Nothing saved or applied. Source, inputs or request could not be verified. "
            "Pasted excerpts are retained; refresh and review a new request.",
            "未保存或应用任何内容。无法校验源报告、输入或请求。粘贴的摘录已保留；"
            "请刷新并复核新请求。",
        ))
        self._update_buttons()

    def _prepare(self):
        if not self.prepare_button.isEnabled():
            return
        self._invalidate_request()
        try:
            self.prepared = self.regeneration.prepare(
                self.kind, self.selected_ids(), self._typed_excerpts(),
                expected_digest=self.document.report_digest,
            )
            self.request_text.setPlainText(self.prepared.request.model_dump_json(indent=2))
            backend = ai_backend.get_active()
            if isinstance(backend, OllamaChatBackend):
                self._reviewed_backend, self._reviewed_recipient = backend, backend.recipient
                self.recipient.setText(bi("Local recipient: ", "本地接收方：") + backend.recipient)
            else:
                self.recipient.setText(bi(
                    "Connect local Ollama, then review the request again.",
                    "请先连接本地 Ollama，再重新复核请求。",
                ))
            self.tabs.setCurrentIndex(1)
            self.status.setText(bi(
                "Request ready; no model call made.", "请求已就绪，尚未调用模型。",
            ))
        except Exception:
            self._failure()
        self._update_buttons()

    def _request_still_current(self, prepared, backend, recipient):
        if (not self.original_consent.isChecked() or self.prepared != prepared
                or ai_backend.get_active() is not backend or backend.recipient != recipient):
            return False
        fresh = self.regeneration.prepare(
            self.kind, self.selected_ids(), self._typed_excerpts(),
            expected_digest=self.document.report_digest,
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
        self.generated_proposal = self.preview = None
        self.preview_text.clear()
        self.generate_consent.setChecked(False)
        self.confirm.setChecked(False)
        self._update_buttons()
        self.status.setText(bi(
            "Generating locally. Cancel discards the reply and waits safely for the worker.",
            "正在本地生成。取消将丢弃回复，并安全等待后台任务结束。",
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
            proposal = FullRegenerationProposal.model_validate(proposal)
            if (proposal.context_digest != prepared.context_digest
                    or proposal.request_digest != prepared.request_digest
                    or proposal.correction_ids != prepared.correction_ids
                    or proposal.excerpts != prepared.excerpts):
                self._failure()
                return
            self.preview = self.service.preview_full_regeneration(
                self.kind, proposal, expected_digest=self.document.report_digest,
            )
            self.generated_proposal = proposal
            self.preview_text.setPlainText(self.preview.detailed_markdown or self.preview.markdown)
            self.tabs.setCurrentIndex(2)
            canonical = proposal.bundle.get("report", proposal.bundle.get("criteria", {}))
            claim_count = sum(len(canonical.get(group, []))
                              for group in ("claims", "stated", "revealed"))
            self.status.setText(bi(
                "Unsaved full bilingual preview. Read evidence and uncertainty before confirming "
                "a separate save. No report has been activated.",
                "当前为尚未保存的完整双语预览。请阅读证据与不确定性，再确认单独保存。未启用任何报告。",
            ) if claim_count else bi(
                "The model returned no supported claims. Review the limitations in both languages; "
                "this unsaved preview is not a substantive finding. Nothing has been activated.",
                "模型没有返回有依据的主张。请复核两种语言中的限制说明；"
                "此未保存的预览不构成实质性发现。未启用任何内容。",
            ))
        except Exception:
            self._failure()

    @Slot(str)
    def _generation_failed(self, _private_error):
        if not self._discard_reply:
            self.status.setText(bi(
                "Local generation failed or returned an invalid report. Nothing was saved. "
                "Pasted excerpts remain; review the request before trying again.",
                "本地生成失败或返回无效报告。未保存任何内容，粘贴的摘录仍保留；请复核请求后重试。",
            ))

    def _finish_worker(self):
        if has_pending_workers(self):
            return
        self._idle_timer.stop()
        self._busy = False
        self._pending_request = None
        self._update_buttons()
        if self._close_when_idle:
            self._close_when_idle = False
            super().reject()

    def reject(self):
        if self._busy or has_pending_workers(self):
            self._discard_reply = self._close_when_idle = True
            self.generate_consent.setChecked(False)
            self.status.setText(bi(
                "Cancelled: discarding the reply and waiting for the local worker. "
                "Pasted excerpts remain unchanged.",
                "已取消：将丢弃回复，并等待本地后台任务结束。粘贴的摘录保持不变。",
            ))
            return
        super().reject()

    def closeEvent(self, event):
        if self._busy or has_pending_workers(self):
            self.reject()
            event.ignore()
            return
        super().closeEvent(event)

    def _save(self):
        if not self.save_button.isEnabled():
            return
        try:
            if not self._request_still_current(
                self.prepared, self._reviewed_backend, self._reviewed_recipient,
            ):
                self._failure()
                return
            self.saved_revision = self.service.save_full_regeneration(
                self.preview, confirmed=self.confirm.isChecked(),
            )
        except Exception:
            self._failure()
            return
        self.accept()
