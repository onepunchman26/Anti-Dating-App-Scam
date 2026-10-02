"""Keep small desktop windows usable without discarding page state."""

from threading import Event

import pytest
from anti_dating_scam_desktop.navigation import Navigator
from anti_dating_scam_desktop.workers import has_pending_workers, run_async
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def _settle(application):
    # LayoutRequest and resize notifications may trigger one another.
    for _ in range(4):
        application.processEvents()


class _DraftScreen(QWidget):
    def __init__(self, *, height=1200, width=0):
        super().__init__()
        self.entries = 0
        layout = QVBoxLayout(self)
        self.editor = QLineEdit()
        layout.addWidget(self.editor)
        spacer = QLabel("Synthetic page content")
        spacer.setMinimumSize(width, height)
        layout.addWidget(spacer)
        self.bottom = QPushButton("Continue")
        layout.addWidget(self.bottom)

    def on_enter(self):
        self.entries += 1


def test_hidden_large_pages_do_not_set_window_minimum(application):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    small = _DraftScreen(height=30)
    large = _DraftScreen(height=1500, width=1700)
    navigator.add("small", small)
    navigator.add("large", large)
    stack.resize(500, 350)
    navigator.go("small")
    stack.show()
    _settle(application)
    assert stack.size() == QSize(500, 350)
    navigator.go("large")
    _settle(application)
    assert stack.size() == QSize(500, 350)
    viewport = stack.currentWidget()
    assert isinstance(viewport, QScrollArea)
    assert viewport.widget() is large
    assert viewport.verticalScrollBar().maximum() > 0
    assert viewport.horizontalScrollBar().maximum() > 0
    stack.close()


def test_back_keeps_draft_scroll_position_and_original_screen(application):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    first = _DraftScreen()
    second = _DraftScreen(height=40)
    navigator.add("first", first)
    navigator.add("second", second)
    stack.resize(500, 350)
    stack.show()
    navigator.go("first")
    _settle(application)
    first.editor.setText("Unsaved synthetic draft")
    first_viewport = stack.currentWidget()
    first_viewport.verticalScrollBar().setValue(150)
    navigator.bind("second")()
    navigator.back()
    _settle(application)
    assert navigator.current_name == "first"
    assert navigator._screens["first"] is first
    assert stack.currentWidget() is first_viewport
    assert first.editor.text() == "Unsaved synthetic draft"
    assert first_viewport.verticalScrollBar().value() == 150
    assert first.entries == 2
    assert second.entries == 1
    assert navigator._history == []
    navigator.back()
    assert first.entries == 2
    stack.close()


def test_keyboard_focus_scrolls_bottom_control_into_view(application):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    screen = _DraftScreen()
    navigator.add("form", screen)
    navigator.go("form")
    stack.resize(500, 350)
    stack.show()
    stack.activateWindow()
    _settle(application)
    screen.editor.setFocus()
    QTest.keyClick(screen.editor, Qt.Key.Key_Tab)
    _settle(application)
    viewport = stack.currentWidget()
    assert application.focusWidget() is screen.bottom
    assert viewport.verticalScrollBar().value() > 0
    bottom_rect = QRect(screen.bottom.mapTo(viewport.viewport(), QPoint()), screen.bottom.size())
    assert viewport.viewport().rect().contains(bottom_rect)
    stack.close()


@pytest.mark.parametrize("reason", [Qt.FocusReason.TabFocusReason, Qt.FocusReason.OtherFocusReason])
def test_programmatic_focus_reveals_bottom_control_after_layout(application, reason):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    screen = _DraftScreen()
    navigator.add("form", screen)
    navigator.go("form")
    stack.resize(500, 350)
    stack.show()
    stack.activateWindow()
    _settle(application)
    screen.bottom.setFocus(reason)
    _settle(application)
    viewport = stack.currentWidget()
    assert application.focusWidget() is screen.bottom
    assert viewport.verticalScrollBar().value() > 0
    bottom_rect = QRect(screen.bottom.mapTo(viewport.viewport(), QPoint()), screen.bottom.size())
    assert viewport.viewport().rect().contains(bottom_rect)
    stack.close()


def test_queued_focus_reveal_does_not_scroll_a_hidden_page(application):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    first = _DraftScreen()
    navigator.add("first", first)
    navigator.add("second", _DraftScreen(height=40))
    navigator.go("first")
    stack.resize(500, 350)
    stack.show()
    stack.activateWindow()
    _settle(application)
    first_viewport = stack.currentWidget()
    first_viewport.verticalScrollBar().setValue(150)
    first.bottom.setFocus(Qt.FocusReason.TabFocusReason)
    navigator.go("second")
    _settle(application)
    assert first_viewport.verticalScrollBar().value() == 150
    assert navigator.current_name == "second"
    stack.close()


def test_navigation_keeps_inflight_worker_owner_alive(application):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    owner = _DraftScreen()
    navigator.add("first", owner)
    navigator.add("second", _DraftScreen(height=40))
    navigator.go("first")
    release = Event()
    results = []
    errors = []
    worker = run_async(owner, lambda: release.wait(3), results.append, errors.append)
    try:
        navigator.go("second")
        assert isValid(owner)
        assert has_pending_workers(stack)
        release.set()
        for _ in range(100):
            application.processEvents()
            if not has_pending_workers(stack):
                break
            QTest.qWait(10)
        assert not has_pending_workers(stack)
        assert results == [True]
        assert errors == []
        navigator.back()
        assert navigator._screens["first"] is owner
    finally:
        release.set()
        if isValid(worker):
            worker.wait(5000)
        stack.close()


def test_wrapped_content_reflows_and_scrolls_after_live_changes(application):
    stack = QStackedWidget()
    navigator = Navigator(stack)
    screen = QWidget()
    layout = QVBoxLayout(screen)
    text = QLabel("Short synthetic notice")
    text.setWordWrap(True)
    layout.addWidget(text)
    bottom = QPushButton("Continue")
    layout.addWidget(bottom)
    navigator.add("form", screen)
    navigator.go("form")
    stack.resize(500, 350)
    stack.show()
    _settle(application)
    viewport = stack.currentWidget()
    assert viewport.verticalScrollBar().maximum() == 0

    text.setText("A synthetic consent notice that wraps without losing its words. " * 80)
    _settle(application)
    assert stack.size() == QSize(500, 350)
    assert viewport.horizontalScrollBar().maximum() == 0
    assert viewport.verticalScrollBar().maximum() > 0
    assert text.height() >= text.heightForWidth(text.width())
    previous_height = screen.height()
    stack.resize(700, 350)
    _settle(application)
    assert stack.size() == QSize(700, 350)
    assert screen.height() < previous_height
    assert text.height() >= text.heightForWidth(text.width())

    text.setText("Short again")
    _settle(application)
    assert viewport.verticalScrollBar().maximum() == 0
    stack.close()
