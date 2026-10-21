import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from test_web_companion import Connection

from anti_dating_scam.ai.privacy import outbound_messages
from anti_dating_scam.services.web_companion import WebCompanion


def summary(**changes):
    return dict(
        schema_version="2.0",
        mode="dating",
        summary_id="a" * 32,
        version=1,
        expires_at=(datetime.now(UTC) + timedelta(days=1)).isoformat(),
        alias="Synthetic",
        age_band="25-34",
        city="Toronto",
        areas=[],
        relationship_goal="long_term",
        accepted_goals=["long_term"],
        accepted_age_bands=["25-34"],
        values=["kindness"],
        life_directions=[],
        communication_preferences=[],
        interests=["reading"],
        preferences=[],
        visibility="participants",
        discoverable=True,
        **changes,
    )


class AI(Connection):
    output = None
    on_reply = None

    def create_backend(self, model, included_plan_confirmed):
        owner = self

        class Backend:
            recipient = "https://api.openai.com/v1/responses#synthetic"

            def set_cancel_event(self, cancel):
                self.cancel = cancel

            def chat_result(self, request):
                owner.requests = outbound_messages(request, recipient=self.recipient, local=False)
                if owner.on_reply:
                    owner.on_reply()
                return SimpleNamespace(text=json.dumps(owner.output))

        return Backend()


def prepared(tmp_path):
    connection = AI()
    service = WebCompanion(tmp_path / "state", connection)
    service.initialize({"confirmed": True})
    peer = {**summary(), "summary_id": "b" * 32}
    args = dict(
        bundle=dict(
            schema_version="1.0",
            mode="dating",
            own_summary=summary(),
            candidates=[dict(public_id="b" * 32, summary=peer)],
        ),
        model="synthetic",
        language="en",
        cloud_consent=True,
        included_plan_confirmed=True,
    )
    connection.output = dict(
        candidates=[
            dict(
                public_id="b" * 32,
                reasons=["Shared reading"],
                differences=[],
                questions=["What do you enjoy reading?"],
                unknowns=["Behavior is not verified"],
            )
        ],
        uncertainty="Self-report only",
    )
    return service, connection, args


def test_review_saved_private_and_no_profile_read_by_default(tmp_path, monkeypatch):
    service, connection, args = prepared(tmp_path)
    monkeypatch.setattr(
        service.vault, "read_profile", lambda: pytest.fail("private profile loaded")
    )
    result = service.dispatch("candidate-review", args)
    assert result["status"] == "private_review" and not result["published"]
    saved = service.dispatch("matching-result", {})
    assert saved["local_receipt"] == result["local_receipt"]
    assert saved["review"]["aliases"]["b" * 32] == "Synthetic"
    assert len(list((service.vault.root / "matching-drafts").glob("*.json"))) == 1
    assert "owner_confirmed_statements" in str(connection.requests)


@pytest.mark.parametrize(
    "change", ["missing_consent", "numeric_consent", "private_peer", "expired", "mode", "duplicate"]
)
def test_invalid_context_fails_before_model(tmp_path, change):
    service, connection, args = prepared(tmp_path)
    if change == "missing_consent":
        args["cloud_consent"] = False
    if change == "numeric_consent":
        args["included_plan_confirmed"] = 1
    if change == "private_peer":
        args["bundle"]["candidates"][0]["summary"]["private_profile"] = "PRIVATE"
    if change == "expired":
        args["bundle"]["own_summary"]["expires_at"] = "2000-01-01T00:00:00Z"
    if change == "mode":
        args["bundle"]["mode"] = "friendship"
    if change == "duplicate":
        args["bundle"]["candidates"] *= 2
    with pytest.raises(ValueError):
        service.dispatch("candidate-review", args)
    assert connection.requests is None


@pytest.mark.parametrize("change", ["identity", "cancel", "wrong_peer", "extra_score"])
def test_unsafe_or_stale_result_is_not_saved(tmp_path, change):
    service, connection, args = prepared(tmp_path)
    if change == "identity":
        connection.on_reply = lambda: setattr(connection, "identity", "another-account")
    if change == "cancel":
        connection.on_reply = service.cancel.set
    if change == "wrong_peer":
        connection.output["candidates"][0]["public_id"] = "c" * 32
    if change == "extra_score":
        connection.output["candidates"][0]["score"] = 99
    root = service.vault.root
    with pytest.raises(ValueError):
        service.dispatch("candidate-review", args)
    assert not (root / "matching-drafts").exists()


def test_draft_pins_owner_facts_and_leaves_private_story_out(tmp_path):
    service, connection, _ = prepared(tmp_path)
    session = service.create_session({"topic": "dating"})
    path = service.vault.root / "sessions" / (session["id"] + ".json")
    session["messages"] = [
        {
            "role": "user",
            "content": "SYNTHETIC_PRIVATE_STORY. I want a long-term relationship and read.",
        }
    ]
    service.vault._atomic(path, session)
    fixed = {
        k: summary()[k]
        for k in ("alias", "age_band", "city", "accepted_age_bands", "interests", "version")
    }
    args = dict(
        **fixed,
        session_id=session["id"],
        expected_revision=0,
        mode="dating",
        model="synthetic",
        language="en",
        cloud_consent=True,
        included_plan_confirmed=True,
    )
    connection.output = {
        k: summary()[k]
        for k in (
            "relationship_goal",
            "accepted_goals",
            "values",
            "life_directions",
            "communication_preferences",
            "preferences",
        )
    }
    result = service.dispatch("summary-draft", args)
    assert result["summary"]["city"] == "Toronto" and not result["published"]
    assert "SYNTHETIC_PRIVATE_STORY" not in json.dumps(result)
    connection.output["city"] = "Ottawa"
    with pytest.raises(ValueError, match="fixed_fields_changed"):
        service.dispatch("summary-draft", args)


def test_only_confirmed_owner_claims_explicitly_selected(tmp_path, monkeypatch):
    service, connection, args = prepared(tmp_path)
    claims = [
        SimpleNamespace(
            confirmation="confirmed", text="CONFIRMED_SYNTHETIC", uncertainty="self-report"
        ),
        SimpleNamespace(
            confirmation="proposed", text="UNAPPROVED_SYNTHETIC", uncertainty="unknown"
        ),
    ]
    monkeypatch.setattr(service.vault, "read_profile", lambda: SimpleNamespace(claims=claims))
    service.dispatch("candidate-review", {**args, "include_profile": True})
    text = str(connection.requests)
    assert "CONFIRMED_SYNTHETIC" in text and "UNAPPROVED_SYNTHETIC" not in text
