"""Synthetic provenance and real stalled-socket cancellation, without HTTP."""

import socket
import threading
import time
from types import SimpleNamespace

import pytest
from test_chatgpt_plan_integration import MODEL, QUESTION, FakeConnection, _completed, _review

from anti_dating_scam.ai.chatgpt_auth import OfficialChatGPTHttpTransport
from anti_dating_scam.ai.chatgpt_backend import ChatGPTPlanBackend
from anti_dating_scam.ai.chatgpt_preferences import ModelPreferences
from anti_dating_scam.ai.privacy import BackendError
from anti_dating_scam.services.reflection_chat import ReflectionChatService


@pytest.mark.parametrize("reported", [MODEL, "synthetic-server-alias", None])
def test_completed_result_preserves_requested_and_reported_ids(reported):
    events = _completed(QUESTION)
    events[-1]["response"].update(
        model=reported, id="resp_synthetic", usage={"input_tokens": 11, "output_tokens": 9}
    )
    backend = ChatGPTPlanBackend(FakeConnection(events), MODEL, included_plan_confirmed=True)
    service = ReflectionChatService()
    prepared = service.begin()
    service.generate(prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend))
    receipt = service.ai_receipts[0]
    assert receipt.requested_model == MODEL and receipt.reported_model == reported
    assert receipt.input_tokens == 11 and receipt.output_tokens == 9
    assert receipt.model_agreement == (
        "exact" if reported == MODEL else "unreported" if reported is None else "different"
    )


@pytest.mark.parametrize("cancel", [False, True])
def test_stalled_stream_exits_on_total_deadline_or_stop(monkeypatch, cancel):
    reader, writer = socket.socketpair()
    file = reader.makefile("rb")

    class Response:
        fp = SimpleNamespace(raw=SimpleNamespace(_sock=reader))

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            file.close()

        def readline(self, limit):
            return file.readline(limit)

    transport = OfficialChatGPTHttpTransport()
    monkeypatch.setattr(transport, "_open", lambda *args: Response())
    stop = threading.Event()
    timer = threading.Timer(0.12, stop.set) if cancel else None
    if timer:
        timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(BackendError) as caught:
            list(
                transport.stream_json_controlled(
                    "synthetic", {}, {}, 5 if cancel else 0.15, cancel_event=stop
                )
            )
        assert caught.value.category == ("cancelled" if cancel else "timeout")
        assert time.monotonic() - started < 2
    finally:
        reader.close()
        writer.close()
        if timer:
            timer.join()


def test_model_choice_is_scoped_and_does_not_persist_billing_consent(tmp_path):
    preferences = ModelPreferences(tmp_path)
    preferences.save("synthetic-account-a", "synthetic-model-one")
    reloaded = ModelPreferences(tmp_path)
    assert reloaded.load("synthetic-account-a") == "synthetic-model-one"
    assert reloaded.load("synthetic-account-b") is None
    raw = next(tmp_path.glob("*.json")).read_text()
    assert "consent" not in raw and "synthetic-account-a" not in raw


def test_safe_error_category_never_discloses_raw_backend_message():
    assert "secret" not in BackendError("synthetic secret", category="usage").public_detail


@pytest.mark.parametrize(
    "problem", [None, "missing_terminal", "unfinished", "changed_id", "mismatch"]
)
def test_plan_stream_with_empty_terminal_output_needs_completed_item_and_agreement(problem):
    import copy

    events = _completed(QUESTION)
    item = copy.deepcopy(events[-1]["response"]["output"][0])
    item.update(id="msg_synthetic", status="completed")
    events[-1]["response"]["output"] = []
    done = {"type": "response.output_item.done", "output_index": 0, "item": item}
    added = {
        "type": "response.output_item.added",
        "output_index": 0,
        "item": {"id": "msg_synthetic", "type": "message"},
    }
    events.insert(0, added)
    events.insert(-1, done)
    if problem == "missing_terminal":
        events.pop()
    elif problem == "unfinished":
        item["status"] = "in_progress"
    elif problem == "changed_id":
        item["id"] = "msg_other"
    elif problem == "mismatch":
        item["content"][0]["text"] = "different synthetic content"
    backend = ChatGPTPlanBackend(FakeConnection(events), MODEL, included_plan_confirmed=True)
    service = ReflectionChatService()
    prepared = service.begin()
    if problem:
        with pytest.raises(ValueError):
            service.generate(
                prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend)
            )
        assert not service.transcript
    else:
        service.generate(
            prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend)
        )
        assert service.transcript[0].content_en == QUESTION["question"]["en"]
