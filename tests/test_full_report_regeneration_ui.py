"""Real Qt and immutable storage with synthetic excerpts and injected local replies."""

import gc
import json
import time
from threading import Event

import pytest
from anti_dating_scam_desktop import ai_backend
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.report_full_regeneration_dialog import ReportFullRegenerationDialog
from anti_dating_scam_desktop.report_revision_dialog import ReportRevisionDialog
from anti_dating_scam_desktop.workers import has_pending_workers
from PySide6.QtCore import QCoreApplication, QEvent, QSize, Qt, QThread, QTimer, Slot
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from test_full_report_regeneration import _EXCERPT, _wire_bundle
from test_report_revision_ui import _choose, _seed

from anti_dating_scam.ai.chat_backends import AnthropicChatBackend, OllamaChatBackend
from anti_dating_scam.services.active_reports import ActiveReportService


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
    until = time.monotonic() + 6
    while not predicate() and time.monotonic() < until:
        application.processEvents()
        time.sleep(0.005)
    assert predicate(), "Synthetic worker did not finish"


def _backend(
    kind="self_portrait",
    *,
    entered=None,
    release=None,
    error=False,
    malformed=False,
    empty=False,
    sources=None,
):
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append((url, payload))
        if entered:
            entered.set()
        if release:
            assert release.wait(6), "Synthetic transport was not released"
        if error:
            raise RuntimeError("synthetic private provider diagnostics")
        bundle = _wire_bundle(kind, empty=empty, sources=sources)
        return {"message": {"content": "malformed" if malformed else json.dumps(bundle)}}

    backend = OllamaChatBackend(model="synthetic-model", transport=transport)
    ai_backend.set_active(backend)
    return backend, calls


def _inputs(dialog, notes):
    _choose(dialog, notes[0].id)
    dialog.excerpt_text.setPlainText(_EXCERPT)
    dialog.original_consent.setChecked(True)


def _prepare(dialog, notes):
    _inputs(dialog, notes)
    dialog.prepare_button.click()
    assert dialog.prepared is not None


def _generate(application, dialog):
    dialog.generate_consent.setChecked(True)
    dialog.generate_button.click()
    _wait(application, lambda: not dialog._busy)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_explicit_inputs_request_preview_save_preserve_originals_and_selection(
    application,
    tmp_path,
    kind,
    language,
):
    notes = _seed(tmp_path, kind)
    active = ActiveReportService(tmp_path)
    active.select(
        active.preview_selection(
            kind,
            None,
            expected_selection_version=active.get_selection(kind).selection_version,
        ),
        confirmed=True,
    )
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    _, calls = _backend(kind)
    set_language(language, persist=False)
    dialog = ReportFullRegenerationDialog(tmp_path, kind)
    assert not calls and not dialog.prepare_button.isEnabled()
    assert not dialog.original_consent.isChecked() and not dialog.confirm.isChecked()
    _inputs(dialog, notes)
    dialog.prepare_button.click()
    assert not calls and not dialog.generate_consent.isChecked()
    assert dialog.request_text.isReadOnly()
    assert json.loads(dialog.request_text.toPlainText()) == dialog.prepared.request.model_dump(
        mode="json",
    )
    assert _EXCERPT in dialog.request_text.toPlainText()
    assert notes[0].correction_text in dialog.request_text.toPlainText()
    assert "S001" in dialog.request_text.toPlainText()
    assert not dialog.generate_button.isEnabled()
    _generate(application, dialog)
    assert len(calls) == 1 and dialog.preview is not None
    assert dialog.preview.operation == "regenerate_report"
    assert dialog.preview_text.isReadOnly() and not dialog.confirm.isChecked()
    assert dialog.preview.proposal.origin == "ai_regenerated"
    assert not (tmp_path / "reports/reviewed_copies").exists()
    assert not dialog.save_button.isEnabled()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert dialog.saved_revision is not None
    saved = dialog.service.read_revision(kind, dialog.saved_revision.id)
    assert saved == dialog.preview
    assert saved.proposal.excerpts[0].text == _EXCERPT
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert ActiveReportService(tmp_path).resolve(kind).revision_id is None
    assert len(calls) == 1
    dialog.close()


@pytest.mark.parametrize("step", ["original", "generation", "saving"])
def test_each_confirmation_is_separate_and_unchecked(application, tmp_path, step):
    notes = _seed(tmp_path)
    _, calls = _backend()
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.excerpt_text.setPlainText(_EXCERPT)
    if step == "original":
        dialog.prepare_button.click()
        assert dialog.prepared is None and not calls
    else:
        dialog.original_consent.setChecked(True)
        dialog.prepare_button.click()
        if step == "generation":
            dialog.generate_button.click()
            assert not calls and dialog.preview is None
        else:
            _generate(application, dialog)
            assert dialog.preview is not None
            dialog.save_button.click()
            assert dialog.saved_revision is None
    assert not (tmp_path / "reports/reviewed_copies").exists()
    dialog.close()


@pytest.mark.parametrize("invalid", ["empty", "whitespace", "too_long", "total"])
def test_invalid_excerpt_bounds_prevent_request_preparation(application, tmp_path, invalid):
    notes = _seed(tmp_path)
    _, calls = _backend()
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    text = {"empty": "", "whitespace": " \n ", "too_long": "a" * 12_001, "total": "a" * 12_000}[
        invalid
    ]
    dialog.excerpt_text.setPlainText(text)
    if invalid == "total":
        dialog.add_excerpt_button.click()
        dialog.excerpt_text.setPlainText("b" * 12_000)
        dialog.add_excerpt_button.click()
        dialog.excerpt_text.setPlainText("c")
    dialog.original_consent.setChecked(True)
    assert not dialog.prepare_button.isEnabled()
    assert not calls
    dialog.close()


def test_excerpt_add_remove_order_and_drafts_preserve_exact_text(application, tmp_path):
    notes = _seed(tmp_path)
    _backend(sources=["S001", "S002"])
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _inputs(dialog, notes)
    dialog.add_excerpt_button.click()
    second = " \nSecond synthetic original excerpt.  "
    dialog.excerpt_text.setPlainText(second)
    assert dialog.excerpt_selector.currentText() == "S002"
    assert not dialog.original_consent.isChecked()
    dialog.excerpt_selector.setCurrentIndex(0)
    assert dialog.excerpt_text.toPlainText() == _EXCERPT
    dialog.excerpt_selector.setCurrentIndex(1)
    assert dialog.excerpt_text.toPlainText() == second
    dialog.original_consent.setChecked(True)
    dialog.prepare_button.click()
    assert [excerpt.text for excerpt in dialog.prepared.excerpts] == [_EXCERPT, second]
    dialog.tabs.setCurrentIndex(0)
    dialog.remove_excerpt_button.click()
    assert dialog._excerpts == [_EXCERPT] and dialog.prepared is None
    for number in range(4):
        dialog.add_excerpt_button.click()
        dialog.excerpt_text.setPlainText(f"Synthetic excerpt {number + 2}.")
    assert dialog.excerpt_selector.count() == 5 and not dialog.add_excerpt_button.isEnabled()
    assert dialog.excerpt_selector.currentText() == "S005"
    dialog.close()


@pytest.mark.parametrize(
    "change", ["excerpt", "correction", "attestation", "request", "source", "backend"]
)
def test_changes_while_worker_runs_reject_reply_and_preserve_pasted_inputs(
    application,
    tmp_path,
    change,
):
    notes = _seed(tmp_path)
    entered, release = Event(), Event()
    _, calls = _backend(entered=entered, release=release)
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes)
    dialog.generate_consent.setChecked(True)
    dialog.generate_button.click()
    expected_text = _EXCERPT
    try:
        _wait(application, entered.is_set)
        assert dialog._busy and has_pending_workers(dialog)
        assert dialog.excerpt_text.isReadOnly() and not dialog.corrections.isEnabled()
        if change == "excerpt":
            expected_text = _EXCERPT + " User changed the excerpt."
            dialog.excerpt_text.setPlainText(expected_text)
        elif change == "correction":
            _choose(dialog, notes[1].id)
        elif change == "attestation":
            dialog.original_consent.setChecked(False)
        elif change == "request":
            dialog.prepared.request.response_schema["description"] = "changed request"
        elif change == "source":
            path = tmp_path / "reports/self_portrait.json"
            path.write_bytes(path.read_bytes() + b" ")
        else:
            ai_backend.set_active(OllamaChatBackend(model="different-synthetic-model"))
    finally:
        release.set()
        _wait(application, lambda: not dialog._busy)
    assert len(calls) == 1
    assert dialog.preview is None and dialog.generated_proposal is None
    assert dialog.excerpt_text.toPlainText() == expected_text
    assert not dialog.save_button.isEnabled() and dialog.saved_revision is None
    dialog.close()


@pytest.mark.parametrize(
    "change", ["excerpt", "correction", "attestation", "tab", "source", "backend", "refresh"]
)
def test_changes_after_preview_prevent_unreviewed_save(application, tmp_path, change):
    notes = _seed(tmp_path)
    _backend()
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes)
    _generate(application, dialog)
    assert dialog.preview is not None
    dialog.confirm.setChecked(True)
    if change == "excerpt":
        dialog.excerpt_text.setPlainText(_EXCERPT + " Edited input.")
    elif change == "correction":
        _choose(dialog, notes[1].id)
    elif change == "attestation":
        dialog.original_consent.setChecked(False)
    elif change == "tab":
        dialog.tabs.setCurrentIndex(0)
        dialog.tabs.setCurrentIndex(2)
    elif change == "source":
        path = tmp_path / "reports/self_portrait_localization.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "backend":
        ai_backend.set_active(OllamaChatBackend(model="different-synthetic-model"))
    else:
        dialog.refresh()
    dialog.save_button.click()
    assert dialog.saved_revision is None and not dialog.confirm.isChecked()
    assert _EXCERPT in dialog.excerpt_text.toPlainText()
    assert not (tmp_path / "reports/reviewed_copies").exists()
    dialog.close()


@pytest.mark.parametrize("action", ["escape", "close"])
def test_cancel_discards_reply_and_waits_until_worker_settles(application, tmp_path, action):
    notes = _seed(tmp_path)
    entered, release = Event(), Event()
    _backend(entered=entered, release=release)
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    dialog.show()
    _prepare(dialog, notes)
    dialog.generate_consent.setChecked(True)
    dialog.generate_button.click()
    try:
        _wait(application, entered.is_set)
        if action == "escape":
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
        else:
            dialog.close()
        application.processEvents()
        assert dialog.isVisible() and dialog._discard_reply and has_pending_workers(dialog)
    finally:
        release.set()
        _wait(application, lambda: not dialog._busy)
    assert not dialog.isVisible() and dialog.preview is None
    assert dialog._excerpts == [_EXCERPT] and dialog.saved_revision is None


@pytest.mark.parametrize("failure", ["error", "malformed"])
def test_generation_failure_keeps_inputs_and_hides_provider_diagnostics(
    application,
    tmp_path,
    failure,
):
    notes = _seed(tmp_path)
    _backend(error=failure == "error", malformed=failure == "malformed")
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes)
    _generate(application, dialog)
    assert dialog._excerpts == [_EXCERPT] and dialog.preview is None
    assert "private provider" not in dialog.status.text()
    assert not dialog.generate_consent.isChecked()
    dialog.close()


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_empty_claims_have_explicit_nonfinding_notice(application, tmp_path, kind):
    notes = _seed(tmp_path, kind)
    _backend(kind, empty=True)
    dialog = ReportFullRegenerationDialog(tmp_path, kind)
    _prepare(dialog, notes)
    _generate(application, dialog)
    assert dialog.preview is not None
    assert "no supported claims" in dialog.status.text()
    assert "not a substantive finding" in dialog.status.text()
    assert not dialog.confirm.isChecked()
    dialog.close()


@pytest.mark.parametrize("external", [False, True])
def test_only_connected_local_model_can_generate(application, tmp_path, external):
    notes = _seed(tmp_path)
    if external:
        ai_backend.set_active(AnthropicChatBackend(api_key="synthetic-not-a-key"))
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    _prepare(dialog, notes)
    dialog.generate_consent.setChecked(True)
    assert not dialog.generate_button.isEnabled() and not dialog.generate_consent.isEnabled()
    assert "Ollama" in dialog.recipient.text()
    dialog.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_all_tabs_fit_small_windows(application, tmp_path, language, size):
    notes = _seed(tmp_path)
    _backend()
    set_language(language, persist=False)
    dialog = ReportFullRegenerationDialog(tmp_path, "self_portrait")
    dialog.resize(*size)
    dialog.show()
    _prepare(dialog, notes)
    _generate(application, dialog)
    for index in range(dialog.tabs.count()):
        dialog.tabs.setCurrentIndex(index)
        application.processEvents()
        assert dialog.size() == QSize(*size)
        assert dialog.rect().contains(dialog.save_button.geometry().center())
        assert dialog.rect().contains(dialog.close_button.geometry().center())
    dialog.close()


def test_entry_keeps_existing_flows_and_does_not_call_model(application, tmp_path, monkeypatch):
    _seed(tmp_path)
    _, calls = _backend()
    seen = []

    def inspect_and_cancel(dialog):
        seen.append(dialog)
        assert dialog.saved_revision is None and dialog.kind == "self_portrait"
        assert not calls
        return dialog.DialogCode.Rejected

    monkeypatch.setattr(ReportFullRegenerationDialog, "exec", inspect_and_cancel)
    parent = ReportRevisionDialog(tmp_path, "self_portrait")
    assert parent.replacement_button.isEnabled() and parent.ai_replacement_button.isEnabled()
    QTimer.singleShot(0, parent.full_regeneration_button.click)
    application.processEvents()
    assert len(seen) == 1 and not calls and not parent.confirm.isChecked()
    assert parent.service.list_revisions("self_portrait") == []
    parent.close()


def test_repeated_dialog_callbacks_use_ui_thread_and_settle_before_deletion(application, tmp_path):
    notes = _seed(tmp_path)
    observed = []

    class ObservedDialog(ReportFullRegenerationDialog):
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
        _prepare(dialog, notes)
        _generate(application, dialog)
        assert not has_pending_workers(dialog)
        dialog.close()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        del dialog
        gc.collect()
        application.processEvents()
    assert observed == [("failed" if attempt % 2 else "ok", True) for attempt in range(8)]
