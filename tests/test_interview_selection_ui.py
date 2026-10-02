"""Report changes must not mix conversations, discard drafts or save stale replies."""

from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.screens import interview_chat_screen as module
from PySide6.QtWidgets import QApplication, QMessageBox

from anti_dating_scam.ai.privacy import ChatRequest


@pytest.fixture
def screen(tmp_path, monkeypatch):
    application = QApplication.instance() or QApplication([])
    previous_language = current_language()
    set_language("en", persist=False)
    state = {"version": "A", "calls": [], "jobs": [], "saved": []}

    def version(_store):
        if state["version"] == "corrupt":
            raise ValueError("private unsafe parser detail")
        return state["version"]

    def chat(request):
        state["calls"].append(request)
        if "during_call" in state:
            state["version"] = state["during_call"]
        return "A synthetic reply."

    backend = SimpleNamespace(name="Synthetic local backend", chat=chat)
    monkeypatch.setattr(module.ai_backend, "get_active", lambda: backend)
    monkeypatch.setattr(module.ai_backend, "interview_reference_version", version)
    monkeypatch.setattr(module.ai_backend, "interview_reference_snapshot", lambda store: (
        "Synthetic assistant reference", version(store)
    ))
    monkeypatch.setattr(module.ai_backend, "build_interview_context", lambda _: "Synthetic notes")
    monkeypatch.setattr(
        module.ai_backend, "build_interview_system", lambda _: "Trusted instruction"
    )
    monkeypatch.setattr(module, "review_request", lambda _parent, _backend, request: request)
    monkeypatch.setattr(module, "run_async", lambda _owner, call, ok, err: state["jobs"].append(
        (call, ok, err)
    ))
    monkeypatch.setattr(module.ai_backend, "prepare_criteria_request", lambda *_: ChatRequest(
        messages=[{"role": "user", "content": "Synthetic interview"}], system="Trusted instruction"
    ))
    monkeypatch.setattr(module.ai_backend, "run_criteria_synthesis", lambda *args, **kwargs: (
        state["saved"].append(kwargs) or tmp_path / "synthetic-report.md"
    ))
    widget = module.InterviewChatScreen(
        None, SimpleNamespace(base_dir=tmp_path),
        lambda: state.setdefault("viewed", True), lambda: None,
    )
    widget.messages = [
        {"role": "user", "content": "Original synthetic question"},
        {"role": "assistant", "content": "Original synthetic answer"},
        {"role": "user", "content": "Additional synthetic answer"},
        {"role": "assistant", "content": "Additional synthetic question"},
    ]
    widget.system_prompt = "Trusted instruction"
    widget._reference_version = "A"
    widget.input_box.setPlainText("  Unsent synthetic draft  ")
    widget.on_enter()
    yield widget, state
    widget.close()
    application.processEvents()
    set_language(previous_language, persist=False)


@pytest.mark.parametrize("changed", ["B", "corrupt"])
@pytest.mark.parametrize("action", ["_send", "_finish"])
def test_changed_report_blocks_before_draft_or_history_mutation(screen, changed, action):
    widget, state = screen
    before = list(widget.messages)
    state["version"] = changed
    getattr(widget, action)()
    assert widget.messages == before
    assert widget.input_box.toPlainText() == "  Unsent synthetic draft  "
    assert not state["jobs"] and not state["calls"] and not state["saved"]
    assert not widget.send_button.isEnabled() and not widget.finish_button.isEnabled()
    assert "private unsafe" not in widget.banner.label.text()


def test_cancelled_disclosure_preserves_draft_and_history(screen, monkeypatch):
    widget, state = screen
    before = list(widget.messages)
    monkeypatch.setattr(module, "review_request", lambda *_: None)
    widget._send()
    assert not state["jobs"]
    assert widget.messages == before
    assert widget.input_box.toPlainText() == "  Unsent synthetic draft  "


def test_selection_change_during_disclosure_sends_nothing(screen, monkeypatch):
    widget, state = screen

    def change(_parent, _backend, request):
        state["version"] = "B"
        return request

    monkeypatch.setattr(module, "review_request", change)
    widget._send()
    assert not state["jobs"] and not state["calls"]
    assert len(widget.messages) == 4
    assert widget.input_box.toPlainText().strip() == "Unsent synthetic draft"


def test_selection_change_before_worker_dispatch_does_not_call_backend(screen):
    widget, state = screen
    widget._send()
    call, _ok, err = state["jobs"].pop()
    state["version"] = "B"
    with pytest.raises(ValueError) as caught:
        call()
    err(str(caught.value))
    assert not state["calls"]
    assert len(widget.messages) == 4 and not widget._busy
    assert widget.input_box.toPlainText().strip() == "Unsent synthetic draft"


def test_selection_change_before_callback_discards_reply_and_keeps_draft(screen):
    widget, state = screen
    widget._send()
    call, ok, _err = state["jobs"].pop()
    reply = call()
    state["version"] = "B"
    ok(reply)
    assert len(state["calls"]) == 1
    assert len(widget.messages) == 4
    assert widget.input_box.toPlainText().strip() == "Unsent synthetic draft"
    assert not widget._busy and not widget.send_button.isEnabled()


def test_selection_change_during_backend_call_rejects_its_reply(screen):
    widget, state = screen
    state["during_call"] = "B"
    widget._send()
    call, _ok, err = state["jobs"].pop()
    with pytest.raises(ValueError) as caught:
        call()
    err(str(caught.value))
    assert len(state["calls"]) == 1 and len(widget.messages) == 4
    assert widget.input_box.toPlainText().strip() == "Unsent synthetic draft"
    assert widget._stale_session and not widget._busy


def test_success_commits_one_turn_without_deleting_a_newer_draft(screen):
    widget, state = screen
    widget._send()
    assert len(widget.messages) == 4
    call, ok, _err = state["jobs"].pop()
    widget.input_box.setPlainText("A newer unsent draft")
    ok(call())
    assert len(widget.messages) == 6
    assert widget.messages[-2]["content"] == "Unsent synthetic draft"
    assert widget.input_box.toPlainText() == "A newer unsent draft"


def test_restart_requires_confirmation_and_preserves_old_conversation(screen, monkeypatch):
    widget, state = screen
    before = list(widget.messages)
    state["version"] = "B"
    widget.on_enter()
    monkeypatch.setattr(QMessageBox, "question", lambda *_: QMessageBox.StandardButton.No)
    widget._start()
    assert widget.messages == before and not widget.archived_interviews
    monkeypatch.setattr(QMessageBox, "question", lambda *_: QMessageBox.StandardButton.Yes)
    widget._start()
    assert widget.archived_interviews == [before]
    call, ok, _err = state["jobs"].pop()
    ok(call())
    assert widget._reference_version == "B" and not widget._stale_session
    assert widget.history_button.isEnabled()
    assert widget.input_box.toPlainText().strip() == "Unsent synthetic draft"
    sent = "\n".join(message.content for message in state["calls"][0].messages)
    assert "Original synthetic question" not in sent
    assert "Additional synthetic answer" not in sent


def test_finish_passes_reference_version_to_save_guard(screen):
    widget, state = screen
    widget._finish()
    call, ok, _err = state["jobs"].pop()
    ok(call())
    assert state["saved"][0]["expected_reference_version"] == "A"
    assert state["viewed"]


def test_chat_text_cannot_load_images_or_links(screen):
    widget, _state = screen
    payload = '<img src="file:///synthetic-secret"> [link](https://synthetic.invalid)'
    widget.messages = [{"role": "assistant", "content": payload}]
    widget._render()
    assert payload in widget.chat_view.toPlainText()
    block = widget.chat_view.document().begin()
    while block.isValid():
        cursor = block.begin()
        while not cursor.atEnd():
            fragment = cursor.fragment()
            assert not fragment.charFormat().isImageFormat()
            assert not fragment.charFormat().isAnchor()
            cursor += 1
        block = block.next()
