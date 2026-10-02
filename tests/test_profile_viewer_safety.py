"""Prevent companion inspection from replacing a user's Markdown draft."""

import json

import pytest
from anti_dating_scam_desktop.app_state import AppState
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens.profile_viewer_screen import ProfileViewerScreen
from PySide6.QtWidgets import QApplication, QMessageBox


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(params=["en", "zh"])
def language(request):
    original = current_language()
    set_language(request.param, persist=False)
    yield request.param
    set_language(original, persist=False)


def _screen(tmp_path, *, markdown="# Synthetic original\n", profile=None):
    store = ProfileStore(tmp_path / "vault", config_path=tmp_path / "config.json")
    if markdown is not None:
        store.save_markdown_profile(markdown)
    if profile is not None:
        store.save_json_profile(profile)
    state = AppState()
    state.current_profile_markdown = markdown or ""
    state.current_profile_json = profile
    screen = ProfileViewerScreen(state, store, lambda: None, lambda: None)
    screen.on_enter()
    return screen, state, store


def test_json_inspection_cannot_overwrite_markdown_draft(
    application, language, tmp_path, monkeypatch,
):
    screen, state, store = _screen(tmp_path, profile={"owner_label": "synthetic"})
    original_md = store.markdown_path.read_bytes()
    original_json = store.json_path.read_bytes()
    draft = "# Unsaved reflection\n<img src='https://invalid.example/x'>\n"
    screen.editor.setPlainText(draft)
    screen._show_json()
    assert screen.editor.toPlainText() == draft
    assert screen.json_view.isReadOnly()
    assert json.loads(screen.json_view.toPlainText()) == {"owner_label": "synthetic"}
    assert not screen.save_button.isEnabled()
    screen._save_markdown()
    assert store.markdown_path.read_bytes() == original_md
    assert store.json_path.read_bytes() == original_json
    screen.tabs.setCurrentIndex(0)
    monkeypatch.setattr(QMessageBox, "information", lambda *_: None)
    screen.save_button.click()
    assert store.load_markdown_profile() == draft
    assert state.current_profile_markdown == draft
    assert store.json_path.read_bytes() == original_json
    screen.close()


def test_json_only_view_cannot_save_placeholder(application, language, tmp_path):
    screen, _, store = _screen(tmp_path, markdown=None, profile={"owner_label": "synthetic"})
    assert screen.editor.toPlainText() == ""
    assert screen.editor.placeholderText()
    assert not screen.save_button.isEnabled()
    screen._save_markdown()
    assert not store.markdown_path.exists()
    screen._show_json()
    assert not screen.save_button.isEnabled()
    screen.close()


@pytest.mark.parametrize("unreadable", [False, True])
def test_missing_or_invalid_companion_preserves_editor(
    application, language, tmp_path, unreadable,
):
    screen, _, store = _screen(tmp_path)
    if unreadable:
        store.json_path.write_text('{"SYNTHETIC_SECRET_MARKER":', encoding="utf-8")
    screen.editor.setPlainText("Draft remains readable")
    screen._show_json()
    assert screen.editor.toPlainText() == "Draft remains readable"
    assert "SYNTHETIC_SECRET_MARKER" not in screen.json_view.toPlainText()
    assert screen.json_view.toPlainText()
    screen.close()


def test_failed_save_preserves_draft_and_state(application, language, tmp_path, monkeypatch):
    screen, state, store = _screen(tmp_path)
    before = store.markdown_path.read_bytes()
    screen.editor.setPlainText("Keep this draft")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[-1]))

    def fail(_):
        raise OSError("SYNTHETIC_PRIVATE_PATH")

    monkeypatch.setattr(store, "save_markdown_profile", fail)
    screen._save_markdown()
    assert screen.editor.toPlainText() == "Keep this draft"
    assert state.current_profile_markdown == "# Synthetic original\n"
    assert store.markdown_path.read_bytes() == before
    assert warnings and "SYNTHETIC_PRIVATE_PATH" not in warnings[0]
    screen.close()


@pytest.mark.parametrize("new_profile", [None, {"owner_label": "synthetic second vault"}])
def test_home_and_viewer_do_not_restore_previous_vault_json(
    application, language, tmp_path, monkeypatch, new_profile,
):
    from anti_dating_scam_desktop import main_window

    store = ProfileStore(tmp_path / "new-vault", config_path=tmp_path / "config.json")
    store.save_markdown_profile("# New synthetic vault")
    monkeypatch.setattr(main_window, "ProfileStore", lambda: store)
    window = main_window.MainWindow()
    window.legacy_state["profile"] = {"owner_label": "OLD_SYNTHETIC_VAULT"}
    window.navigator.go("profile_detection")
    window.app_state.current_profile_json = new_profile
    window.app_state.current_profile_markdown = "# New synthetic vault"
    window._go_home()
    assert window.app_state.current_profile_json == new_profile
    window._go_profile_viewer()
    assert window.app_state.current_profile_json == new_profile
    viewer = window.navigator._screens["profile_viewer"]
    viewer._show_json()
    assert "OLD_SYNTHETIC_VAULT" not in viewer.json_view.toPlainText()
    window.close()


def test_legacy_screen_updates_still_reach_app_state(application, tmp_path, monkeypatch):
    from anti_dating_scam_desktop import main_window

    store = ProfileStore(tmp_path / "vault", config_path=tmp_path / "config.json")
    monkeypatch.setattr(main_window, "ProfileStore", lambda: store)
    window = main_window.MainWindow()
    window._go_settings()
    window.legacy_state["provider_name"] = "Synthetic test provider"
    window._go_home()
    assert window.app_state.provider_name == "Synthetic test provider"
    window.close()
