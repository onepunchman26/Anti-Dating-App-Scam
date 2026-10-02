"""Actual Qt review controls and local synthetic persistence; no provider calls."""

import json

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.report_review_dialog import ReportReviewDialog
from anti_dating_scam_desktop.screens.criteria_viewer_screen import CriteriaViewerScreen
from anti_dating_scam_desktop.screens.self_portrait_viewer_screen import SelfPortraitViewerScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def english_ui():
    previous = current_language()
    set_language("en", persist=False)
    yield
    set_language(previous, persist=False)


def _write_report(
    vault, kind="self_portrait", *, text="I prefer clear communication.", source="synthetic-note",
):
    claim = {
        "topic": "values", "claim": text, "type": "observation", "confidence": "low",
        "evidence": [{"quote": text, "source": source}],
    }
    common = {"report_type": kind, "open_questions": [], "caveats": ["Synthetic limited evidence."]}
    if kind == "self_portrait":
        data = {
            **common, "schema_version": "0.2", "claims": [claim],
            "consistency_findings": [],
            "data_coverage": {
                "sources_read": [source], "covered": [], "not_covered": [],
            },
        }
    else:
        data = {**common, "schema_version": "0.1", "stated": [claim], "revealed": []}
    directory = vault / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{kind}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _draft(dialog, text="I need time to reflect before answering."):
    dialog.correction.setPlainText(text)
    dialog.reason.setPlainText("The original claim misses the context of this synthetic note.")


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_explicit_save_reopens_annotation_without_changing_report(application, tmp_path, kind):
    report = _write_report(tmp_path, kind)
    before = report.read_bytes()
    dialog = ReportReviewDialog(tmp_path, kind)
    assert dialog.document is not None
    assert not (tmp_path / "reports" / "review_history").exists()
    assert "synthetic-note" in dialog.details.toPlainText()
    assert "Low: limited support" in dialog.details.toPlainText()
    assert "Synthetic limited evidence" in dialog.details.toPlainText()
    _draft(dialog)
    assert not dialog.save_button.isEnabled()
    assert dialog.service.list_corrections(kind) == []
    dialog.confirm.setChecked(True)
    assert dialog.service.list_corrections(kind) == []
    dialog.save_button.click()
    records = dialog.service.list_corrections(kind)
    assert len(records) == 1
    assert records[0].original_claim == "I prefer clear communication."
    assert report.read_bytes() == before
    assert not dialog.correction.toPlainText()
    _draft(dialog, "A second unsaved draft")
    assert "Unsaved draft" in dialog.status.text()
    assert not dialog.confirm.isChecked()
    dialog.close()
    reopened = ReportReviewDialog(tmp_path, kind)
    assert records[0].correction_text in reopened.current_history.toPlainText()
    assert "No saved corrections" in reopened.prior_history.toPlainText()
    reopened.close()


def test_cancel_discards_only_unsaved_draft(application, tmp_path):
    report = _write_report(tmp_path)
    before = report.read_bytes()
    dialog = ReportReviewDialog(tmp_path, "self_portrait")
    _draft(dialog)
    dialog.confirm.setChecked(True)
    dialog.close_button.click()
    assert dialog.result() == dialog.DialogCode.Rejected
    assert dialog.service.list_corrections("self_portrait") == []
    assert not (tmp_path / "reports" / "review_history").exists()
    assert report.read_bytes() == before


def test_stale_write_preserves_draft_requires_refresh_and_distinguishes_history(
    application, tmp_path,
):
    _write_report(tmp_path)
    dialog = ReportReviewDialog(tmp_path, "self_portrait")
    _draft(dialog, "First version correction")
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    _draft(dialog, "Unsaved draft retained")
    dialog.confirm.setChecked(True)
    _write_report(tmp_path, text="I sometimes prefer written communication.")
    dialog.save_button.click()
    assert len(dialog.service.list_corrections("self_portrait")) == 1
    assert "not saved" in dialog.status.text()
    assert dialog.correction.toPlainText() == "Unsaved draft retained"
    assert not dialog.save_button.isEnabled()
    dialog.refresh_button.click()
    assert dialog.correction.toPlainText() == "Unsaved draft retained"
    assert dialog.claims.currentRow() == -1
    assert not dialog.confirm.isChecked()
    assert "First version correction" in dialog.prior_history.toPlainText()
    assert "First version correction" not in dialog.current_history.toPlainText()
    dialog.claims.setCurrentRow(0)
    assert not dialog.save_button.isEnabled()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    records = dialog.service.list_corrections("self_portrait")
    assert len(records) == 2
    latest = next(item for item in records if item.correction_text == "Unsaved draft retained")
    assert latest.original_claim == "I sometimes prefer written communication."
    assert "Unsaved draft retained" in dialog.current_history.toPlainText()
    dialog.close()


def test_report_and_annotation_markup_are_inert_plain_text(application, tmp_path):
    unsafe = '<img src="https://synthetic.invalid/pixel"> [open](file:///synthetic) <b>literal</b>'
    _write_report(tmp_path, text=unsafe, source=unsafe)
    dialog = ReportReviewDialog(tmp_path, "self_portrait")
    assert unsafe in dialog.details.toPlainText()
    _draft(dialog, unsafe)
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert unsafe in dialog.current_history.toPlainText()
    for editor in (dialog.details, dialog.current_history, dialog.prior_history):
        block = editor.document().begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                assert not fragment.charFormat().isAnchor()
                assert not fragment.charFormat().isImageFormat()
                iterator += 1
            block = block.next()
    assert all(
        label.textFormat() == Qt.TextFormat.PlainText for label in dialog.findChildren(QLabel)
    )
    dialog.close()


def test_legacy_invalid_report_preserves_files_and_draft(application, tmp_path):
    path = _write_report(tmp_path)
    dialog = ReportReviewDialog(tmp_path, "self_portrait")
    _draft(dialog)
    path.write_text('{"legacy": "unvalidated report"}', encoding="utf-8")
    before = path.read_bytes()
    dialog.refresh_button.click()
    assert "Regenerate" in dialog.status.text()
    assert dialog.correction.toPlainText()
    assert not dialog.save_button.isEnabled()
    assert path.read_bytes() == before
    dialog.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("screen_type,kind", [
    (SelfPortraitViewerScreen, "self_portrait"), (CriteriaViewerScreen, "mate_criteria"),
])
def test_both_viewer_buttons_open_review_for_current_vault(
    application, tmp_path, screen_type, kind, language,
):
    set_language(language, persist=False)
    store = ProfileStore(tmp_path, config_path=tmp_path / "synthetic-config.json")
    _write_report(tmp_path, kind)
    screen = screen_type(None, store, lambda: None)
    seen = []

    def inspect_modal():
        dialog = application.activeModalWidget()
        try:
            if isinstance(dialog, ReportReviewDialog) and dialog.document is not None:
                seen.append((dialog.kind, dialog.document.claims[0].claim, dialog.windowTitle()))
        finally:
            if dialog is not None:
                dialog.reject()

    QTimer.singleShot(20, inspect_modal)
    screen.review_button.click()
    assert seen == [(kind, "I prefer clear communication.",
                     "Review original evidence & corrections"
                     if language == "en" else "复核原报告证据与更正")]
    screen.close()


@pytest.mark.parametrize("screen_type,kind", [
    (SelfPortraitViewerScreen, "self_portrait"), (CriteriaViewerScreen, "mate_criteria"),
])
def test_viewer_keeps_notice_that_corrections_are_not_applied(
    application, tmp_path, screen_type, kind,
):
    store = ProfileStore(tmp_path, config_path=tmp_path / "synthetic-config.json")
    _write_report(tmp_path, kind)
    dialog = ReportReviewDialog(tmp_path, kind)
    _draft(dialog)
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    dialog.close()
    screen = screen_type(None, store, lambda: None)
    screen.on_enter()
    assert not screen.correction_banner.isHidden()
    assert "1 saved correction" in screen.correction_banner.text()
    assert "Original reports are unchanged" in screen.correction_banner.text()
    assert "not automatically applied to the active report" in screen.correction_banner.text()
    screen.close()


def test_edit_limits_and_new_selection_require_confirmation(application, tmp_path):
    _write_report(tmp_path)
    dialog = ReportReviewDialog(tmp_path, "self_portrait")
    _draft(dialog)
    dialog.confirm.setChecked(True)
    assert dialog.save_button.isEnabled()
    dialog.reason.setPlainText("x" * 2_001)
    assert not dialog.save_button.isEnabled()
    _draft(dialog)
    dialog.correction.setPlainText("x" * 8_001)
    assert not dialog.save_button.isEnabled()
    _draft(dialog)
    dialog.claims.setCurrentRow(-1)
    dialog.claims.setCurrentRow(0)
    assert not dialog.confirm.isChecked()
    assert not dialog.save_button.isEnabled()
    dialog.close()
