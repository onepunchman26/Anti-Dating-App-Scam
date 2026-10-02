"""Real window navigation at bounded sizes, isolated from vaults and providers."""

import pytest
from anti_dating_scam_desktop import main_window
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from PySide6.QtCore import QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def restore_language():
    original = current_language()
    yield
    set_language(original, persist=False)


def _settle(application):
    for _ in range(4):
        application.processEvents()


def _window(tmp_path, monkeypatch, language, size):
    set_language(language, persist=False)
    store = ProfileStore(tmp_path / "synthetic-vault", config_path=tmp_path / "pointer.json")
    store.save_markdown_profile("# Synthetic reflection\nI take time before making plans.\n")
    monkeypatch.setattr(main_window, "ProfileStore", lambda: store)
    window = main_window.MainWindow()
    window.resize(*size)
    window.show()
    return window


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_every_page_keeps_requested_window_size_and_reveals_focused_controls(
    application, tmp_path, monkeypatch, language, size,
):
    window = _window(tmp_path, monkeypatch, language, size)
    try:
        _settle(application)
        for name, page in window.navigator._screens.items():
            window.navigator.go(name, remember=False)
            _settle(application)
            assert window.size() == QSize(*size), (name, window.size())
            assert page.isVisible()
            area = page.parentWidget()
            while area is not None and not isinstance(area, QScrollArea):
                area = area.parentWidget()
            assert area is not None, name
            if name in {"welcome", "home", "beacon_exchange", "assisted_browser_export"}:
                assert area.horizontalScrollBar().maximum() == 0, name
            buttons = [button for button in page.findChildren(QPushButton)
                       if button.isVisible() and button.isEnabled()]
            if buttons:
                button = max(buttons, key=lambda b: b.mapTo(page, b.rect().center()).y())
                button.setFocus(Qt.FocusReason.TabFocusReason)
                _settle(application)
                assert button.hasFocus(), name
                assert area.viewport().rect().contains(
                    button.mapTo(area.viewport(), button.rect().center()),
                ), name
                assert window.size() == QSize(*size), name
    finally:
        window.close()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_return_navigation_preserves_draft_and_language_rebuild_keeps_size(
    application, tmp_path, monkeypatch, language,
):
    window = _window(tmp_path, monkeypatch, language, (940, 700))
    try:
        window.navigator.go("beacon_exchange")
        beacon = window.navigator._screens["beacon_exchange"]
        beacon.pseudonym.setText("synthetic-draft")
        beacon.their_beacon.setPlainText("UNSENT_SYNTHETIC_TEXT")
        window.navigator.go("home")
        window.navigator.back()
        _settle(application)
        assert window.navigator.current_name == "beacon_exchange"
        assert window.navigator._screens["beacon_exchange"] is beacon
        assert beacon.pseudonym.text() == "synthetic-draft"
        assert beacon.their_beacon.toPlainText() == "UNSENT_SYNTHETIC_TEXT"
        assert not beacon.disclosure_consent.isChecked()
        assert window.size() == QSize(940, 700)
        window._toggle_language()
        _settle(application)
        assert window.navigator.current_name == "beacon_exchange"
        assert window.size() == QSize(940, 700)
        # Language rebuild already reconstructs pages; it must not infer consent.
        assert not window.navigator._screens["beacon_exchange"].disclosure_consent.isChecked()
    finally:
        window.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize(
    ("previous", "destination"),
    [
        ("home", "self_portrait"),
        ("import_data", "self_portrait"),
        ("self_portrait", "self_portrait_viewer"),
        ("home", "self_portrait_viewer"),
    ],
)
def test_portrait_back_button_survives_language_rebuild(
    application, tmp_path, monkeypatch, language, previous, destination,
):
    window = _window(tmp_path, monkeypatch, language, (940, 700))
    try:
        window.navigator.go(previous)
        window.navigator.go(destination)
        _settle(application)
        language_button = window.findChild(QPushButton, "LanguageButton")
        language_button.click()
        _settle(application)
        assert window.navigator.current_name == destination

        page = window.navigator._screens[destination]
        back_label = "返回" if language == "en" else "Back"
        back = next(button for button in page.findChildren(QPushButton)
                    if button.text() == back_label)
        back.setFocus(Qt.FocusReason.TabFocusReason)
        _settle(application)
        QTest.mouseClick(back, Qt.MouseButton.LeftButton)
        _settle(application)
        assert window.navigator.current_name == previous
    finally:
        window.close()
