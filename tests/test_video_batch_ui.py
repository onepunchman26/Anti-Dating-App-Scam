"""Connected EN/ZH desktop journeys, selected scopes and late-worker isolation."""

from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.screens import video_batch_screen as ui
from PySide6.QtWidgets import QApplication, QDialog
from test_video_batches import SyntheticBackend, rows

from anti_dating_scam.batch_context.importers import preview_rows


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def language_restore():
    original = current_language()
    yield
    set_language(original, persist=False)


def immediate(_owner, call, done, error):
    try:
        done(call())
    except Exception as exc:
        error(str(exc))


@pytest.mark.parametrize("language", ["en", "zh"])
def test_import_filter_process_review_correct_undo(application, tmp_path, monkeypatch, language):
    set_language(language, persist=False)
    reviews = []
    monkeypatch.setattr(
        ui, "review_dialog", lambda _p, title, text: reviews.append((title, text)) or True
    )
    monkeypatch.setattr(ui, "run_async", immediate)
    monkeypatch.setattr(ui.ai_backend, "get_active", lambda: SyntheticBackend())
    state = SimpleNamespace(vault_path=tmp_path)
    screen = ui.VideoBatchScreen(
        state, SimpleNamespace(base_dir=tmp_path), ui.VideoBatchState(), lambda: None
    )
    screen.on_enter()
    screen._preview(preview_rows(rows()))
    screen.source.setCurrentIndex(screen.source.findData("youtube"))
    screen._filter()
    assert screen.table.rowCount() == 1
    screen.source.setCurrentIndex(0)
    screen.start_date.setText("2026-09-01")
    screen.unknown_dates.setChecked(False)
    screen._filter()
    assert screen.table.rowCount() == 0
    screen.start_date.clear()
    screen.unknown_dates.setChecked(True)
    screen._filter()
    screen._create()
    assert screen.batch and len(screen.batch.items) == 4
    screen._analyze()
    assert screen.batch.counts()["full"] == 1 and screen.batch.counts()["partial"] == 2
    assert not screen.service.memory.read().entries
    assert len(reviews) == 2  # One local import and one AI scope for the entire collection.
    screen.groups.item(0).setSelected(True)
    screen._details()
    assert "Framing light" in screen.details.toPlainText()
    screen.service.memory.change(0, action="enable", confirmed=True)
    screen._review("confirm")
    assert len(screen.service.memory.read().entries) == 1
    screen.groups.item(0).setSelected(True)
    screen.edit.setText("Saved for work only.")
    screen._review("revise")
    assert not screen.service.memory.read().entries and screen.batch.findings[0].status == "draft"
    screen._undo()
    assert screen.batch is None and not screen.service.list()
    screen.close()


def test_declined_scope_never_calls_provider(application, tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "review_dialog", lambda *_args: True)
    screen = ui.VideoBatchScreen(
        SimpleNamespace(vault_path=tmp_path),
        SimpleNamespace(base_dir=tmp_path),
        ui.VideoBatchState(),
        lambda: None,
    )
    screen.on_enter()
    screen._preview(preview_rows(rows()))
    screen._create()
    backend = SyntheticBackend()
    monkeypatch.setattr(ui.ai_backend, "get_active", lambda: backend)
    monkeypatch.setattr(ui, "review_dialog", lambda *_args: False)
    screen._analyze()
    assert not backend.calls and not screen.holder.grants
    screen.close()


def test_vault_switch_clears_preview_filters_and_late_callback(application, tmp_path, monkeypatch):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    state = SimpleNamespace(vault_path=first)
    holder = ui.VideoBatchState()
    screen = ui.VideoBatchScreen(state, SimpleNamespace(base_dir=first), holder, lambda: None)
    screen.on_enter()
    screen._preview(preview_rows(rows()))
    screen.pasted.setPlainText("PRIVATE_SYNTHETIC_MARKER")
    screen.edit.setText("PRIVATE_SYNTHETIC_MARKER")
    pending = []
    monkeypatch.setattr(
        ui, "run_async", lambda _owner, call, done, error: pending.append((call, done))
    )
    screen._work(lambda _: preview_rows(rows()), screen._preview)
    state.vault_path = second
    screen.on_enter()
    pending[0][1](pending[0][0]())
    assert not holder.preview and not screen.pasted.toPlainText()
    assert screen.source.count() == 0 and screen.collection.count() == 0
    assert screen.table.rowCount() == 0 and not screen.edit.text()
    screen.close()


def test_bilingual_help_is_real_dialog_and_safe_text(application, tmp_path, monkeypatch):
    rendered = []
    monkeypatch.setattr(
        QDialog, "exec", lambda self: rendered.append(self) or QDialog.DialogCode.Rejected
    )
    screen = ui.VideoBatchScreen(
        SimpleNamespace(vault_path=tmp_path),
        SimpleNamespace(base_dir=tmp_path),
        ui.VideoBatchState(),
        lambda: None,
    )
    screen._help()
    assert rendered
    screen.close()
