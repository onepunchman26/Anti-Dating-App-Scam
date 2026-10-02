"""Synthetic Qt checks for complete disclosures and usable narrow export controls."""

from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.screens.beacon_exchange_screen import BeaconExchangeScreen
from anti_dating_scam_desktop.style import APP_STYLESHEET
from anti_dating_scam_desktop.widgets.assisted_browser_export_page import AssistedBrowserExportPage
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QAccessible
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea

from anti_dating_scam.browser_export.export_models import ExportMode


@pytest.fixture()
def application():
    app = QApplication.instance() or QApplication([])
    previous_style = app.styleSheet()
    previous_language = current_language()
    app.setStyleSheet(APP_STYLESHEET)
    yield app
    app.setStyleSheet(previous_style)
    set_language(previous_language, persist=False)
    app.processEvents()


def test_status_retains_long_path_and_markup_as_complete_wrapped_plain_text(application):
    text = "Synthetic vault: C:/" + "long_unbroken_folder_name_" * 30 + "/<b>literal</b>"
    banner = StatusBanner(text)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(banner)
    area.resize(600, 260)
    area.show()
    application.processEvents()
    assert banner.label.text() == text
    assert banner.label.textFormat() == Qt.TextFormat.PlainText
    assert area.horizontalScrollBar().maximum() == 0
    assert banner.label.height() >= banner.label.heightForWidth(banner.label.width())
    assert banner.label.heightForWidth(500) > banner.label.heightForWidth(900)
    area.close()
    area.deleteLater()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_wrapped_checkbox_keeps_native_keyboard_mouse_and_accessible_consent(application, language):
    text = {
        "en": "I agree only after reading this entire synthetic disclosure, "
        "including every caveat. Nothing is shared without this explicit consent.",
        "zh": "我只会在读完这条合成声明及其中的所有限制之后同意。未经我明确同意，不分享任何内容。",
    }[language]
    checkbox = WrappedCheckBox(text)
    checkbox.resize(290, checkbox.heightForWidth(290))
    checkbox.show()
    application.processEvents()
    assert checkbox.text() == checkbox.label.text() == text
    assert checkbox.label.textFormat() == Qt.TextFormat.PlainText
    assert not checkbox.isChecked()
    assert checkbox.minimumSizeHint().width() < 290
    assert checkbox.label.height() >= checkbox.label.heightForWidth(checkbox.label.width())
    accessible = QAccessible.queryAccessibleInterface(checkbox)
    assert accessible.role() == QAccessible.Role.CheckBox
    assert accessible.text(QAccessible.Text.Name) == text
    assert not accessible.state().checked
    toggles = []
    checkbox.toggled.connect(toggles.append)
    checkbox.setFocus()
    assert checkbox.hasFocus()
    QTest.keyClick(checkbox, Qt.Key.Key_Space)
    assert checkbox.isChecked() and accessible.state().checked
    QTest.mouseClick(checkbox, Qt.MouseButton.LeftButton, pos=checkbox.label.geometry().center())
    assert not checkbox.isChecked()
    checkbox.setChecked(True)
    assert toggles == [True, False, True]
    checkbox.setEnabled(False)
    QTest.keyClick(checkbox, Qt.Key.Key_Space)
    QTest.mouseClick(checkbox, Qt.MouseButton.LeftButton, pos=checkbox.label.geometry().center())
    assert checkbox.isChecked() and toggles == [True, False, True]
    checkbox.close()
    checkbox.deleteLater()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("width,height", [(940, 700), (1100, 760)])
@pytest.mark.parametrize("page_name", ["beacon", "export"])
def test_full_disclosures_and_export_actions_fit_normal_viewports(
    application, tmp_path, language, width, height, page_name,
):
    set_language(language, persist=False)
    if page_name == "beacon":
        page = BeaconExchangeScreen(
            None, SimpleNamespace(json_path=tmp_path / "synthetic_card.json"), lambda: None,
        )
    else:
        page = AssistedBrowserExportPage({})
    viewport = QScrollArea()
    viewport.setWidgetResizable(True)
    viewport.setWidget(page)
    viewport.resize(width, height)
    viewport.show()
    application.processEvents()
    assert viewport.size().width() == width
    assert viewport.horizontalScrollBar().maximum() == 0
    assert page.minimumSizeHint().width() <= viewport.viewport().width()
    checkboxes = page.findChildren(WrappedCheckBox)
    assert len(checkboxes) == (1 if page_name == "beacon" else 5)
    for checkbox in checkboxes:
        assert not checkbox.isChecked()
        assert checkbox.label.height() >= checkbox.label.heightForWidth(checkbox.label.width())
        assert checkbox.label.geometry().right() < checkbox.width()
    if page_name == "export":
        buttons = page.findChildren(QPushButton)
        assert len(buttons) == 8
        for button in buttons:
            assert button.width() >= button.sizeHint().width(), button.text()
        # Every item remains required: neither wrapping nor keyboard use weakens the gate.
        assert not page._config(ExportMode.VISIBLE_PAGE_EXPORT).consent_confirmed
        for checkbox in checkboxes[:-1]:
            checkbox.setChecked(True)
            assert not page._consent_confirmed()
        last = checkboxes[-1]
        last.setFocus()
        QTest.keyClick(last, Qt.Key.Key_Space)
        assert page._config(ExportMode.VISIBLE_PAGE_EXPORT).consent_confirmed
        checkboxes[0].setChecked(False)
        assert not page._consent_confirmed()
    viewport.close()
    viewport.deleteLater()
