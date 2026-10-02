"""An empty, synthetic folder is sufficient to enter the chat product."""

import pytest
from anti_dating_scam_desktop.app_state import AppState
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens.profile_detection_screen import ProfileDetectionScreen
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("action", ["create", "open", "continue"])
def test_empty_folder_enters_home_without_import_or_profile(
    tmp_path, monkeypatch, language, action,
):
    application = QApplication.instance() or QApplication([])
    previous = current_language()
    set_language(language, persist=False)
    visits = []
    store = ProfileStore(tmp_path / "unused", config_path=tmp_path / "pointer.json")
    state = AppState()
    screen = ProfileDetectionScreen(
        state, store, lambda: visits.append("home"),
        lambda: visits.append("import"), lambda: visits.append("back"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    try:
        if action == "create":
            parent = tmp_path / "synthetic-parent"
            parent.mkdir()
            monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(parent))
            screen.create_button.click()
        else:
            vault = store.create_vault(tmp_path / "synthetic-parent")
            if action == "open":
                monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(vault))
                screen.open_vault_button.click()
            else:
                screen.on_enter()
                assert not screen.build_button.isHidden()
                screen.build_button.click()
        application.processEvents()
        assert visits == ["home"]
        assert state.vault_path == store.base_dir
        assert not store.detect_existing_profile()
        assert not list(store.base_dir.rglob("self_portrait*.json"))
    finally:
        screen.close()
        set_language(previous, persist=False)
