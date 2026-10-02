"""Synthetic local transport and real Qt/service boundaries; no actual model calls."""

import gc
import json
import time
from threading import Event

import pytest
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.report_ai_replacement_dialog import ReportAIReplacementDialog
from anti_dating_scam_desktop.report_revision_dialog import ReportRevisionDialog
from anti_dating_scam_desktop.workers import has_pending_workers
from PySide6.QtCore import QCoreApplication, QEvent, QSize, Qt, QThread, QTimer, Slot
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from test_report_revision_ui import _seed

from anti_dating_scam.ai.chat_backends import AnthropicChatBackend, OllamaChatBackend
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.report_revisions import AIReplacementPreview

EN = "I may sometimes prefer time to reflect; these quotations provide limited context."
ZH = "我有时可能希望留出思考时间；这些引文仅提供有限背景。"


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def isolated_ui():
    previous_language, previous_backend = current_language(), ai_backend.get_active()
    set_language("en", persist=False)
    ai_backend.set_active(None)
    yield
    ai_backend.set_active(previous_backend)
    set_language(previous_language, persist=False)


def _wait(application, predicate):
    until = time.monotonic() + 5
    while not predicate() and time.monotonic() < until:
        application.processEvents()
        time.sleep(0.005)
    assert predicate(), "Synthetic worker did not finish"


def _backend(*, entered=None, release=None, error=False, malformed=False):
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append((url, payload))
        if entered:
            entered.set()
        if release:
            assert release.wait(5), "Synthetic transport was not released"
        if error:
            raise RuntimeError("synthetic private diagnostics must not appear")
        return {"message": {"content": "invalid" if malformed else json.dumps({
            "text_en": EN, "text_zh": ZH,
        })}}

    backend = OllamaChatBackend(model="synthetic-test-model", transport=transport)
    ai_backend.set_active(backend)
    return backend, calls


def _choose(dialog, note):
    for row in range(dialog.corrections.count()):
        if dialog.corrections.item(row).data(Qt.ItemDataRole.UserRole) == note.id:
            dialog.corrections.setCurrentRow(row)
            return
    raise AssertionError("Synthetic correction not offered")


def _prepare(dialog, note):
    _choose(dialog, note)
    dialog.prepare_button.click()
    assert dialog.prepared is not None


def _generate(application, dialog):
    dialog.generate_consent.setChecked(True)
    dialog.generate_button.click()
    _wait(application, lambda: not dialog._busy)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_exact_review_generation_edit_preview_save_keeps_originals_and_active_report(
    application, tmp_path, kind, language,
):
    notes = _seed(tmp_path, kind)
    active = ActiveReportService(tmp_path)
    active.select(active.preview_selection(
        kind, None, expected_selection_version=active.get_selection(kind).selection_version,
    ), confirmed=True)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    _, calls = _backend()
    set_language(language, persist=False)
    dialog = ReportAIReplacementDialog(tmp_path, kind)
    assert not calls and dialog.corrections.currentRow() == -1
    assert not dialog.generate_button.isEnabled() and not dialog.save_button.isEnabled()
    _prepare(dialog, notes[0])
    assert not calls and not dialog.generate_consent.isChecked()
    assert not dialog.generate_button.isEnabled()
    assert dialog.request_text.isReadOnly()
    assert json.loads(dialog.request_text.toPlainText()) == dialog.prepared.request.model_dump(
        mode="json",
    )
    assert "SAVED_QUOTATIONS_UNVERIFIED" in dialog.request_text.toPlainText()
    assert notes[0].correction_text in dialog.request_text.toPlainText()
    _generate(application, dialog)
    assert len(calls) == 1 and dialog.text_en.toPlainText() == EN
    assert dialog.text_zh.toPlainText() == ZH and not dialog.generate_consent.isChecked()
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    assert not (tmp_path / "reports/reviewed_copies").exists()
    dialog.text_en.setPlainText(EN + " Human-reviewed wording remains provisional.")
    dialog.preview_button.click()
    preview = dialog.preview
    assert isinstance(preview, AIReplacementPreview)
    assert preview.proposal.origin == "ai_assisted"
    assert preview.replacement_claim.confidence == "low"
    assert preview.replacement_claim.type == "speculation"
    assert preview.replacement_claim.evidence == preview.removed_claims[0].evidence
    assert "AI-assisted interpretation" in dialog.preview_text.toPlainText().replace("\\", "")
    assert "AI 辅助解释" in dialog.preview_text.toPlainText()
    assert not dialog.save_button.isEnabled()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert dialog.saved_revision is not None
    reopened = dialog.service.read_revision(kind, dialog.saved_revision.id)
    assert isinstance(reopened, AIReplacementPreview)
    assert reopened.proposal == preview.proposal
    for path, contents in before.items():
        assert path.read_bytes() == contents
    assert ActiveReportService(tmp_path).resolve(kind).revision_id is None
    assert len(calls) == 1
    dialog.close()


@pytest.mark.parametrize("backend", [None, "external"])
def test_no_local_connection_cannot_generate(application, tmp_path, backend):
    notes = _seed(tmp_path)
    if backend:
        ai_backend.set_active(AnthropicChatBackend(api_key="synthetic-not-a-key"))
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes[0])
    dialog.generate_consent.setChecked(True)
    assert not dialog.generate_button.isEnabled()
    assert not dialog.generate_consent.isEnabled()
    assert "Ollama" in dialog.recipient.text()
    dialog.close()


@pytest.mark.parametrize("change", ["source", "selection", "backend", "request"])
def test_stale_request_reply_cannot_replace_existing_draft(
    application, tmp_path, change,
):
    notes = _seed(tmp_path)
    entered, release = Event(), Event()
    backend, calls = _backend(entered=entered, release=release)
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    dialog.text_en.setPlainText("Keep my existing English draft.")
    dialog.text_zh.setPlainText("保留我的现有中文草稿。")
    _prepare(dialog, notes[0])
    dialog.generate_consent.setChecked(True)
    dialog.generate_button.click()
    try:
        _wait(application, entered.is_set)
        assert dialog._busy and has_pending_workers(dialog)
        assert not dialog.corrections.isEnabled() and not dialog.refresh_button.isEnabled()
        assert dialog.text_en.isReadOnly() and dialog.text_zh.isReadOnly()
        if change == "source":
            source = tmp_path / "reports/self_portrait.json"
            source.write_bytes(source.read_bytes() + b" ")
        elif change == "selection":
            _choose(dialog, notes[1])  # Programmatic changes must also fail closed.
        elif change == "backend":
            ai_backend.set_active(OllamaChatBackend(model="different-synthetic-model"))
        else:
            dialog.prepared.request.response_schema["description"] = "changed request"
    finally:
        release.set()
        _wait(application, lambda: not dialog._busy)
    assert len(calls) == 1
    assert dialog.text_en.toPlainText() == "Keep my existing English draft."
    assert dialog.text_zh.toPlainText() == "保留我的现有中文草稿。"
    assert dialog.generated_proposal is None and dialog.preview is None
    assert not dialog.save_button.isEnabled()
    assert not (tmp_path / "reports/reviewed_copies").exists()
    assert backend is not None
    dialog.close()


@pytest.mark.parametrize("action", ["escape", "close"])
def test_cancel_waits_for_native_worker_and_discards_reply(application, tmp_path, action):
    notes = _seed(tmp_path)
    entered, release = Event(), Event()
    _backend(entered=entered, release=release)
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    dialog.show()
    dialog.text_en.setPlainText("Keep the draft through cancellation.")
    dialog.text_zh.setPlainText("取消时保留此草稿。")
    _prepare(dialog, notes[0])
    dialog.generate_consent.setChecked(True)
    dialog.generate_button.click()
    try:
        _wait(application, entered.is_set)
        if action == "escape":
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
        else:
            dialog.close()
        application.processEvents()
        assert dialog.isVisible() and has_pending_workers(dialog)
        assert dialog._discard_reply
    finally:
        release.set()
        _wait(application, lambda: not dialog._busy)
    assert not dialog.isVisible()
    assert dialog.text_en.toPlainText() == "Keep the draft through cancellation."
    assert dialog.text_zh.toPlainText() == "取消时保留此草稿。"
    assert dialog.generated_proposal is None
    assert dialog.saved_revision is None


@pytest.mark.parametrize("failure", ["error", "malformed"])
def test_failed_generation_preserves_draft_without_provider_diagnostics(
    application, tmp_path, failure,
):
    notes = _seed(tmp_path)
    _backend(error=failure == "error", malformed=failure == "malformed")
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    dialog.text_en.setPlainText("Keep existing words.")
    dialog.text_zh.setPlainText("保留现有文字。")
    _prepare(dialog, notes[0])
    _generate(application, dialog)
    assert dialog.text_en.toPlainText() == "Keep existing words."
    assert dialog.text_zh.toPlainText() == "保留现有文字。"
    assert "private diagnostics" not in dialog.status.text()
    assert not dialog.generate_consent.isChecked()
    assert dialog.saved_revision is None
    dialog.close()


def test_edits_selection_refresh_and_tab_changes_reset_confirmation(application, tmp_path):
    notes = _seed(tmp_path)
    _backend()
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes[0])
    _generate(application, dialog)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.text_en.insertPlainText(" Perhaps.")
    assert dialog.preview is None and not dialog.confirm.isChecked()
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.tabs.setCurrentIndex(2)
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    dialog.tabs.setCurrentIndex(3)
    assert not dialog.save_button.isEnabled()
    _choose(dialog, notes[1])
    assert dialog.prepared is None and dialog.generated_proposal is None
    assert dialog.text_zh.toPlainText() == ZH and not dialog.preview_button.isEnabled()
    dialog.refresh()
    assert dialog.text_zh.toPlainText() == ZH and not dialog.preview_button.isEnabled()
    dialog.close()


@pytest.mark.parametrize("phase", ["preview", "save"])
def test_source_change_before_preview_or_save_fails_closed(application, tmp_path, phase):
    notes = _seed(tmp_path)
    _backend()
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes[0])
    _generate(application, dialog)
    if phase == "save":
        dialog.preview_button.click()
        dialog.confirm.setChecked(True)
    source = tmp_path / "reports/self_portrait.json"
    source.write_bytes(source.read_bytes() + b" ")
    if phase == "save":
        dialog.save_button.click()
    else:
        dialog.preview_button.click()
    assert dialog.preview is None and dialog._stale
    assert dialog.text_en.toPlainText() == EN and dialog.saved_revision is None
    dialog.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_all_dialog_tabs_fit_smaller_windows(application, tmp_path, language, size):
    notes = _seed(tmp_path)
    _backend()
    set_language(language, persist=False)
    dialog = ReportAIReplacementDialog(tmp_path, "self_portrait")
    dialog.resize(*size)
    dialog.show()
    _prepare(dialog, notes[0])
    for index in range(dialog.tabs.count()):
        dialog.tabs.setCurrentIndex(index)
        application.processEvents()
        assert dialog.size() == QSize(*size)
        assert dialog.rect().contains(dialog.close_button.geometry().center())
        assert dialog.rect().contains(dialog.save_button.geometry().center())
    dialog.close()


def test_revision_entry_opens_separate_ai_flow_without_running_model(
    application, tmp_path, monkeypatch,
):
    _seed(tmp_path)
    _, calls = _backend()
    seen = []

    def inspect_and_cancel(dialog):
        seen.append(dialog)
        assert dialog.kind == "self_portrait" and dialog.saved_revision is None
        assert not calls
        return dialog.DialogCode.Rejected

    monkeypatch.setattr(ReportAIReplacementDialog, "exec", inspect_and_cancel)
    parent = ReportRevisionDialog(tmp_path, "self_portrait")
    QTimer.singleShot(0, parent.ai_replacement_button.click)
    application.processEvents()
    assert len(seen) == 1 and not calls
    assert not parent.confirm.isChecked()
    assert parent.service.list_revisions("self_portrait") == []
    parent.close()


def test_repeated_dialog_worker_callbacks_stay_on_ui_thread_and_settle_before_deletion(
    application, tmp_path,
):
    notes = _seed(tmp_path)
    observed = []

    class ObservedDialog(ReportAIReplacementDialog):
        @Slot(object)
        def _generation_completed(self, proposal):
            observed.append(("ok", QThread.currentThread() == application.thread()))
            super()._generation_completed(proposal)

        @Slot(str)
        def _generation_failed(self, error):
            observed.append(("failed", QThread.currentThread() == application.thread()))
            super()._generation_failed(error)

    for attempt in range(8):
        _backend(error=bool(attempt % 2))
        dialog = ObservedDialog(tmp_path, "self_portrait")
        _prepare(dialog, notes[0])
        _generate(application, dialog)
        assert not has_pending_workers(dialog)
        dialog.close()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        del dialog
        gc.collect()
        application.processEvents()
    assert observed == [("failed" if attempt % 2 else "ok", True) for attempt in range(8)]
