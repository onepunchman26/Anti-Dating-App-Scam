"""Synthetic, hermetic desktop paths for the conversation-first entry."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop import main_window
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.profile_store import ProfileStore
from anti_dating_scam_desktop.screens import chatgpt_connect_screen, reflection_chat_screen
from PySide6.QtCore import QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionStatus, ChatGPTModelChoice
from anti_dating_scam.services.reflection_chat import read_saved_reflection

_USER_TEXT = "Synthetic: I prefer to pause when a conversation feels tense."
_QUESTION = {
    "question": {
        "en": "What helps you feel understood during a difficult conversation?",
        "zh": "在困难的对话中，什么能让你感到被理解？",
    }
}


def _pair(en, zh):
    return {"en": en, "zh": zh}


def _portrait():
    return {
        "report": {
            "schema_version": "0.2",
            "report_type": "self_portrait",
            "data_coverage": {
                "sources_read": ["S001"],
                "covered": [_pair("One typed statement was considered.", "只考虑了一段输入。")],
                "not_covered": [_pair("Other situations remain unknown.", "其他情境仍然未知。")],
            },
            "claims": [
                {
                    "topic": "communication",
                    "type": "speculation",
                    "confidence": "low",
                    "claim": _pair(
                        "A pause may help in tense talks.", "在紧张的对话中，暂停可能有帮助。"
                    ),
                    "evidence": [{"source": "S001", "quote": _USER_TEXT}],
                }
            ],
            "consistency_findings": [],
            "open_questions": [_pair("What makes a pause respectful?", "怎样的暂停才显得尊重？")],
            "caveats": [_pair("A tentative self-report reflection.", "这只是暂定的自述反思。")],
        }
    }


class _Deferred:
    def __init__(self):
        self.pending = []

    def run(self, _owner, call, done, error):
        self.pending.append((call, done, error))

    def finish(self):
        call, done, error = self.pending.pop(0)
        try:
            done(call())
        except Exception as exc:
            error(str(exc))


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


def _window(tmp_path, monkeypatch, language="en", size=(940, 700)):
    set_language(language, persist=False)
    store = ProfileStore(tmp_path / "synthetic-vault", config_path=tmp_path / "pointer.json")
    monkeypatch.setattr(main_window, "ProfileStore", lambda: store)
    window = main_window.MainWindow()
    window.resize(*size)
    window.show()
    return window, store


def _local_backend(*responses):
    calls = []
    remaining = iter(responses)

    def transport(_url, payload, _headers, _timeout):
        calls.append(payload)
        return {"message": {"content": json.dumps(next(remaining), ensure_ascii=False)}}

    return OllamaChatBackend(model="synthetic-reflection-ui", transport=transport), calls


def _button(page, label):
    return next(button for button in page.findChildren(QPushButton) if button.text() == label)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_start_send_end_and_separate_save_are_explicit_and_leave_existing_reports(
    application,
    tmp_path,
    monkeypatch,
    language,
):
    backend, calls = _local_backend(_QUESTION, _QUESTION, _portrait())
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    deferred = _Deferred()
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    window, store = _window(tmp_path, monkeypatch, language=language)
    try:
        store.create_default_directories()
        original = store.self_portrait_json_path
        original.write_bytes(b"synthetic existing report bytes")
        window.navigator.go("home")
        home = window.navigator._screens["home"]
        assert [button.text() for button in home.findChildren(QPushButton)] == (
            [
                "Connect ChatGPT",
                "AI Chat",
                "My reflections",
                "Share or compare reflections",
                "Saved videos & interests",
                "Introductions & invitations",
                "More tools",
            ]
            if language == "en"
            else [
                "连接 ChatGPT",
                "AI 聊天",
                "我的相处画像",
                "分享或比对相处画像",
                "收藏视频与兴趣",
                "介绍与邀请",
                "更多工具",
            ]
        )
        home.chat_button.click()
        chat = window.navigator._screens["reflection_chat"]
        assert window.navigator.current_name == "reflection_chat"
        assert chat.service.session_id is None
        assert not any(
            token in button.text().lower()
            for button in chat.findChildren(QPushButton)
            for token in ("duration", "market", "manual", "ollama")
        )

        chat.start_button.click()
        assert len(deferred.pending) == 1 and len(calls) == 0
        deferred.finish()
        assert len(calls) == 1
        assert chat.service.running
        assert len(chat.service.transcript) == 1
        assert _QUESTION["question"][language] in chat.chat_view.toPlainText()

        chat.input_box.setPlainText(_USER_TEXT)
        chat.send_button.click()
        deferred.finish()
        assert len(calls) == 2
        assert [item.role for item in chat.service.transcript] == [
            "assistant",
            "user",
            "assistant",
        ]
        assert chat.service.transcript[1].content == _USER_TEXT
        assert chat.service.portrait is None

        chat.end_button.click()
        assert not chat.service.running
        assert not chat._busy and chat.start_button.isEnabled()
        assert chat.portrait_button.isEnabled()
        assert not deferred.pending
        assert chat.service.portrait is None  # End never synthesizes a report.
        chat.portrait_button.click()
        assert len(deferred.pending) == 1 and len(calls) == 2
        deferred.finish()
        assert len(calls) == 3
        assert chat.service.portrait is not None
        assert chat.preview.isVisible() and chat.save_button.isVisible()
        selected_claim = _portrait()["report"]["claims"][0]["claim"][language]
        other_claim = _portrait()["report"]["claims"][0]["claim"][
            "zh" if language == "en" else "en"
        ]
        assert selected_claim in chat.preview.toPlainText()
        assert other_claim not in chat.preview.toPlainText()
        assert _USER_TEXT in chat.preview.toPlainText()
        assert not chat.preview.openExternalLinks() and not chat.preview.openLinks()
        assert original.read_bytes() == b"synthetic existing report bytes"

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
        )
        chat.save_button.click()
        saved_dir = window.reflection_state.saved[store.base_dir]
        assert saved_dir.parent.name == "reflection_history"
        assert (
            read_saved_reflection(store.base_dir, chat.service.session_id)["report"]["claims"][0][
                "evidence"
            ][0]["quote"]
            == _USER_TEXT
        )
        assert original.read_bytes() == b"synthetic existing report bytes"
    finally:
        window.close()


def test_end_while_busy_stops_immediately_and_discards_late_reply(
    application,
    tmp_path,
    monkeypatch,
):
    backend, calls = _local_backend(_QUESTION, _QUESTION)
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    deferred = _Deferred()
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    window, _store = _window(tmp_path, monkeypatch)
    try:
        window.navigator.go("reflection_chat")
        chat = window.navigator._screens["reflection_chat"]
        chat.start_button.click()
        deferred.finish()
        chat.input_box.setPlainText(_USER_TEXT)
        chat.send_button.click()
        assert len(deferred.pending) == 1
        assert len(chat.service.transcript) == 2  # Original typed answer is retained.
        chat.end_button.click()
        assert not chat.service.running
        assert chat.service.portrait is None
        assert len(calls) == 1
        deferred.finish()
        assert len(calls) == 1  # Late call is rejected before transport.
        assert [item.role for item in chat.service.transcript] == ["assistant", "user"]
        assert chat.service.portrait is None
        assert not deferred.pending
    finally:
        window.close()


def test_end_discards_a_reply_already_in_transport(application, tmp_path, monkeypatch):
    entered = Event()
    release = Event()
    calls = []

    def transport(_url, payload, _headers, _timeout):
        calls.append(payload)
        if len(calls) == 2:
            entered.set()
            assert release.wait(5)
        return {"message": {"content": json.dumps(_QUESTION, ensure_ascii=False)}}

    backend = OllamaChatBackend(model="synthetic-reflection-ui", transport=transport)
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    deferred = _Deferred()
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    window, _store = _window(tmp_path, monkeypatch)
    try:
        window.navigator.go("reflection_chat")
        chat = window.navigator._screens["reflection_chat"]
        chat.start_button.click()
        deferred.finish()
        chat.input_box.setPlainText(_USER_TEXT)
        chat.send_button.click()
        call, done, error = deferred.pending.pop(0)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(call)
            assert entered.wait(5)
            chat.end_button.click()
            assert not chat.service.running
            assert chat.service.portrait is None
            release.set()
            try:
                done(future.result(timeout=5))
            except Exception as exc:
                error(str(exc))
        assert len(calls) == 2  # The call had already started; its result is discarded.
        assert [item.role for item in chat.service.transcript] == ["assistant", "user"]
        assert chat.service.portrait is None
    finally:
        release.set()
        window.close()


def test_old_canceled_callback_cannot_clear_new_session_busy(application, tmp_path, monkeypatch):
    backend, _calls = _local_backend(_QUESTION, _QUESTION)
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    deferred = _Deferred()
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    window, _store = _window(tmp_path, monkeypatch)
    try:
        window.navigator.go("reflection_chat")
        chat = window.navigator._screens["reflection_chat"]
        chat._start()
        deferred.finish()
        chat.input_box.setPlainText(_USER_TEXT)
        chat._send()
        chat._end()
        assert not chat._busy
        chat._start()
        assert chat._busy and len(deferred.pending) == 2
        deferred.finish()  # Old canceled service request and its error callback.
        assert chat._busy and chat.service.running
        deferred.finish()
        assert not chat._busy and len(chat.service.transcript) == 1
    finally:
        window.close()


def test_remote_disclosure_cancel_sends_nothing_and_keeps_typed_turn(
    application,
    tmp_path,
    monkeypatch,
):
    class Remote:
        recipient = "https://synthetic.invalid/chat"
        name = "Synthetic remote"

        def __init__(self):
            self.calls = []

        def chat(self, request):
            self.calls.append(request)
            raise AssertionError("Canceled disclosure must not reach transport")

    backend = Remote()
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    deferred = _Deferred()
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    window, _store = _window(tmp_path, monkeypatch)
    try:
        window.navigator.go("reflection_chat")
        chat = window.navigator._screens["reflection_chat"]
        first = chat.service.begin()
        chat.service.accept_turn(first.request_id, json.dumps(_QUESTION, ensure_ascii=False))
        chat.on_enter()
        monkeypatch.setattr(
            reflection_chat_screen, "review_reflection_request", lambda *_args: None
        )
        chat.input_box.setPlainText(_USER_TEXT)
        chat.send_button.click()
        assert backend.calls == [] and deferred.pending == []
        assert [item.role for item in chat.service.transcript] == ["assistant", "user"]
        assert chat.service.transcript[-1].content == _USER_TEXT
        assert chat.service.running and chat.service.portrait is None
    finally:
        window.close()


def test_chatgpt_login_needs_extra_credit_confirmation_and_model_discovery_is_not_chat(
    application,
    tmp_path,
    monkeypatch,
):
    class FakeConnection:
        def __init__(self):
            self.connects = 0
            self.models = 0
            self.backends = 0
            self.chat_calls = 0

        def status(self):
            return ChatGPTConnectionStatus()

        def connect(self, *, cancel_event):
            self.connects += 1
            return ChatGPTConnectionStatus(connected=True, sharing=True)

        def list_models(self):
            self.models += 1
            return [ChatGPTModelChoice(slug="synthetic-model", display_name="Synthetic")]

        def create_backend(self, slug, *, included_plan_confirmed):
            self.backends += 1
            assert slug == "synthetic-model" and included_plan_confirmed is True
            return SimpleNamespace(name="Synthetic ChatGPT", provider_id="chatgpt_plan")

    connection = FakeConnection()
    deferred = _Deferred()
    monkeypatch.setattr(chatgpt_connect_screen, "run_async", deferred.run)
    active = []
    monkeypatch.setattr(chatgpt_connect_screen.ai_backend, "set_active", active.append)
    page = chatgpt_connect_screen.ChatGPTConnectScreen(
        None,
        None,
        lambda: active.append("done"),
        lambda: active.append("back"),
        connection=connection,
    )
    page.show()
    try:
        page.on_enter()
        assert not page.use_button.isEnabled() and not page.plan_consent.isChecked()
        page.connect_button.click()
        assert connection.connects == 0 and active == []
        deferred.finish()
        assert connection.connects == 1 and active == []
        assert not page.use_button.isEnabled()
        assert connection.models == 0 and connection.chat_calls == 0
        deferred.finish()  # Account catalog loads even while credit consent is unchecked.
        assert connection.models == 1 and connection.chat_calls == 0
        assert not page.use_button.isEnabled() and not page.plan_consent.isChecked()
        page.plan_consent.setChecked(True)
        assert page.use_button.isEnabled()
        page.use_button.click()
        deferred.finish()
        assert connection.models == 1 and connection.backends == 1
        assert connection.chat_calls == 0
        assert active[-1] == "done" and active[0].provider_id == "chatgpt_plan"
    finally:
        page.close()


def test_cancel_login_does_not_activate_ai(application, monkeypatch):
    class FakeConnection:
        def status(self):
            return ChatGPTConnectionStatus()

        def connect(self, *, cancel_event):
            assert cancel_event.is_set()
            return ChatGPTConnectionStatus()

    deferred = _Deferred()
    monkeypatch.setattr(chatgpt_connect_screen, "run_async", deferred.run)
    active = []
    monkeypatch.setattr(chatgpt_connect_screen.ai_backend, "set_active", active.append)
    page = chatgpt_connect_screen.ChatGPTConnectScreen(
        None,
        None,
        lambda: active.append("done"),
        lambda: active.append("back"),
        connection=FakeConnection(),
    )
    page.show()
    try:
        page.on_enter()
        page.connect_button.click()
        _button(page, "Back").click()
        deferred.finish()
        assert active == ["back"]
        assert not page.use_button.isEnabled()
    finally:
        page.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_real_window_chat_navigation_language_change_keeps_transcript_and_draft(
    application,
    tmp_path,
    monkeypatch,
    language,
    size,
):
    backend, calls = _local_backend(_QUESTION)
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    deferred = _Deferred()
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    window, _store = _window(tmp_path, monkeypatch, language, size)
    try:
        window.navigator.go("home")
        _settle(application)
        home = window.navigator._screens["home"]
        home.chat_button.click()
        _settle(application)
        assert window.navigator.current_name == "reflection_chat"
        chat = window.navigator._screens["reflection_chat"]
        chat.start_button.click()
        deferred.finish()
        draft = "Synthetic unsent answer: I need a thoughtful pause."
        chat.input_box.setPlainText(draft)
        _settle(application)
        assert window.size() == QSize(*size) and len(calls) == 1
        old_session = chat.service.session_id
        window.findChild(QPushButton, "LanguageButton").click()
        _settle(application)
        rebuilt = window.navigator._screens["reflection_chat"]
        assert rebuilt is not chat
        assert window.navigator.current_name == "reflection_chat"
        assert window.size() == QSize(*size)
        assert rebuilt.service.session_id == old_session
        assert rebuilt.input_box.toPlainText() == draft
        assert _QUESTION["question"][current_language()] in rebuilt.chat_view.toPlainText()
        assert [item.role for item in rebuilt.service.transcript] == ["assistant"]
        back = _button(rebuilt, "返回" if language == "en" else "Back")
        back.setFocus(Qt.FocusReason.TabFocusReason)
        _settle(application)
        QTest.mouseClick(back, Qt.MouseButton.LeftButton)
        _settle(application)
        assert window.navigator.current_name == "home"
    finally:
        window.close()
