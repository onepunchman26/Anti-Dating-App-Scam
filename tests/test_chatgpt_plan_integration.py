"""Synthetic ChatGPT-plan adapter plus the real reflection service boundary.

No test here starts OAuth, opens a browser, calls HTTP, or uses a real model.
"""

import json
import threading

import pytest

from anti_dating_scam.ai.chatgpt_auth import (
    RESPONSES_URL,
    ChatGPTConnectionStatus,
    ChatGPTModelChoice,
)
from anti_dating_scam.ai.chatgpt_backend import ChatGPTPlanBackend
from anti_dating_scam.ai.privacy import (
    BackendError,
    ChatRequest,
    ReviewedDisclosure,
    disclosure_fingerprint,
)
from anti_dating_scam.services.reflection_chat import (
    ReflectionChatError,
    ReflectionChatService,
    ReflectionChatStaleError,
)

MODEL = "synthetic-chat-model"
ANSWER = "Synthetic: I ask for a pause when a conversation gets intense."
QUESTION = {
    "question": {
        "en": "What helps you feel understood during a difficult conversation?",
        "zh": "在困难的对话中，什么能让你感到被理解？",
    }
}


def _json(value):
    return json.dumps(value, ensure_ascii=False)


def _completed(value):
    text = _json(value)
    return [
        {"type": "response.output_text.delta", "delta": text},
        {
            "type": "response.completed",
            "response": {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": text}],
                    }
                ],
            },
        },
    ]


def _portrait():
    return {
        "report": {
            "schema_version": "0.2",
            "report_type": "self_portrait",
            "data_coverage": {
                "sources_read": ["S001"],
                "covered": [
                    {
                        "en": "One typed answer was considered.",
                        "zh": "仅考虑了一段亲自输入的回答。",
                    }
                ],
                "not_covered": [
                    {
                        "en": "Other situations and repeated behavior are unknown.",
                        "zh": "其他情境与重复行为尚不清楚。",
                    }
                ],
            },
            "claims": [
                {
                    "topic": "communication",
                    "type": "speculation",
                    "confidence": "low",
                    "claim": {
                        "en": "This statement may describe a preference for a pause.",
                        "zh": "这段话可能表达了暂停的偏好。",
                    },
                    "evidence": [{"quote": ANSWER, "source": "S001"}],
                }
            ],
            "consistency_findings": [],
            "open_questions": [
                {
                    "en": "What makes a pause feel respectful?",
                    "zh": "怎样的暂停会让你感到被尊重？",
                }
            ],
            "caveats": [
                {
                    "en": "A provisional interpretation of one typed answer only.",
                    "zh": "仅对一段亲自输入的回答作暂定解释。",
                }
            ],
        }
    }


class FakeTransport:
    def __init__(self, *scripts):
        self.scripts = list(scripts)
        self.calls = []
        self.on_stream = None

    def stream_json(self, url, payload, headers, timeout):
        self.calls.append((url, payload, headers, timeout))
        if self.on_stream is not None:
            self.on_stream()
        script = self.scripts.pop(0)
        if isinstance(script, Exception):
            raise script
        yield from script


class FakeConnection:
    def __init__(self, *scripts):
        self.transport = FakeTransport(*scripts)
        self.client_id = "oaiapp_synthetic_account"
        self.token_calls = 0
        self.model_calls = 0

    def status(self):
        return ChatGPTConnectionStatus(
            connected=True,
            sharing=True,
            client_id=self.client_id,
        )

    def list_models(self):
        self.model_calls += 1
        return (ChatGPTModelChoice(slug=MODEL, display_name="Synthetic model"),)

    def access_token(self):
        self.token_calls += 1
        return "synthetic-token"


def _review(prepared, backend, *, recipient=None):
    source = prepared.request
    recipient = backend.recipient if recipient is None else recipient
    return ChatRequest(
        messages=source.messages,
        system=source.system,
        response_schema=source.response_schema,
        allow_schema_fallback=False,
        privacy_mode="reviewed_remote",
        disclosure=ReviewedDisclosure(
            recipient=recipient,
            messages=source.messages,
            reviewed=True,
            fingerprint=disclosure_fingerprint(source.messages, source.system, recipient),
        ),
    )


def _assert_strict_objects(value):
    if isinstance(value, list):
        for item in value:
            _assert_strict_objects(item)
    elif isinstance(value, dict):
        assert "default" not in value
        if value.get("type") == "object":
            assert value["additionalProperties"] is False
            assert value["required"] == list(value["properties"])
        for item in value.values():
            _assert_strict_objects(item)


def test_real_reflection_flow_uses_approved_strict_completed_responses_only():
    connection = FakeConnection(
        _completed(QUESTION), _completed(QUESTION), _completed(_portrait())
    )
    backend = ChatGPTPlanBackend(connection, MODEL, included_plan_confirmed=True)
    service = ReflectionChatService()

    first = service.begin()
    assert connection.transport.calls == []
    question = service.generate(
        first, backend, confirmed=True, reviewed_request=_review(first, backend)
    )
    assert question.en == QUESTION["question"]["en"]

    turn = service.propose_turn(ANSWER)
    service.generate(turn, backend, confirmed=True, reviewed_request=_review(turn, backend))
    assert [item.role for item in service.transcript] == ["assistant", "user", "assistant"]
    service.stop()
    assert len(connection.transport.calls) == 2  # End made no model call.

    prepared = service.portrait_request()
    portrait = service.generate(
        prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend)
    )
    assert portrait["report"]["claims"][0]["confidence"] == "low"
    assert portrait["report"]["claims"][0]["evidence"] == [
        {"quote": ANSWER, "source": "S001"}
    ]
    assert [item[0] for item in connection.transport.calls] == [RESPONSES_URL] * 3
    for _url, payload, headers, _timeout in connection.transport.calls:
        assert headers == {"Authorization": "Bearer synthetic-token"}
        assert payload["model"] == MODEL
        assert payload["stream"] is True and payload["store"] is False
        assert payload["text"]["format"]["type"] == "json_schema"
        assert payload["text"]["format"]["strict"] is True
        _assert_strict_objects(payload["text"]["format"]["schema"])
    assert len(connection.transport.calls) == 3


def test_plan_confirmation_blocks_model_call_even_after_review():
    connection = FakeConnection(_completed(QUESTION))
    backend = ChatGPTPlanBackend(connection, MODEL)
    service = ReflectionChatService()
    prepared = service.begin()
    with pytest.raises(ReflectionChatError):
        service.generate(
            prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend)
        )
    assert connection.transport.calls == []
    assert connection.model_calls == connection.token_calls == 0
    assert service.transcript == ()


@pytest.mark.parametrize("change", ["recipient", "account"])
def test_changed_recipient_or_account_rejects_before_model_call(change):
    connection = FakeConnection(_completed(QUESTION))
    backend = ChatGPTPlanBackend(connection, MODEL, included_plan_confirmed=True)
    service = ReflectionChatService()
    prepared = service.begin()
    reviewed = _review(prepared, backend)
    if change == "recipient":
        reviewed = _review(prepared, backend, recipient="https://synthetic.invalid/other")
    else:
        connection.client_id = "oaiapp_another_synthetic_account"
    with pytest.raises(ReflectionChatError):
        service.generate(prepared, backend, confirmed=True, reviewed_request=reviewed)
    assert connection.transport.calls == []
    assert service.transcript == ()


@pytest.mark.parametrize(
    "script",
    [
        BackendError("ChatGPT usage limit reached. Review Manage usage."),
        [{"type": "response.incomplete", "response": {"status": "incomplete"}}],
        [{"type": "response.output_text.delta", "delta": _json(QUESTION)}],
    ],
)
def test_usage_limit_or_incomplete_stream_never_accepts_or_retries(script):
    connection = FakeConnection(script)
    backend = ChatGPTPlanBackend(connection, MODEL, included_plan_confirmed=True)
    service = ReflectionChatService()
    prepared = service.begin()
    with pytest.raises(ReflectionChatError):
        service.generate(
            prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend)
        )
    assert len(connection.transport.calls) == 1
    assert service.transcript == ()
    with pytest.raises(ReflectionChatStaleError):
        service.accept_turn(prepared.request_id, _json(QUESTION))


def test_cancel_event_and_end_discard_late_completed_reply():
    connection = FakeConnection(_completed(QUESTION))
    backend = ChatGPTPlanBackend(connection, MODEL, included_plan_confirmed=True)
    service = ReflectionChatService()
    prepared = service.begin()
    cancelled = threading.Event()
    backend.set_cancel_event(cancelled)

    def end_during_stream():
        service.stop()
        cancelled.set()

    connection.transport.on_stream = end_during_stream
    with pytest.raises(ReflectionChatError):
        service.generate(
            prepared, backend, confirmed=True, reviewed_request=_review(prepared, backend)
        )
    assert len(connection.transport.calls) == 1
    assert service.transcript == () and not service.running
    with pytest.raises(ReflectionChatStaleError):
        service.accept_turn(prepared.request_id, _json(QUESTION))
