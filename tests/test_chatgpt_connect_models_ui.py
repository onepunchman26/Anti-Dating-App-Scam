"""Real Qt connection feedback and catalog selection, using synthetic services."""

import json
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.navigation import Navigator
from anti_dating_scam_desktop.screens import chatgpt_connect_screen
from PySide6.QtCore import QAbstractAnimation, QPoint, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QStackedWidget

from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionStatus, ChatGPTModelChoice


class Deferred:
    def __init__(self):
        self.pending = []

    def run(self, _owner, call, done, error):
        self.pending.append((call, done, error))

    def finish(self):
        call, done, error = self.pending.pop(0)
        try:
            result = call()
        except Exception:
            error("Synthetic safe failure")
        else:
            done(result)


class FakeConnection:
    def __init__(self, *, connected=True, sharing=True, catalog_error=False):
        self.current = ChatGPTConnectionStatus(connected=connected, sharing=sharing)
        self.catalog_error = catalog_error
        self.catalog_calls, self.connect_calls, self.created, self.inference_calls = 0, 0, [], 0
        self.models = (
            ChatGPTModelChoice(slug="synthetic-large", display_name="Synthetic Large"),
            ChatGPTModelChoice(slug="synthetic-luna", display_name="Synthetic Luna"),
        )

    def status(self):
        return self.current

    def list_models(self):
        self.catalog_calls += 1
        if self.catalog_error:
            raise RuntimeError("Synthetic catalog failure")
        return self.models

    def connect(self, *, cancel_event):
        self.connect_calls += 1
        self.current = ChatGPTConnectionStatus(connected=True, sharing=True)
        return self.current

    def create_backend(self, slug, *, included_plan_confirmed):
        self.created.append((slug, included_plan_confirmed))
        assert included_plan_confirmed is True
        return SimpleNamespace(provider_id="chatgpt_plan", model=slug)


@pytest.mark.parametrize("remembered", ["synthetic-large", "synthetic-removed"])
def test_reopened_picker_restores_choice_or_requires_reselection(
    application, tmp_path, monkeypatch, remembered
):
    from anti_dating_scam.ai.chatgpt_preferences import ModelPreferences

    connection = FakeConnection()
    connection.current = connection.current.model_copy(update={"client_id": "oaiapp_synthetic"})
    preferences = ModelPreferences(tmp_path)
    preferences.save("oaiapp_synthetic", remembered)
    stack, _navigator, page, deferred, activated, _actions, _state = screen(
        monkeypatch, connection=connection
    )
    page.preferences = ModelPreferences(tmp_path)
    try:
        deferred.finish()
        if remembered == "synthetic-large":
            assert page.model_picker.currentData() == remembered
        else:
            assert page.model_picker.currentIndex() == -1
            page.plan_consent.setChecked(True)
            page._use()
            assert activated == [] and connection.created == []
    finally:
        stack.close()


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def restore_language():
    original = current_language()
    yield
    set_language(original, persist=False)


def settle(application):
    for _ in range(4):
        application.processEvents()


def screen(monkeypatch, *, language="en", connection=None, size=(940, 700)):
    set_language(language, persist=False)
    deferred, activated, actions = Deferred(), [], []
    monkeypatch.setattr(chatgpt_connect_screen, "run_async", deferred.run)
    monkeypatch.setattr(chatgpt_connect_screen.ai_backend, "get_active", lambda: None)
    monkeypatch.setattr(chatgpt_connect_screen.ai_backend, "set_active", activated.append)
    state = SimpleNamespace(provider_name="", model_name="")
    page = chatgpt_connect_screen.ChatGPTConnectScreen(
        state,
        None,
        lambda: actions.append("done"),
        lambda: actions.append("back"),
        connection=connection or FakeConnection(),
    )
    stack = QStackedWidget()
    navigator = Navigator(stack)
    navigator.add("connect", page)
    stack.resize(*size)
    stack.show()
    navigator.go("connect")
    return stack, navigator, page, deferred, activated, actions, state


@pytest.mark.parametrize("language", ["en", "zh"])
def test_signedin_badge_animates_and_loads_catalog_before_credit_confirmation(
    application,
    monkeypatch,
    language,
):
    stack, _, page, deferred, activated, _, _ = screen(monkeypatch, language=language)
    try:
        settle(application)
        assert page.success.isVisible()
        assert page.success.animation.state() == QAbstractAnimation.State.Running
        assert (
            "account connected" if language == "en" else "账号连接成功"
        ) in page.success.label.text()
        assert not page.plan_consent.isChecked() and not page.use_button.isEnabled()
        assert len(deferred.pending) == 1 and page.connection.catalog_calls == 0
        deferred.finish()
        assert page.connection.catalog_calls == 1
        assert page.model_picker.isEnabled() and page.model_picker.currentData() == "synthetic-luna"
        assert page.model_picker.count() == 3
        assert not page.use_button.isEnabled() and activated == []
        assert page.connection.created == [] and page.connection.inference_calls == 0
        assert (
            "不保证" in page.model_hint.text()
            if language == "zh"
            else "does not guarantee" in page.model_hint.text()
        )
    finally:
        stack.close()


@pytest.mark.parametrize("selected", ["synthetic-luna", "synthetic-large"])
def test_model_picker_and_credit_confirmation_activate_exact_selected_slug(
    application,
    monkeypatch,
    selected,
):
    stack, _, page, deferred, activated, actions, state = screen(monkeypatch)
    try:
        deferred.finish()
        page.model_picker.setCurrentIndex(page.model_picker.findData(selected))
        page._use()
        assert deferred.pending == [] and page.connection.created == [] and activated == []
        page.plan_consent.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(page.plan_consent, Qt.Key.Key_Space)
        settle(application)
        assert page.plan_consent.isChecked() and page.use_button.isEnabled()
        page.use_button.click()
        assert activated == []
        deferred.finish()
        assert page.connection.created == [(selected, True)]
        assert activated[0].model == selected and actions == ["done"]
        assert state.model_name == selected and state.provider_name == "ChatGPT plan"
        assert "ready to chat" in page.success.label.text()
        assert page.connection.inference_calls == 0
    finally:
        stack.close()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_identity_success_without_plan_permission_is_distinct_and_never_loads_catalog(
    application,
    monkeypatch,
    language,
):
    connection = FakeConnection(sharing=False)
    stack, _, page, deferred, activated, _, _ = screen(
        monkeypatch,
        language=language,
        connection=connection,
    )
    try:
        settle(application)
        assert page.success.isVisible() and deferred.pending == []
        assert (
            "permission is missing" if language == "en" else "尚未获得套餐使用权限"
        ) in page.banner.label.text()
        page.plan_consent.setChecked(True)
        assert not page.use_button.isEnabled() and not page.model_picker.isEnabled()
        assert connection.catalog_calls == 0 and connection.created == [] and activated == []
    finally:
        stack.close()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_catalog_failure_preserves_identity_success_and_never_claims_ready(
    application,
    monkeypatch,
    language,
):
    connection = FakeConnection(catalog_error=True)
    stack, _, page, deferred, activated, _, _ = screen(
        monkeypatch,
        language=language,
        connection=connection,
    )
    try:
        deferred.finish()
        settle(application)
        assert page.success.isVisible()
        assert (
            "account connected" if language == "en" else "账号连接成功"
        ) in page.success.label.text()
        assert ("could not load" if language == "en" else "未加载成功") in page.banner.label.text()
        page.plan_consent.setChecked(True)
        assert not page.use_button.isEnabled() and not page.model_picker.isEnabled()
        assert connection.current.connected and activated == [] and connection.created == []
    finally:
        stack.close()


def test_back_discards_late_catalog_and_never_activates(application, monkeypatch):
    stack, _, page, deferred, activated, actions, _ = screen(monkeypatch)
    try:
        page.plan_consent.setChecked(True)
        next(button for button in page.findChildren(QPushButton) if button.text() == "Back").click()
        deferred.finish()
        assert actions == ["back"] and activated == [] and page._models == ()
        assert not page.use_button.isEnabled() and page.connection.created == []
    finally:
        stack.close()


def test_reenter_after_back_can_load_a_new_catalog(application, monkeypatch):
    stack, navigator, page, deferred, activated, actions, _ = screen(monkeypatch)
    try:
        next(button for button in page.findChildren(QPushButton) if button.text() == "Back").click()
        deferred.finish()
        navigator.go("connect")
        deferred.finish()
        assert page.model_picker.isEnabled() and page._models == page.connection.models
        assert actions == ["back"] and activated == []
    finally:
        stack.close()


def test_reentry_discards_previous_catalog_without_losing_the_new_load(application, monkeypatch):
    stack, navigator, page, deferred, activated, _, _ = screen(monkeypatch)
    try:
        old_call, old_done, _ = deferred.pending.pop(0)
        old_result = old_call()
        next(button for button in page.findChildren(QPushButton) if button.text() == "Back").click()
        navigator.go("connect")
        assert len(deferred.pending) == 1
        old_done(old_result)
        assert page._models == () and not page.model_picker.isEnabled()
        deferred.finish()
        assert page._models == page.connection.models and page.model_picker.isEnabled()
        assert activated == []
    finally:
        stack.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_model_choice_credit_and_back_are_keyboard_accessible_in_real_viewport(
    application,
    monkeypatch,
    language,
    size,
):
    stack, navigator, page, deferred, _, _, _ = screen(monkeypatch, language=language, size=size)
    try:
        deferred.finish()
        settle(application)
        viewport = navigator._viewports["connect"]
        assert stack.size() == QSize(*size) and not viewport.horizontalScrollBar().maximum()
        assert page.model_picker.accessibleName()
        assert page.plan_consent.accessibleName() == page.plan_consent.text()
        back = next(
            button
            for button in page.findChildren(QPushButton)
            if button.text() == ("Back" if language == "en" else "返回")
        )
        for control in (page.model_picker, page.plan_consent, back):
            control.setFocus(Qt.FocusReason.TabFocusReason)
            settle(application)
            assert control.hasFocus()
            center = control.mapTo(
                viewport.viewport(), QPoint(control.width() // 2, control.height() // 2)
            )
            assert viewport.viewport().rect().contains(center)
    finally:
        stack.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_primary_window_path_connects_then_enters_chat_and_private_exchange(
    application,
    monkeypatch,
    tmp_path,
    language,
    size,
):
    from anti_dating_scam_desktop import main_window
    from anti_dating_scam_desktop.profile_store import ProfileStore
    from anti_dating_scam_desktop.screens import reflection_chat_screen

    from anti_dating_scam.ai.chat_backends import OllamaChatBackend

    set_language(language, persist=False)
    store = ProfileStore(tmp_path / "synthetic-empty-vault", config_path=tmp_path / "pointer.json")
    store.create_default_directories()
    monkeypatch.setattr(main_window, "ProfileStore", lambda: store)
    connection = FakeConnection(connected=False, sharing=False)
    monkeypatch.setattr(chatgpt_connect_screen, "ChatGPTConnectionService", lambda: connection)
    monkeypatch.setattr(chatgpt_connect_screen.ai_backend, "_active", None)
    deferred, requests = Deferred(), []
    monkeypatch.setattr(chatgpt_connect_screen, "run_async", deferred.run)
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)

    def transport(_url, payload, _headers, _timeout):
        requests.append(payload)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "question": {
                            "en": "What helps you feel listened to?",
                            "zh": "什么能让你感到被倾听？",
                        }
                    }
                )
            }
        }

    def create(slug, *, included_plan_confirmed):
        assert included_plan_confirmed is True
        connection.created.append((slug, included_plan_confirmed))
        backend = OllamaChatBackend(model=slug, transport=transport)
        backend.provider_id = "chatgpt_plan"
        return backend

    monkeypatch.setattr(connection, "create_backend", create)
    window = main_window.MainWindow()
    window.resize(*size)
    window.show()
    try:
        assert window.navigator.current_name == "welcome" and requests == []
        next(
            button
            for button in window.navigator._screens["welcome"].findChildren(QPushButton)
            if button.text() == ("Get Started" if language == "en" else "开始使用")
        ).click()
        policy = window.navigator._screens["policy"]
        assert window.navigator.current_name == "policy" and not policy.next_button.isEnabled()
        policy.checkbox.setChecked(True)
        policy.next_button.click()
        assert window.navigator.current_name == "profile_detection"
        window.navigator._screens["profile_detection"].build_button.click()
        assert window.navigator.current_name == "home" and not store.detect_existing_profile()
        window.navigator._screens["home"].connect_button.click()
        connection_page = window.navigator._screens["ai_connect"]
        assert window.navigator.current_name == "ai_connect"
        connection_page.connect_button.click()
        deferred.finish()
        deferred.finish()
        assert connection_page.success.isVisible()
        assert connection_page.model_picker.currentData() == "synthetic-luna"
        assert requests == [] and connection.created == []
        assert not connection_page.plan_consent.isChecked()
        assert not connection_page.use_button.isEnabled()
        connection_page.plan_consent.setChecked(True)
        connection_page.use_button.click()
        deferred.finish()
        assert connection.created == [("synthetic-luna", True)] and requests == []
        assert window.navigator.current_name == "reflection_chat"
        conversation = window.navigator._screens["reflection_chat"]
        conversation.start_button.click()
        deferred.finish()
        assert len(requests) == 1 and conversation.service.running
        draft = "Synthetic unsent reflection draft."
        conversation.input_box.setPlainText(draft)
        session_id = conversation.service.session_id
        conversation.end_button.click()
        assert not conversation.service.running and conversation.service.portrait is None
        assert len(requests) == 1 and deferred.pending == []
        label = "Share or compare reflections" if language == "en" else "分享或比对相处画像"
        next(
            button for button in conversation.findChildren(QPushButton) if button.text() == label
        ).click()
        assert window.navigator.current_name == "relationship_exchange"
        page = window.navigator._screens["relationship_exchange"]
        settle(application)
        assert page.isVisible() and window.size() == QSize(*size)
        assert (
            not window.navigator._viewports["relationship_exchange"].horizontalScrollBar().maximum()
        )
        back = next(
            button
            for button in page.findChildren(QPushButton)
            if button.text() == ("Back" if language == "en" else "返回")
        )
        back.setFocus(Qt.FocusReason.TabFocusReason)
        settle(application)
        back.click()
        assert window.navigator.current_name == "reflection_chat"
        assert conversation.service.session_id == session_id and not conversation.service.running
        assert conversation.input_box.toPlainText() == draft
        assert len(requests) == 1 and deferred.pending == []
        window.navigator.go("home", remember=False)
        window.navigator._screens["home"].findChild(
            QPushButton, "home_relationship_exchange"
        ).click()
        assert window.navigator.current_name == "relationship_exchange"
        assert len(requests) == 1
    finally:
        window.close()
