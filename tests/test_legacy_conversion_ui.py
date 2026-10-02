"""Synthetic actual-service Qt conversion, separate selection and intentional disable flows."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.legacy_conversion_dialog import LegacyConversionDialog
from anti_dating_scam_desktop.legacy_report_dialog import LegacyReportDialog
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.report_selection_dialog import ReportSelectionDialog
from anti_dating_scam_desktop.screens.criteria_viewer_screen import CriteriaViewerScreen
from anti_dating_scam_desktop.screens.self_portrait_viewer_screen import SelfPortraitViewerScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit
from test_self_portrait_html import SAMPLE

from anti_dating_scam.services.active_reports import ActiveReportService, LegacyReviewOnlyError
from anti_dating_scam.services.legacy_reports import LegacyReportService


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def english_ui():
    previous = current_language()
    set_language("en", persist=False)
    yield
    set_language(previous, persist=False)


def _seed(vault, kind="self_portrait", *, incomplete=False):
    reports = vault / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    claim = {
        "topic": "communication", "claim": {
            "en": "May prefer quiet time.", "zh": "可能偏好安静时间。",
        },
        "type": "inference", "confidence": "low",
        "evidence": [{"quote": "I need quiet time.", "source": "synthetic-note"}],
    }
    payload = {
        "schema_version": "0.3", "claims": [claim],
        "caveats": [{"en": "Synthetic and uncertain.", "zh": "合成且不确定。"}],
        "unknown_field": {"preserve_me": ["ARCHIVE_ONLY_SYNTHETIC", None]},
    }
    if kind == "mate_criteria":
        claim["criterion"] = claim.pop("claim")
        payload["schema_version"] = "0.1"
        payload["stated_criteria"] = payload.pop("claims")
        payload["revealed_criteria"] = []
    if incomplete:
        if kind == "self_portrait":
            payload = deepcopy(SAMPLE)
        else:
            claim.pop("confidence")
    raw = b"\xef\xbb\xbf" + (json.dumps(payload, ensure_ascii=False) + "\r\n ").encode()
    (reports / f"{kind}.json").write_bytes(raw)
    (reports / f"{kind}.md").write_bytes(b"# Original synthetic narrative\r\n")
    service = LegacyReportService(vault)
    preview = service.preview_archive(kind, expected_digest=service.inspect(kind).source_digest)
    return service.save_archive(preview, confirmed=True)


def _save(dialog):
    dialog.preview_button.click()
    assert dialog.preview is not None and dialog.preview.eligible
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert dialog.saved_conversion is not None
    return dialog.saved_conversion


def _choose(dialog, value):
    for row in range(dialog.choices.count()):
        actual = dialog.choices.item(row).data(Qt.ItemDataRole.UserRole)
        if actual == value or isinstance(actual, list) and tuple(actual) == value:
            dialog.choices.setCurrentRow(row)
            return
    raise AssertionError("Synthetic choice missing")


def _use(dialog, value):
    _choose(dialog, value)
    dialog.preview_button.click()
    assert dialog.preview is not None
    dialog.confirm.setChecked(True)
    dialog.use_button.click()
    assert dialog.result() == QDialogAccepted


QDialogAccepted = 1


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_preview_save_reopen_is_partial_and_never_activates_or_overwrites(
    application, tmp_path, kind, language,
):
    archive = _seed(tmp_path, kind)
    original = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    set_language(language, persist=False)
    dialog = LegacyConversionDialog(tmp_path, kind, archive_id=archive.id)
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    dialog.preview_button.click()
    assert dialog.preview.eligible and dialog.preview.converted_count == 1
    assert "unknown_field" in dialog.review_text.toPlainText()
    assert "English" in dialog.report_text.toPlainText()
    assert "中文版" in dialog.report_text.toPlainText()
    assert "ARCHIVE_ONLY_SYNTHETIC" not in dialog.report_text.toPlainText()
    assert "I need quiet time" in dialog.report_text.toPlainText()
    assert not dialog.service.list_conversions(kind)
    dialog.confirm.setChecked(True)
    dialog.tabs.setCurrentIndex(1)
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    saved = dialog.saved_conversion
    assert saved is not None and dialog.history.count() == 1
    assert not (tmp_path / "reports/active_selections").exists()
    assert all(path.read_bytes() == raw for path, raw in original.items())
    assert dialog.preview is None and not dialog.confirm.isChecked()
    dialog.close()
    (tmp_path / "reports" / f"{kind}.json").write_bytes(b"Changed synthetic original")
    reopened = LegacyConversionDialog(tmp_path, kind)
    assert reopened.history.count() == 1
    reopened.history.setCurrentRow(0)
    assert "I need quiet time" in reopened.saved_text.toPlainText()
    assert "Changed synthetic original" not in reopened.saved_text.toPlainText()
    reopened.close()


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_real_sparse_legacy_shape_is_blocked_without_empty_success(application, tmp_path, kind):
    archive = _seed(tmp_path, kind, incomplete=True)
    dialog = LegacyConversionDialog(tmp_path, kind, archive_id=archive.id)
    dialog.preview_button.click()
    assert dialog.preview is not None and not dialog.preview.eligible
    assert dialog.preview.converted_count == 0
    assert not dialog.confirm.isEnabled() and not dialog.save_button.isEnabled()
    assert "No complete supported claim" in dialog.status.text()
    dialog.confirm.setChecked(True)
    dialog._save()
    assert dialog.saved_conversion is None
    assert not (tmp_path / "reports/converted_reports").exists()
    assert not (tmp_path / "reports/active_selections").exists()
    dialog.close()


def test_source_change_refuses_save_and_refresh_retains_archive_without_consent(
    application, tmp_path,
):
    archive = _seed(tmp_path)
    dialog = LegacyConversionDialog(tmp_path, "self_portrait", archive_id=archive.id)
    dialog.preview_button.click()
    preview = dialog.preview
    dialog.confirm.setChecked(True)
    (tmp_path / "reports/self_portrait.html").write_text("New synthetic companion")
    dialog.save_button.click()
    assert dialog.saved_conversion is None and dialog.preview == preview
    assert "stale" in dialog.status.text()
    assert not dialog.preview_button.isEnabled() and not dialog.save_button.isEnabled()
    dialog.refresh_button.click()
    assert dialog.archives.currentRow() == 0
    assert dialog.preview is None and not dialog.confirm.isChecked()
    dialog.preview_button.click()
    assert dialog.preview is None and not dialog.save_button.isEnabled()
    assert not (tmp_path / "reports/converted_reports").exists()
    dialog.close()


def test_cancel_and_changed_archive_reset_confirmation_without_writes(application, tmp_path):
    first = _seed(tmp_path)
    _seed(tmp_path)
    dialog = LegacyConversionDialog(tmp_path, "self_portrait", archive_id=first.id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.archives.setCurrentRow(1 - dialog.archives.currentRow())
    assert dialog.preview is None and not dialog.confirm.isChecked()
    assert not dialog.save_button.isEnabled()
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.close_button.click()
    assert not (tmp_path / "reports/converted_reports").exists()


@pytest.mark.parametrize("kind,screen_type", [
    ("self_portrait", SelfPortraitViewerScreen), ("mate_criteria", CriteriaViewerScreen),
])
def test_explicit_conversion_use_then_review_only_disables_references_and_can_reselect(
    application, tmp_path, kind, screen_type,
):
    archive = _seed(tmp_path, kind)
    conversion = LegacyConversionDialog(tmp_path, kind, archive_id=archive.id)
    saved = _save(conversion)
    active = ActiveReportService(tmp_path)
    assert active.resolve(kind) is None
    selection = ReportSelectionDialog(tmp_path, kind)
    _use(selection, ("conversion", saved.id))
    assert active.resolve(kind).conversion_id == saved.id
    store = ProfileStore(tmp_path, config_path=tmp_path / "synthetic-settings.json")
    screen = screen_type(None, store, lambda: None)
    screen.on_enter()
    assert "partial legacy conversion" in screen.path_label.text()
    assert screen.viewer.toPlainText() == active.resolve(kind).markdown
    assert "May prefer quiet time" in screen.viewer.toPlainText()
    assert "I need quiet time" in (
        active.resolve(kind).detailed_markdown or active.resolve(kind).markdown
    )
    assert "original" in screen.review_button.text().lower()
    disabled = ReportSelectionDialog(tmp_path, kind)
    _choose(disabled, ("review_only", None))
    assert "disabling active report references" in disabled.confirm.text()
    assert disabled.use_button.text() == "Disable report references"
    disabled.preview_button.click()
    assert active.resolve(kind).conversion_id == saved.id
    disabled.confirm.setChecked(True)
    disabled.use_button.click()
    with pytest.raises(LegacyReviewOnlyError):
        active.resolve(kind)
    screen.on_enter()
    assert not screen.viewer.toPlainText()
    assert "references to AI are disabled" in screen.path_label.text()
    assert screen.legacy_button.isEnabled()
    restored = ReportSelectionDialog(tmp_path, kind)
    _use(restored, ("conversion", saved.id))
    assert active.resolve(kind).conversion_id == saved.id
    conversion.close()
    screen.close()


def test_stale_conversion_activation_and_corrupt_conversion_allow_explicit_disable(
    application, tmp_path,
):
    archive = _seed(tmp_path)
    dialog = LegacyConversionDialog(tmp_path, "self_portrait", archive_id=archive.id)
    saved = _save(dialog)
    selection = ReportSelectionDialog(tmp_path, "self_portrait")
    _choose(selection, ("conversion", saved.id))
    selection.preview_button.click()
    selection.confirm.setChecked(True)
    (tmp_path / "reports/self_portrait.md").write_bytes(b"Changed original synthetic")
    selection.use_button.click()
    assert not (tmp_path / "reports/active_selections").exists()
    assert "changed" in selection.status.text()
    assert not selection.confirm.isChecked()
    corrupted = Path(saved.directory_path) / "preview.json"
    corrupted.write_text("UNVERIFIED_SYNTHETIC", encoding="utf-8")
    recovered = ReportSelectionDialog(tmp_path, "self_portrait")
    _use(recovered, ("review_only", None))
    with pytest.raises(LegacyReviewOnlyError):
        ActiveReportService(tmp_path).resolve("self_portrait")
    history = LegacyConversionDialog(tmp_path, "self_portrait")
    assert history.history.count() == 0
    assert "UNVERIFIED_SYNTHETIC" not in history.saved_text.toPlainText()
    dialog.close()
    history.close()


def test_saved_archive_entry_opens_conversion_with_that_archive(application, tmp_path):
    archive = _seed(tmp_path)
    parent = LegacyReportDialog(tmp_path, "self_portrait")
    parent.history.setCurrentRow(0)
    seen = []

    def inspect_modal():
        modal = application.activeModalWidget()
        try:
            if isinstance(modal, LegacyConversionDialog):
                seen.append(modal._archives[modal.archives.currentRow()].id)
        finally:
            if modal is not None:
                modal.reject()

    QTimer.singleShot(20, inspect_modal)
    parent.conversion_button.click()
    assert seen == [archive.id]
    assert not (tmp_path / "reports/converted_reports").exists()
    parent.close()


def test_conversion_readers_are_literal_and_help_is_read_only_scope(application, tmp_path):
    archive = _seed(tmp_path)
    dialog = LegacyConversionDialog(tmp_path, "self_portrait", archive_id=archive.id)
    dialog.preview_button.click()
    assert any("correction tools still target" in label.text()
               for label in dialog.findChildren(QLabel))
    for reader in dialog.findChildren(QPlainTextEdit):
        assert reader.isReadOnly()
        block = reader.document().begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                assert not fragment.charFormat().isAnchor()
                assert not fragment.charFormat().isImageFormat()
                iterator += 1
            block = block.next()
    assert all(label.textFormat() == Qt.TextFormat.PlainText
               for label in dialog.findChildren(QLabel))
    dialog.close()
