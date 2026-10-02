"""Synthetic actual-service Qt choices; no AI, external file launch or real vault."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.report_review_dialog import ReportReviewDialog
from anti_dating_scam_desktop.report_revision_dialog import ReportRevisionDialog
from anti_dating_scam_desktop.report_selection_dialog import ReportSelectionDialog
from anti_dating_scam_desktop.screens.criteria_interview_screen import CriteriaInterviewScreen
from anti_dating_scam_desktop.screens.criteria_viewer_screen import CriteriaViewerScreen
from anti_dating_scam_desktop.screens.self_portrait_viewer_screen import SelfPortraitViewerScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication
from test_report_revision_ui import _seed

from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionService


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def english_ui():
    previous = current_language()
    set_language("en", persist=False)
    yield
    set_language(previous, persist=False)


def _copy(vault, kind="self_portrait"):
    notes = _seed(vault, kind)
    store = ProfileStore(vault, config_path=vault / "synthetic-settings.json")
    path = store.self_portrait_path if kind == "self_portrait" else store.mate_criteria_path
    path.write_text("LEGACY ORIGINAL MARKDOWN", encoding="utf-8")
    store.self_portrait_detailed_path.write_text("ORIGINAL DETAIL FILE", encoding="utf-8")
    service = ReportRevisionService(vault)
    document = ReportReviewService(vault).inspect(kind)
    preview = service.preview_withdrawals(
        kind, [notes[0].id], expected_digest=document.report_digest,
    )
    return store, service.save_withdrawals(preview, confirmed=True)


def _choose(dialog, revision_id):
    for row in range(dialog.choices.count()):
        if dialog.choices.item(row).data(Qt.ItemDataRole.UserRole) == revision_id:
            dialog.choices.setCurrentRow(row)
            return
    raise AssertionError("Synthetic choice not offered")


def _select(vault, kind, revision_id):
    service = ActiveReportService(vault)
    preview = service.preview_selection(
        kind, revision_id, expected_selection_version=service.get_selection(kind).selection_version,
    )
    return service.select(preview, confirmed=True)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_preview_confirm_use_and_restore_never_overwrite_sources(
    application, tmp_path, kind, language,
):
    store, saved = _copy(tmp_path, kind)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    set_language(language, persist=False)
    dialog = ReportSelectionDialog(tmp_path, kind)
    assert dialog.choices.currentRow() == -1
    assert not dialog.use_button.isEnabled()
    assert dialog.service.resolve(kind) is None
    _choose(dialog, saved.id)
    assert not dialog.use_button.isEnabled()
    dialog.preview_button.click()
    assert dialog.preview is not None
    assert "English" in dialog.reader.toPlainText() and "中文版" in dialog.reader.toPlainText()
    dialog.confirm.setChecked(True)
    assert dialog.service.resolve(kind) is None
    dialog.use_button.click()
    assert dialog.result() == dialog.DialogCode.Accepted
    active = store.read_active_report(kind)
    assert active.revision_id == saved.id
    loader = store.load_self_portrait if kind == "self_portrait" else store.load_mate_criteria
    assert loader() == active.markdown
    if kind == "self_portrait":
        assert store.load_self_portrait_json() == active.canonical["report"]
    for path, data in before.items():
        assert path.read_bytes() == data
    assert store.self_portrait_path == tmp_path / "reports/self_portrait.md"
    restore = ReportSelectionDialog(tmp_path, kind)
    _choose(restore, None)
    restore.preview_button.click()
    restore.confirm.setChecked(True)
    restore.use_button.click()
    assert restore.result() == restore.DialogCode.Accepted
    assert store.read_active_report(kind).revision_id is None
    if kind == "self_portrait":
        assert store.self_portrait_path.read_text(encoding="utf-8") == "LEGACY ORIGINAL MARKDOWN"


def test_cancel_and_changed_choice_do_not_select(application, tmp_path):
    _, saved = _copy(tmp_path)
    dialog = ReportSelectionDialog(tmp_path, "self_portrait")
    _choose(dialog, saved.id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    _choose(dialog, None)
    assert dialog.preview is None and not dialog.reader.toPlainText()
    assert not dialog.confirm.isChecked() and not dialog.use_button.isEnabled()
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.cancel_button.click()
    assert dialog.service.resolve("self_portrait") is None
    assert not (tmp_path / "reports/active_selections").exists()


def test_stale_confirmation_requires_refresh_preserving_choice(application, tmp_path):
    _, saved = _copy(tmp_path)
    dialog = ReportSelectionDialog(tmp_path, "self_portrait")
    _choose(dialog, saved.id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    concurrent = _select(tmp_path, "self_portrait", None)
    dialog.use_button.click()
    assert dialog.service.get_selection("self_portrait") == concurrent
    assert dialog.choices.currentItem().data(Qt.ItemDataRole.UserRole) == saved.id
    assert not dialog.use_button.isEnabled() and not dialog.preview_button.isEnabled()
    assert "refresh" in dialog.status.text()
    dialog.refresh_button.click()
    assert dialog.choices.currentItem().data(Qt.ItemDataRole.UserRole) == saved.id
    assert dialog.preview is None and not dialog.confirm.isChecked()
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.use_button.click()
    assert dialog.service.resolve("self_portrait").revision_id == saved.id


@pytest.mark.parametrize("kind,screen_type", [
    ("self_portrait", SelfPortraitViewerScreen), ("mate_criteria", CriteriaViewerScreen),
])
def test_viewers_use_selected_snapshot_and_fail_closed_when_stale(
    application, tmp_path, monkeypatch, kind, screen_type,
):
    store, saved = _copy(tmp_path, kind)
    _select(tmp_path, kind, saved.id)
    screen = screen_type(None, store, lambda: None)
    screen.on_enter()
    active = store.read_active_report(kind)
    assert screen.viewer.toPlainText() == active.markdown
    assert "LEGACY ORIGINAL" not in screen.viewer.toPlainText()
    assert saved.id[:12] in screen.path_label.text()
    assert not screen.viewer.openExternalLinks() and not screen.viewer.openLinks()
    opened = []
    if kind == "self_portrait":
        module = "anti_dating_scam_desktop.screens.self_portrait_viewer_screen"
        monkeypatch.setattr(module + ".show_verified_report", lambda *args: opened.append(args[2]))
        monkeypatch.setattr(
            module + ".QDesktopServices.openUrl", lambda *args: pytest.fail("file open"),
        )
        screen.visual_button.click()
        screen.detailed_button.click()
        assert opened == [active.detailed_markdown or active.markdown] * 2
    source = tmp_path / "reports" / f"{kind}.json"
    source.write_bytes(source.read_bytes() + b"\n")
    if kind == "self_portrait":
        screen._open_visual()
        assert opened == [active.detailed_markdown or active.markdown] * 2
        assert not screen.viewer.toPlainText()
    screen.on_enter()
    assert not screen.viewer.toPlainText()
    assert "cannot be verified" in screen.path_label.text()
    assert screen.selection_button.isEnabled()
    if kind == "self_portrait":
        assert not screen.visual_button.isEnabled() and not screen.detailed_button.isEnabled()
    with pytest.raises(ActiveReportError):
        (store.load_self_portrait if kind == "self_portrait" else store.load_mate_criteria)()
    screen.close()


def test_default_visual_resolves_once_and_reads_only_original_bundle(
    application, tmp_path, monkeypatch,
):
    store, _ = _copy(tmp_path)
    screen = SelfPortraitViewerScreen(None, store, lambda: None)
    calls = []

    def resolve_once(kind):
        calls.append(kind)
        if len(calls) > 1:
            raise ActiveReportError("Synthetic concurrent selection change")
        return None

    monkeypatch.setattr(store, "read_active_report", resolve_once)
    monkeypatch.setattr(
        store, "load_self_portrait_json", lambda: pytest.fail("mixed active JSON loader"),
    )
    opened = []
    module = "anti_dating_scam_desktop.screens.self_portrait_viewer_screen"
    monkeypatch.setattr(module + ".QDesktopServices.openUrl", lambda url: opened.append(url))
    screen._open_current_report()
    assert calls == ["self_portrait"]
    assert len(opened) == 1
    assert store.self_portrait_html_path.is_file()
    screen.close()


def test_untrusted_selected_preview_and_viewer_are_inert_plain_text(application, tmp_path):
    unsafe = '<img src="https://synthetic.invalid/pixel"> [link](file:///synthetic)'
    _seed(tmp_path, first=unsafe)
    dialog = ReportSelectionDialog(tmp_path, "self_portrait")
    _choose(dialog, None)
    dialog.preview_button.click()
    assert "pixel" in dialog.reader.toPlainText()
    dialog.confirm.setChecked(True)
    dialog.use_button.click()
    store = ProfileStore(tmp_path, config_path=tmp_path / "synthetic-settings.json")
    screen = SelfPortraitViewerScreen(None, store, lambda: None)
    screen.on_enter()
    assert "pixel" in screen.viewer.toPlainText()
    for widget in (dialog.reader, screen.viewer):
        block = widget.document().begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                assert not fragment.charFormat().isAnchor()
                assert not fragment.charFormat().isImageFormat()
                iterator += 1
            block = block.next()
    screen.close()


def test_corrupt_copy_can_deliberately_restore_original(application, tmp_path):
    store, saved = _copy(tmp_path)
    _select(tmp_path, "self_portrait", saved.id)
    Path(saved.markdown_path).write_text("UNVERIFIED SYNTHETIC CONTENT", encoding="utf-8")
    with pytest.raises(ActiveReportError):
        store.read_active_report("self_portrait")
    dialog = ReportSelectionDialog(tmp_path, "self_portrait")
    assert dialog.choices.count() == 2  # Verified original plus explicit review-only recovery.
    _choose(dialog, None)
    dialog.preview_button.click()
    assert "UNVERIFIED SYNTHETIC" not in dialog.reader.toPlainText()
    dialog.confirm.setChecked(True)
    dialog.use_button.click()
    assert store.read_active_report("self_portrait").revision_id is None


def test_corrupt_journal_never_resets_or_falls_back(application, tmp_path):
    store, saved = _copy(tmp_path)
    _select(tmp_path, "self_portrait", saved.id)
    event = next((tmp_path / "reports/active_selections").rglob("selection.json"))
    event.write_text('{"damaged":"synthetic"}', encoding="utf-8")
    before = event.read_bytes()
    dialog = ReportSelectionDialog(tmp_path, "self_portrait")
    assert dialog.choices.count() == 0
    assert "needs repair" in dialog.status.text()
    assert not dialog.use_button.isEnabled()
    assert event.read_bytes() == before
    with pytest.raises(ActiveReportError):
        store.load_self_portrait()
    dialog.close()


def test_viewer_and_review_dialog_entries_preserve_original_correction_scope(application, tmp_path):
    store, saved = _copy(tmp_path)
    _select(tmp_path, "self_portrait", saved.id)
    screen = SelfPortraitViewerScreen(None, store, lambda: None)
    review = ReportReviewDialog(tmp_path, "self_portrait")
    revision = ReportRevisionDialog(tmp_path, "self_portrait")
    assert len(review.document.claims) == 2
    assert revision.corrections.count() == 2
    assert "original" in review.windowTitle()
    review.correction.setPlainText("Unsaved original correction")
    for parent in (screen, review, revision):
        seen = []

        def cancel_modal(seen=seen):
            modal = application.activeModalWidget()
            try:
                if isinstance(modal, ReportSelectionDialog):
                    seen.append(modal.selection.revision_id)
            finally:
                if modal is not None:
                    modal.reject()

        QTimer.singleShot(20, cancel_modal)
        parent.selection_button.click()
        assert seen == [saved.id]
    assert review.correction.toPlainText() == "Unsaved original correction"
    for widget in (screen, review, revision):
        widget.close()


def test_legacy_default_and_vault_switch_keep_original_writer_paths(application, tmp_path):
    first = tmp_path / "first"
    store, saved = _copy(first)
    assert store.read_active_report("self_portrait") is None
    assert store.load_self_portrait() == "LEGACY ORIGINAL MARKDOWN"
    _select(first, "self_portrait", saved.id)
    second = tmp_path / "second"
    other, _ = _copy(second)
    store.set_base_dir(second)
    assert store.read_active_report("self_portrait") is None
    assert store.load_self_portrait() == "LEGACY ORIGINAL MARKDOWN"
    assert store.self_portrait_path == other.self_portrait_path


def test_manual_handoff_stale_selection_preserves_notes_request_and_clipboard(
    application, tmp_path,
):
    store, saved = _copy(tmp_path)
    _select(tmp_path, "self_portrait", saved.id)
    store.criteria_interview_request_path.write_text("PREVIOUS SYNTHETIC REQUEST", encoding="utf-8")
    source = store.self_portrait_json_path
    source.write_bytes(source.read_bytes() + b"\n")
    state = SimpleNamespace(import_sources=[])
    screen = CriteriaInterviewScreen(state, store, lambda: None, lambda: None, lambda: None)
    screen.notes.setPlainText("Unsaved synthetic notes")
    application.clipboard().setText("PREVIOUS SYNTHETIC CLIPBOARD")
    screen._prepare()
    screen._copy_prompt()
    assert store.criteria_interview_request_path.read_text(encoding="utf-8") == \
        "PREVIOUS SYNTHETIC REQUEST"
    assert application.clipboard().text() == "PREVIOUS SYNTHETIC CLIPBOARD"
    assert screen.notes.toPlainText() == "Unsaved synthetic notes"
    assert state.import_sources == []
    assert "cannot be verified" in screen.banner.label.text()
    screen.close()
