"""Synthetic Qt withdrawal-preview/save flows using the real local services."""

import json
from pathlib import Path

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.report_review_dialog import ReportReviewDialog
from anti_dating_scam_desktop.report_revision_dialog import ReportRevisionDialog
from anti_dating_scam_desktop.screens.criteria_viewer_screen import CriteriaViewerScreen
from anti_dating_scam_desktop.screens.self_portrait_viewer_screen import SelfPortraitViewerScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.report_review import ReportReviewService


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def english_ui():
    previous = current_language()
    set_language("en", persist=False)
    yield
    set_language(previous, persist=False)


def _seed(vault, kind="self_portrait", *, first="I need time to reflect."):
    claims = [{
        "topic": "communication", "claim": text, "type": "observation", "confidence": "low",
        "evidence": [{"quote": text, "source": "synthetic-note"}],
    } for text in (first, "I prefer clear communication.")]
    common = {
        "report_type": kind, "open_questions": [], "caveats": ["Synthetic evidence is limited."],
    }
    if kind == "self_portrait":
        canonical = {"report": {
            **common, "schema_version": "0.2", "claims": claims,
            "data_coverage": {"sources_read": ["synthetic-note"], "covered": [], "not_covered": []},
            "consistency_findings": [],
        }}
        source = canonical["report"]
    else:
        canonical = {
            "criteria": {**common, "schema_version": "0.1", "stated": claims, "revealed": []},
            "ideal_profiles": {"schema_version": "0.1", "candidates": [],
                               "caveats": ["No real person is described."]},
        }
        source = canonical["criteria"]
    directory = vault / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{kind}.json").write_text(json.dumps(source), encoding="utf-8")
    if kind == "mate_criteria":
        (directory / "ideal_partner_profiles.json").write_text(
            json.dumps(canonical["ideal_profiles"]), encoding="utf-8",
        )
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成中文译文第{index}项"}
        for index, (path, text) in enumerate(required_localization_sources(kind, canonical).items())
    ]
    (directory / f"{kind}_localization.json").write_text(
        json.dumps({"schema_version": "0.1", "localized_text": entries}), encoding="utf-8",
    )
    service = ReportReviewService(vault)
    document = service.inspect(kind)
    return [service.record_correction(
        kind, expected_digest=document.report_digest, target_path=claim.path,
        correction_text="This claim misses context and should be withdrawn.",
        reason="A fictional note does not support the interpretation.", confirmed=True,
    ) for claim in document.claims]


def _choose(dialog, record_id, checked=True):
    for index in range(dialog.corrections.count()):
        item = dialog.corrections.item(index)
        if item.data(Qt.ItemDataRole.UserRole) == record_id:
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            return
    raise AssertionError("Expected synthetic correction was not offered")


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_explicit_selection_preview_save_reopen_preserves_sources(
    application, tmp_path, kind, language,
):
    notes = _seed(tmp_path, kind)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*.json")}
    set_language(language, persist=False)
    dialog = ReportRevisionDialog(tmp_path, kind)
    assert dialog.document is not None
    assert dialog.selected_ids() == []
    assert not dialog.preview_button.isEnabled()
    assert not dialog.save_button.isEnabled()
    _choose(dialog, notes[0].id)
    assert dialog.preview_button.isEnabled()
    assert not dialog.save_button.isEnabled()
    dialog.preview_button.click()
    assert dialog.preview is not None
    assert "English" in dialog.preview_text.toPlainText()
    assert "中文版" in dialog.preview_text.toPlainText()
    assert notes[0].original_claim in dialog.removed.toPlainText()
    assert not (tmp_path / "reports" / "reviewed_copies").exists()
    assert not dialog.save_button.isEnabled()
    dialog.confirm.setChecked(True)
    assert dialog.service.list_revisions(kind) == []
    dialog.save_button.click()
    saved = dialog.service.list_revisions(kind)
    assert len(saved) == 1
    assert not dialog.save_button.isEnabled()
    assert dialog.saved_text.toPlainText()
    for path, data in before.items():
        assert path.read_bytes() == data
    dialog.close()
    reopened = ReportRevisionDialog(tmp_path, kind)
    assert reopened.history.count() == 1
    reopened.history.setCurrentRow(0)
    verified = reopened.service.read_revision(kind, saved[0].id)
    assert reopened.saved_text.toPlainText() == (verified.detailed_markdown or verified.markdown)
    reopened.close()


def test_cancel_after_preview_writes_no_copy(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.close_button.click()
    assert dialog.service.list_revisions("self_portrait") == []
    assert not (tmp_path / "reports" / "reviewed_copies").exists()


def test_selection_and_tab_changes_invalidate_confirmation(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    assert dialog.save_button.isEnabled()
    dialog.tabs.setCurrentIndex(2)
    assert not dialog.confirm.isChecked()
    assert not dialog.save_button.isEnabled()
    dialog.tabs.setCurrentIndex(1)
    dialog.confirm.setChecked(True)
    _choose(dialog, notes[1].id)
    assert dialog.preview is None
    assert not dialog.preview_text.toPlainText()
    assert not dialog.confirm.isChecked()
    assert not dialog.save_button.isEnabled()
    dialog.close()


def test_stale_companion_requires_refresh_and_preserves_selection(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    assert dialog.preview is not None
    dialog.confirm.setChecked(True)
    companion = tmp_path / "reports" / "self_portrait_localization.json"
    companion.write_bytes(companion.read_bytes() + b"\n")
    dialog.save_button.click()
    assert "No copy was saved" in dialog.status.text()
    assert dialog.selected_ids() == [notes[0].id]
    assert not dialog.preview_button.isEnabled()
    assert not dialog.save_button.isEnabled()
    assert dialog.service.list_revisions("self_portrait") == []
    dialog.refresh_button.click()
    assert dialog.selected_ids() == [notes[0].id]
    assert dialog.preview is None
    assert not dialog.confirm.isChecked()
    dialog.preview_button.click()
    assert dialog.preview is not None
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert len(dialog.service.list_revisions("self_portrait")) == 1
    dialog.close()


def test_old_selection_remembered_and_saved_copy_reopens_after_regeneration(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    original_saved_text = dialog.saved_text.toPlainText()
    _seed(tmp_path, first="I prefer a different pace in some situations.")
    dialog.refresh_button.click()
    assert notes[0].id not in dialog.selected_ids()
    assert notes[0].original_claim in dialog.unavailable.toPlainText()
    assert not dialog.unavailable.isHidden()
    assert dialog.history.count() == 1
    dialog.history.setCurrentRow(0)
    assert dialog.saved_text.toPlainText() == original_saved_text
    dialog.close()


def test_untrusted_notes_and_previews_are_plain_text(application, tmp_path):
    unsafe = '<img src="https://synthetic.invalid/pixel"> [open](file:///synthetic) <b>literal</b>'
    notes = _seed(tmp_path, first=unsafe)
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    assert unsafe in dialog.removed.toPlainText()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    readers = (dialog.correction_details, dialog.removed, dialog.preview_text, dialog.saved_text)
    for reader in readers:
        block = reader.document().begin()
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


def test_missing_localization_refuses_preview_preserving_selection(application, tmp_path):
    notes = _seed(tmp_path)
    (tmp_path / "reports" / "self_portrait_localization.json").unlink()
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    assert dialog.preview is None
    assert dialog.selected_ids() == [notes[0].id]
    assert "localization file is required" in dialog.status.text()
    assert not dialog.save_button.isEnabled()
    assert not (tmp_path / "reports" / "reviewed_copies").exists()
    dialog.close()


def test_tampered_saved_copy_is_never_displayed(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportRevisionDialog(tmp_path, "self_portrait")
    _choose(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    saved = dialog.service.list_revisions("self_portrait")[0]
    Path(saved.markdown_path).write_text("UNVERIFIED synthetic tampering", encoding="utf-8")
    dialog.history.setCurrentRow(-1)
    dialog.history.setCurrentRow(0)
    assert "cannot be verified" in dialog.saved_text.toPlainText()
    assert "UNVERIFIED" not in dialog.saved_text.toPlainText()
    dialog.close()


@pytest.mark.parametrize("screen_type,kind", [
    (SelfPortraitViewerScreen, "self_portrait"), (CriteriaViewerScreen, "mate_criteria"),
])
def test_viewer_review_path_opens_copy_dialog_and_preserves_annotation_draft(
    application, tmp_path, screen_type, kind,
):
    _seed(tmp_path, kind)
    store = ProfileStore(tmp_path, config_path=tmp_path / "synthetic-config.json")
    screen = screen_type(None, store, lambda: None)
    seen = []

    def open_copy():
        review = application.activeModalWidget()
        try:
            if isinstance(review, ReportReviewDialog):
                review.correction.setPlainText("Unsaved annotation draft")

                def inspect_copy():
                    copy = application.activeModalWidget()
                    try:
                        if isinstance(copy, ReportRevisionDialog):
                            seen.append((copy.kind, copy.corrections.count(), copy.selected_ids()))
                    finally:
                        if copy is not None:
                            copy.reject()

                QTimer.singleShot(20, inspect_copy)
                review.revision_button.click()
                seen.append(review.correction.toPlainText())
        finally:
            if review is not None:
                review.reject()

    QTimer.singleShot(20, open_copy)
    screen.review_button.click()
    assert seen == [(kind, 2, []), "Unsaved annotation draft"]
    screen.close()
