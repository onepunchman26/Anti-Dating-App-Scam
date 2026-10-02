"""Synthetic Qt archive/review workflows; no semantic conversion or external file opening."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.legacy_report_dialog import LegacyReportDialog
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens.criteria_viewer_screen import CriteriaViewerScreen
from anti_dating_scam_desktop.screens.self_portrait_viewer_screen import SelfPortraitViewerScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit
from test_report_revision_ui import _seed as _current_report
from test_self_portrait_html import SAMPLE

from anti_dating_scam.services.active_reports import ActiveReportService
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


def _legacy(vault, kind="self_portrait"):
    reports = vault / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    value = deepcopy(SAMPLE) if kind == "self_portrait" else {
        "report_type": "mate_criteria", "schema_version": "0.1",
        "stated_criteria": [{"criterion": {"en": "Some quiet time", "zh": "一些安静时间"},
                             "source": "interview", "evidence": ""}],
        "revealed_criteria": [], "contradictions": [], "deal_breakers": [],
        "strong_preferences": [], "flexible_preferences": [], "realism_notes": [],
        "caveats": [{"en": "Synthetic legacy", "zh": "合成旧格式"}],
    }
    value["unknown_extension"] = {"nested": [None, 1, "PRESERVE_SYNTHETIC_VALUE"]}
    raw = b"\xef\xbb\xbf" + (json.dumps(value, ensure_ascii=False, indent=3) + "\r\n  ").encode()
    (reports / f"{kind}.json").write_bytes(raw)
    (reports / f"{kind}.md").write_bytes(b"# Original synthetic prose\r\nUntouched.\r\n")
    return {path.name: path.read_bytes() for path in reports.iterdir() if path.is_file()}


def _choose_file(combo, label):
    index = combo.findData(label)
    assert index >= 0
    combo.setCurrentIndex(index)


def _save(dialog):
    dialog.preview_button.click()
    assert dialog.preview is not None
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert dialog.saved_archive is not None
    return dialog.saved_archive


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_inspect_preview_archive_reopen_preserves_exact_unknown_source_bytes(
    application, tmp_path, kind, language,
):
    originals = _legacy(tmp_path, kind)
    set_language(language, persist=False)
    dialog = LegacyReportDialog(tmp_path, kind)
    assert dialog.inspection is not None
    assert dialog.inspection.format == (
        "self_portrait_v03" if kind == "self_portrait" else "mate_criteria_legacy_v01"
    )
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    assert not (tmp_path / "reports/legacy_archives").exists()
    _choose_file(dialog.files, f"{kind}.json")
    assert "PRESERVE_SYNTHETIC_VALUE" in dialog.original_text.toPlainText()
    dialog.preview_button.click()
    assert "English" in dialog.preview_text.toPlainText()
    assert "中文版" in dialog.preview_text.toPlainText()
    assert "unknown_extension" in dialog.field_ledger.toPlainText()
    assert all(field.status == "preserved_only" for field in dialog.preview.field_ledger)
    assert not dialog.service.list_archives(kind)
    assert not dialog.save_button.isEnabled()
    preview = dialog.preview
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    saved = dialog.saved_archive
    assert saved is not None and dialog.history.count() == 1
    assert dialog.preview is None and not dialog.confirm.isChecked()
    assert not (tmp_path / "reports/active_selections").exists()
    assert not (tmp_path / "reports/reviewed_copies").exists()
    assert not (tmp_path / "reports/review_history").exists()
    for label, raw in originals.items():
        assert (tmp_path / "reports" / label).read_bytes() == raw
        assert dialog.service.read_snapshot(kind, saved.id, label) == raw
    dialog.close()
    # Saved history survives source replacement, independently of current-format readability.
    (tmp_path / "reports" / f"{kind}.json").write_bytes(b"New current source is not valid JSON")
    restarted = LegacyReportDialog(tmp_path, kind)
    assert restarted.history.count() == 1
    restarted.history.setCurrentRow(0)
    assert restarted.service.read_archive(kind, saved.id) == preview
    _choose_file(restarted.saved_files, f"{kind}.json")
    assert "PRESERVE_SYNTHETIC_VALUE" in restarted.saved_text.toPlainText()
    assert "New current source" not in restarted.saved_text.toPlainText()
    assert restarted.service.read_snapshot(kind, saved.id, f"{kind}.json") \
        == originals[f"{kind}.json"]
    restarted.close()


def test_close_after_preview_creates_no_archive_and_tab_changes_reset_confirmation(
    application, tmp_path,
):
    _legacy(tmp_path)
    dialog = LegacyReportDialog(tmp_path, "self_portrait")
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.tabs.setCurrentIndex(1)
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    dialog.tabs.setCurrentIndex(2)
    assert not dialog.save_button.isEnabled()
    dialog.confirm.setChecked(True)
    dialog.close_button.click()
    assert not (tmp_path / "reports/legacy_archives").exists()


@pytest.mark.parametrize("change", ["existing", "previously_absent"])
def test_stale_original_or_new_companion_refuses_save_until_refresh(
    application, tmp_path, change,
):
    _legacy(tmp_path)
    dialog = LegacyReportDialog(tmp_path, "self_portrait")
    dialog.preview_button.click()
    old = dialog.preview
    dialog.confirm.setChecked(True)
    path = tmp_path / "reports" / (
        "self_portrait.md" if change == "existing" else "self_portrait_localization.json"
    )
    path.write_bytes(b"Synthetic changed bytes")
    dialog.save_button.click()
    assert dialog.saved_archive is None
    assert dialog.preview == old
    assert "stale" in dialog.status.text()
    assert not dialog.save_button.isEnabled() and not dialog.preview_button.isEnabled()
    assert not (tmp_path / "reports/legacy_archives").exists()
    dialog.refresh_button.click()
    assert dialog.preview is None and not dialog.confirm.isChecked()
    saved = _save(dialog)
    assert dialog.service.read_snapshot("self_portrait", saved.id, path.name) == path.read_bytes()
    dialog.close()


def test_missing_binary_and_empty_files_are_distinguished_without_inventing_text(
    application, tmp_path,
):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "self_portrait.json").write_bytes(b"\xff\xfe\x00\x81")
    (reports / "self_portrait.md").write_bytes(b"")
    dialog = LegacyReportDialog(tmp_path, "self_portrait")
    _choose_file(dialog.files, "self_portrait.json")
    assert "not decodable UTF-8" in dialog.original_text.toPlainText()
    _choose_file(dialog.files, "self_portrait.md")
    assert dialog.original_text.toPlainText() == ""
    _choose_file(dialog.files, "self_portrait_localization.json")
    assert "absent" in dialog.original_text.toPlainText()
    saved = _save(dialog)
    _choose_file(dialog.saved_files, "self_portrait.json")
    assert "not decodable UTF-8" in dialog.saved_text.toPlainText()
    assert dialog.service.read_snapshot("self_portrait", saved.id, "self_portrait.json") \
        == b"\xff\xfe\x00\x81"
    _choose_file(dialog.saved_files, "self_portrait_localization.json")
    assert "absent" in dialog.saved_text.toPlainText()
    dialog.close()


def test_all_missing_files_cannot_create_meaningless_archive(application, tmp_path):
    dialog = LegacyReportDialog(tmp_path, "self_portrait")
    assert dialog.inspection.format == "missing"
    assert not dialog.preview_button.isEnabled() and not dialog.save_button.isEnabled()
    assert not list(tmp_path.iterdir())
    dialog.close()


def test_literal_html_markdown_and_unknown_fields_have_no_active_links_or_images(
    application, tmp_path,
):
    _legacy(tmp_path)
    unsafe = '<script>alert("synthetic")</script><img src="https://synthetic.invalid/pixel">'
    source = tmp_path / "reports/self_portrait.html"
    source.write_bytes(unsafe.encode())
    dialog = LegacyReportDialog(tmp_path, "self_portrait")
    _choose_file(dialog.files, "self_portrait.html")
    assert dialog.original_text.toPlainText() == unsafe
    _save(dialog)
    _choose_file(dialog.saved_files, "self_portrait.html")
    assert dialog.saved_text.toPlainText() == unsafe
    for reader in (dialog.diagnostics, dialog.original_text, dialog.preview_text,
                   dialog.field_ledger, dialog.saved_text):
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
    assert all(reader.isReadOnly() for reader in dialog.findChildren(QPlainTextEdit))
    dialog.close()


@pytest.mark.parametrize("kind,screen_type", [
    ("self_portrait", SelfPortraitViewerScreen), ("mate_criteria", CriteriaViewerScreen),
])
def test_both_viewers_offer_legacy_review_even_when_active_report_is_stale(
    application, tmp_path, kind, screen_type,
):
    _current_report(tmp_path, kind)
    active = ActiveReportService(tmp_path)
    active.select(active.preview_selection(
        kind, None, expected_selection_version=active.get_selection(kind).selection_version,
    ), confirmed=True)
    journal = {
        path: path.read_bytes() for path in (tmp_path / "reports/active_selections").rglob("*")
        if path.is_file()
    }
    _legacy(tmp_path, kind)
    store = ProfileStore(tmp_path, config_path=tmp_path / "synthetic-settings.json")
    screen = screen_type(None, store, lambda: None)
    screen.on_enter()
    assert not screen.viewer.toPlainText()
    assert screen.legacy_button.isEnabled()
    seen = []

    def inspect_archive_dialog():
        modal = application.activeModalWidget()
        try:
            if isinstance(modal, LegacyReportDialog):
                seen.append((modal.kind, modal.inspection.format))
        finally:
            if modal is not None:
                modal.reject()

    QTimer.singleShot(20, inspect_archive_dialog)
    screen.legacy_button.click()
    assert seen == [(kind, "self_portrait_v03" if kind == "self_portrait"
                     else "mate_criteria_legacy_v01")]
    assert all(path.read_bytes() == raw for path, raw in journal.items())
    assert not (tmp_path / "reports/legacy_archives").exists()
    screen.close()


def test_corrupt_archive_refuses_display_and_never_replaces_current_files(application, tmp_path):
    originals = _legacy(tmp_path)
    dialog = LegacyReportDialog(tmp_path, "self_portrait")
    saved = _save(dialog)
    dialog.close()
    archive_source = Path(saved.directory_path) / "self_portrait.json"
    archive_source.write_bytes(b"UNVERIFIED synthetic corruption")
    reopened = LegacyReportDialog(tmp_path, "self_portrait")
    assert reopened.history.count() == 0
    assert "cannot be verified" in reopened.saved_text.toPlainText()
    assert "UNVERIFIED" not in reopened.saved_text.toPlainText()
    assert all((tmp_path / "reports" / label).read_bytes() == raw
               for label, raw in originals.items())
    reopened.close()


def test_markdown_only_preview_does_not_generate_json_or_translation(application, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    raw = b"# Original English-only synthetic note\r\nNo quote or source supplied."
    (reports / "mate_criteria.md").write_bytes(raw)
    dialog = LegacyReportDialog(tmp_path, "mate_criteria")
    assert dialog.inspection.format == "markdown_only"
    saved = _save(dialog)
    assert not (reports / "mate_criteria.json").exists()
    assert not (reports / "mate_criteria_localization.json").exists()
    restarted = LegacyReportService(tmp_path)
    assert restarted.read_snapshot("mate_criteria", saved.id, "mate_criteria.md") == raw
    archived = restarted.read_archive("mate_criteria", saved.id)
    missing = next(file for file in archived.files if file.label == "mate_criteria.json")
    assert missing.present is False
    dialog.close()
