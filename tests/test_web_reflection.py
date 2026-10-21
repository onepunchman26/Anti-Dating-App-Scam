import json
from types import SimpleNamespace

import pytest

from anti_dating_scam.ai.privacy import outbound_messages
from anti_dating_scam.services.web_companion import CompanionError, WebCompanion
from anti_dating_scam.services.work_profile import WorkProfileError

WORDS = "I wanted a quiet afternoon, but we changed plans without discussing it."


def content():
    return {
        "events": [
            {
                "event_id": "a" * 32,
                "occurred_at": "Unknown",
                "context": "A reported change of plans.",
                "source": "self_recollection",
                "material_id": None,
                "quote_or_summary": WORDS,
                "fact_status": "reported",
            }
        ],
        "interpretations": [
            {
                "explanation": "There may be a difference in planning preferences.",
                "evidence_ids": ["a" * 32],
                "alternative_explanations": ["A misunderstanding is possible."],
                "uncertainty": "The other person's reasons are unknown.",
            }
        ],
        "repeated_event_ids": [],
        "repetition_context": "",
        "concern": "needs_clarification",
        "uncertainty": "One account, not a verified pattern.",
        "optional_actions": ["clarify", "slow_down"],
        "action_status": "open",
        "personal_feelings": "I wanted a calmer afternoon.",
        "expectations_supported": [],
        "expectations_unknown": ["How we will agree on changes."],
        "boundaries_and_pace": ["Discuss changes before committing."],
        "self_insights_to_review": [],
    }


class Connection:
    identity = "synthetic-private-reflection"
    hook = None

    def __init__(self):
        self.payload = content()
        self.calls = []

    def status(self):
        return SimpleNamespace(
            connected=True, sharing=True, client_id=self.identity, label="Synthetic"
        )

    def diagnostic(self):
        return SimpleNamespace(phase="connected")

    def create_backend(self, model, included_plan_confirmed):
        assert model == "synthetic" and included_plan_confirmed is True
        owner = self

        class Backend:
            recipient = "https://api.openai.com/v1/responses#synthetic"

            def set_cancel_event(self, cancel):
                self.cancel = cancel

            def chat_result(self, request):
                owner.calls.append(
                    outbound_messages(request, recipient=self.recipient, local=False)
                )
                if owner.hook:
                    owner.hook()
                return SimpleNamespace(text=getattr(owner, "raw_text", json.dumps(owner.payload)))

        return Backend()


@pytest.fixture
def prepared(tmp_path):
    connection = Connection()
    companion = WebCompanion(tmp_path / "state", connection)
    companion.initialize({"confirmed": True})
    created = companion.create_session({"topic": "reflection"})
    session = companion.read_session({"session_id": created["id"]})
    session.messages = [
        {"role": "user", "content": WORDS},
        {"role": "assistant", "content": "Assistant-only invented claim."},
    ]
    session.revision = 2
    companion.vault._atomic(
        companion.vault.root / "sessions" / (session.id + ".json"), session.model_dump()
    )
    request = {
        "session_id": session.id,
        "expected_revision": 2,
        "language": "en",
        "model": "synthetic",
        "cloud_consent": True,
        "included_plan_confirmed": True,
    }
    return companion, connection, request


def test_review_save_correct_restart_delete_reuses_existing_store(prepared):
    c, connection, request = prepared
    draft = c.dispatch("reflection-draft", request)
    assert draft["saved"] is False
    assert c.dispatch("reflection-list", {}) == {"records": []}
    record = c.dispatch(
        "reflection-approve",
        {
            "session_id": request["session_id"],
            "expected_revision": 2,
            "confirmed": True,
            "content": draft["content"],
        },
    )
    corrected = {**record["content"], "personal_feelings": "I felt disappointed, not unsafe."}
    updated = c.dispatch(
        "reflection-save",
        {
            "record_id": record["record_id"],
            "expected_revision": 1,
            "confirmed": True,
            "content": corrected,
        },
    )
    assert updated["revision"] == 2
    assert "calmer afternoon" not in json.dumps(updated["history"])
    with pytest.raises(WorkProfileError, match="revision_conflict"):
        c.dispatch(
            "reflection-save",
            {
                "record_id": record["record_id"],
                "expected_revision": 1,
                "confirmed": True,
                "content": record["content"],
            },
        )
    restarted = WebCompanion(c.state.root, connection)
    restarted.initialize({"confirmed": True})
    assert (
        restarted.dispatch("reflection-read", {"record_id": record["record_id"]})["content"]
        == corrected
    )
    restarted.dispatch(
        "reflection-delete",
        {"record_id": record["record_id"], "expected_revision": 2, "confirmed": True},
    )
    removed = restarted.dispatch("reflection-read", {"record_id": record["record_id"]})
    assert removed["status"] == "deleted" and removed["content"] is None
    raw = (restarted.vault.root / "relationship-support" / "state.json").read_text()
    assert WORDS not in raw and corrected["personal_feelings"] not in raw
    assert (
        restarted.read_session({"session_id": request["session_id"]}).messages[0]["content"]
        == WORDS
    )
    assert restarted.vault.read_profile().revision == 0
    assert len(connection.calls) == 1  # Reading/editing/deleting never calls AI.


@pytest.mark.parametrize("field", ["cloud_consent", "included_plan_confirmed"])
@pytest.mark.parametrize("value", [False, 1, "true"])
def test_no_draft_without_exact_cloud_permission(prepared, field, value):
    c, connection, request = prepared
    with pytest.raises(ValueError):
        c.dispatch("reflection-draft", {**request, field: value})
    assert connection.calls == []


@pytest.mark.parametrize(
    "change", ["assistant_quote", "new_quote", "verified", "diagnosis", "extra_field"]
)
def test_invalid_model_evidence_never_becomes_a_draft(prepared, change):
    c, connection, request = prepared
    if change == "assistant_quote":
        connection.payload["events"][0]["quote_or_summary"] = "Assistant-only invented claim."
    elif change == "new_quote":
        connection.payload["events"][0]["quote_or_summary"] = "They threatened me."
    elif change == "verified":
        connection.payload["events"][0]["fact_status"] = "direct_observation"
    elif change == "diagnosis":
        connection.payload["interpretations"][0]["explanation"] = "This person is a psychopath."
    else:
        connection.payload["secret_score"] = 10
    with pytest.raises(ValueError):
        c.dispatch("reflection-draft", request)
    assert c.dispatch("reflection-list", {})["records"] == []


def test_selected_session_only_no_profile_or_other_transcript(prepared):
    c, connection, request = prepared
    other = c.create_session({"topic": "support"})
    untouched = c.read_session({"session_id": other["id"]})
    untouched.messages = [{"role": "user", "content": "OTHER_SESSION_PRIVATE_SENTINEL"}]
    c.vault._atomic(c.vault.root / "sessions" / (untouched.id + ".json"), untouched.model_dump())
    c.apply_profile(
        {
            "expected_revision": 0,
            "confirmed": True,
            "changes": [
                {
                    "action": "upsert",
                    "claim": {
                        "topic": "values",
                        "text": "PROFILE_PRIVATE_SENTINEL",
                        "source": {"source_type": "self_report", "reference": "Synthetic"},
                        "confirmation": "confirmed",
                        "uncertainty": "Unverified",
                    },
                }
            ],
        }
    )
    c.dispatch("reflection-draft", request)
    sent = json.dumps(connection.calls)
    assert WORDS in sent and "PRIVATE_SENTINEL" not in sent


def test_account_change_and_stop_discard_inflight_proposal(prepared):
    c, connection, request = prepared
    connection.hook = lambda: c.cancel.set()
    with pytest.raises(ValueError, match="cancelled"):
        c.dispatch("reflection-draft", request)
    connection.hook = lambda: setattr(connection, "identity", "different-synthetic-account")
    with pytest.raises(CompanionError, match="account_changed"):
        c.dispatch("reflection-draft", request)


def test_stale_session_prevents_approval_and_no_empty_generation(prepared):
    c, connection, request = prepared
    with pytest.raises(CompanionError, match="revision_conflict"):
        c.dispatch(
            "reflection-approve",
            {
                "session_id": request["session_id"],
                "expected_revision": 1,
                "confirmed": True,
                "content": content(),
            },
        )
    fresh = c.create_session({"topic": "preparation"})
    with pytest.raises(ValueError, match="selected_conversation_required"):
        c.dispatch(
            "reflection-draft", {**request, "session_id": fresh["id"], "expected_revision": 0}
        )
    assert connection.calls == []


def test_concurrent_profile_write_is_refused(prepared):
    c, _, _ = prepared
    c.lock.acquire()
    try:
        with pytest.raises(CompanionError, match="request_in_progress"):
            c.apply_profile({})
    finally:
        c.lock.release()


def test_conflicting_json_fields_are_not_silently_accepted(prepared):
    c, connection, request = prepared
    connection.raw_text = '{"events":[], ' + json.dumps(content())[1:]
    with pytest.raises(ValueError):
        c.dispatch("reflection-draft", request)
    assert c.dispatch("reflection-list", {})["records"] == []
