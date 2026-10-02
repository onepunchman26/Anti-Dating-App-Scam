"""Real-service Qt tests use only bounded synthetic flat profile files."""

import json
from copy import deepcopy
from dataclasses import asdict

import pytest
from anti_dating_scam_desktop.app_state import AppState
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_migration_dialog import ProfileMigrationDialog
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens.profile_detection_screen import ProfileDetectionScreen
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
)

from anti_dating_scam.engine.personal_profile_builder import PersonalProfileBuilder


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def english_ui(monkeypatch):
    previous = current_language()
    set_language("en", persist=False)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    yield
    set_language(previous, persist=False)


def _seed(vault, mode="both", *, invalid=False):
    vault.mkdir(parents=True)
    files = {}
    if mode in ("both", "md"):
        files["profile.mpm.md"] = (
            b"\xef\xbb\xbf# Synthetic profile\r\n<img src='https://example.invalid/a'>\r\n"
            + "偏好慢慢了解。\r\n".encode()
        )
    if mode in ("both", "json"):
        profile = PersonalProfileBuilder().build(manual_notes="Synthetic privacy preference.")
        if invalid:
            profile["unsupported_synthetic_field"] = "NEVER_ECHO_IN_ERROR"
        files["profile.json"] = b"\xef\xbb\xbf" + (
            json.dumps(profile, ensure_ascii=False, indent=3) + "\r\n "
        ).encode()
    for name, raw in files.items():
        (vault / name).write_bytes(raw)
    return files


def _screen(tmp_path):
    store = ProfileStore(tmp_path / "previous", config_path=tmp_path / "config.json")
    store.save_markdown_profile("Previous saved synthetic profile")
    store.remember_vault()
    state = AppState(
        vault_path=store.base_dir, profile_path=store.markdown_path,
        profile_json_path=store.json_path, current_profile_markdown="UNSAVED_SYNTHETIC_DRAFT",
        current_profile_json={"old": "synthetic"}, manual_notes="Synthetic draft notes",
        profile_exists=True,
    )
    visits = []
    screen = ProfileDetectionScreen(state, store, lambda: visits.append("home"),
                                    lambda: None, lambda: None)
    return screen, visits


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("mode", ["both", "md", "json"])
def test_explicit_literal_copy_preserves_bytes_and_requires_confirmation(
    application, tmp_path, language, mode,
):
    originals = _seed(tmp_path / "legacy", mode)
    set_language(language, persist=False)
    dialog = ProfileMigrationDialog(tmp_path / "legacy")
    assert dialog.preview.eligible
    assert not dialog.migrate_button.isEnabled()
    assert not (tmp_path / "legacy/profile").exists()
    for name, raw in originals.items():
        # Qt omits an initial BOM and normalizes line separators for display only.
        expected = raw.decode("utf-8-sig").replace("\r\n", "\n")
        assert dialog.file_readers[name].toPlainText() == expected
    assert all(label.textFormat() == Qt.TextFormat.PlainText
               for label in dialog.findChildren(QLabel))
    for reader in dialog.findChildren(QPlainTextEdit):
        assert reader.isReadOnly()
        block = reader.document().begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                assert not iterator.fragment().charFormat().isAnchor()
                assert not iterator.fragment().charFormat().isImageFormat()
                iterator += 1
            block = block.next()
    dialog.confirm.setChecked(True)
    dialog.migrate_button.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert set(dialog.migration_result.files) == set(originals)
    for name, raw in originals.items():
        assert (tmp_path / "legacy" / name).read_bytes() == raw
        assert (tmp_path / "legacy/profile" / name).read_bytes() == raw
    dialog.close()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_invalid_json_is_literal_review_only_with_safe_diagnostic(application, tmp_path, language):
    _seed(tmp_path / "legacy", invalid=True)
    set_language(language, persist=False)
    dialog = ProfileMigrationDialog(tmp_path / "legacy")
    assert not dialog.preview.eligible
    assert "NEVER_ECHO_IN_ERROR" in dialog.file_readers["profile.json"].toPlainText()
    assert "NEVER_ECHO_IN_ERROR" not in dialog.review_text.toPlainText()
    assert "NEVER_ECHO_IN_ERROR" not in dialog.status.text()
    assert not dialog.confirm.isEnabled()
    dialog.confirm.setChecked(True)
    dialog._migrate()
    assert not (tmp_path / "legacy/profile").exists()
    dialog.close()


@pytest.mark.parametrize("mutation", ["source", "new_companion", "destination"])
def test_stale_copy_refused_and_refresh_clears_confirmation(application, tmp_path, mutation):
    vault = tmp_path / "legacy"
    _seed(vault, "md")
    dialog = ProfileMigrationDialog(vault)
    dialog.confirm.setChecked(True)
    if mutation == "source":
        (vault / "profile.mpm.md").write_text("Changed synthetic source")
    elif mutation == "new_companion":
        (vault / "profile.json").write_text("{}")
    else:
        (vault / "profile").mkdir()
        (vault / "profile/keep.txt").write_text("Synthetic destination")
    dialog.migrate_button.click()
    assert dialog.migration_result is None and dialog.preview is None
    assert "stale" in dialog.status.text()
    assert not dialog.confirm.isChecked() and not dialog.migrate_button.isEnabled()
    assert not (vault / "profile/profile.mpm.md").exists()
    dialog.refresh_button.click()
    assert dialog.preview is not None
    assert not dialog.confirm.isChecked() and not dialog.migrate_button.isEnabled()
    assert dialog.preview.eligible == (mutation == "source")
    dialog.close()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_remembered_flat_has_review_action_without_automatic_writes(
    application, tmp_path, language,
):
    vault = tmp_path / "legacy"
    originals = _seed(vault)
    store = ProfileStore(vault, config_path=tmp_path / "config.json")
    state = AppState(current_profile_markdown="Unsaved synthetic")
    set_language(language, persist=False)
    screen = ProfileDetectionScreen(state, store, lambda: None, lambda: None, lambda: None)
    screen.on_enter()
    assert not screen.migration_button.isHidden()
    assert screen.continue_button.isHidden() and screen.build_button.isHidden()
    assert not store.config_path.exists() and not (vault / "profile").exists()
    assert state.current_profile_markdown == "Unsaved synthetic"
    assert all((vault / name).read_bytes() == raw for name, raw in originals.items())
    screen.close()


@pytest.mark.parametrize("failure", ["cancel", "stale", "invalid", "destination"])
def test_selected_flat_failure_preserves_current_config_and_drafts(
    application, tmp_path, monkeypatch, failure,
):
    screen, visits = _screen(tmp_path)
    vault = tmp_path / "legacy"
    _seed(vault, invalid=(failure == "invalid"))
    if failure == "destination":
        (vault / "profile").mkdir()
        (vault / "profile/unrelated.txt").write_text("Do not overwrite")
    before = deepcopy(asdict(screen.state))
    pointer = screen.profile_store.config_path.read_bytes()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(vault))

    def inspect_and_cancel(dialog):
        assert screen.profile_store.base_dir == tmp_path / "previous"
        assert screen.profile_store.config_path.read_bytes() == pointer
        if failure == "stale":
            dialog.confirm.setChecked(True)
            (vault / "profile.mpm.md").write_text("Changed synthetic")
            dialog.migrate_button.click()
            assert dialog.migration_result is None
        elif failure in ("invalid", "destination"):
            assert not dialog.preview.eligible
        dialog.reject()
        return dialog.result()

    monkeypatch.setattr(ProfileMigrationDialog, "exec", inspect_and_cancel)
    screen._open_existing_vault()
    assert not visits
    assert asdict(screen.state) == before
    assert screen.profile_store.base_dir == tmp_path / "previous"
    assert screen.profile_store.config_path.read_bytes() == pointer
    assert not (vault / "profile/profile.mpm.md").exists()
    screen.close()


@pytest.mark.parametrize("mode", ["both", "md", "json"])
def test_selected_flat_success_switches_only_after_copy_and_clears_missing_companion(
    application, tmp_path, monkeypatch, mode,
):
    screen, visits = _screen(tmp_path)
    vault = tmp_path / "legacy"
    originals = _seed(vault, mode)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(vault))

    def confirm(dialog):
        assert screen.profile_store.base_dir == tmp_path / "previous"
        dialog.confirm.setChecked(True)
        dialog.migrate_button.click()
        return dialog.result()

    monkeypatch.setattr(ProfileMigrationDialog, "exec", confirm)
    screen._open_existing_vault()
    assert visits == ["home"]
    assert screen.profile_store.base_dir == vault
    assert screen.state.vault_path == vault and screen.state.profile_exists
    assert (screen.state.current_profile_markdown is None) == (mode == "json")
    assert (screen.state.current_profile_json is None) == (mode == "md")
    assert ProfileStore(config_path=screen.profile_store.config_path).base_dir == vault
    assert all((vault / "profile" / name).read_bytes() == raw for name, raw in originals.items())
    screen.close()


def test_current_nested_wins_and_legacy_review_cannot_overwrite(application, tmp_path, monkeypatch):
    screen, visits = _screen(tmp_path)
    vault = tmp_path / "legacy"
    _seed(vault)
    (vault / "profile").mkdir()
    (vault / "profile/profile.mpm.md").write_text("CURRENT_SYNTHETIC_PROFILE")
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(vault))

    def must_not_migrate(*args):
        raise AssertionError("Current layout must load before legacy migration")

    monkeypatch.setattr(ProfileMigrationDialog, "exec", must_not_migrate)
    screen._open_existing_vault()
    assert visits == ["home"]
    assert screen.state.current_profile_markdown == "CURRENT_SYNTHETIC_PROFILE"
    screen.on_enter()
    assert not screen.continue_button.isHidden() and not screen.migration_button.isHidden()
    dialog = ProfileMigrationDialog(vault)
    assert not dialog.preview.eligible and not dialog.migrate_button.isEnabled()
    assert (vault / "profile/profile.mpm.md").read_text() == "CURRENT_SYNTHETIC_PROFILE"
    dialog.close()
    screen.close()


def test_failed_load_does_not_half_switch_or_clear_draft(application, tmp_path):
    screen, visits = _screen(tmp_path)
    vault = tmp_path / "bad-current"
    (vault / "profile").mkdir(parents=True)
    (vault / "profile/profile.mpm.md").write_text("New synthetic")
    (vault / "profile/profile.json").write_text("invalid synthetic JSON")
    before = deepcopy(asdict(screen.state))
    pointer = screen.profile_store.config_path.read_bytes()
    assert not screen._activate_vault(vault)
    assert screen.profile_store.base_dir == tmp_path / "previous"
    assert screen.profile_store.config_path.read_bytes() == pointer
    assert asdict(screen.state) == before and not visits
    screen.close()
