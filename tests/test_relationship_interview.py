import json
from types import SimpleNamespace

import pytest
from test_web_companion import Connection

from anti_dating_scam.services.relationship_interview import (
    INITIAL_AREAS,
    InterviewState,
    accept_reply,
)
from anti_dating_scam.services.web_companion import CompanionError, WebCompanion


class InterviewConnection(Connection):
    reply = {}
    calls = 0

    def create_backend(self, model, included_plan_confirmed):
        base = super().create_backend(model, included_plan_confirmed)
        owner = self
        original = base.chat_result

        def chat(request):
            original(request)
            owner.reviewed_request = request
            owner.calls += 1
            return SimpleNamespace(text=json.dumps(owner.reply))

        base.chat_result = chat
        return base


def setup(tmp_path):
    connection = InterviewConnection()
    service = WebCompanion(tmp_path / "state", connection)
    service.initialize({"confirmed": True})
    session = service.create_session({"topic": "dating", "guided": True, "language": "zh-CN"})
    return service, connection, session


def send(service, connection, session, area="pace", text="I prefer slow introductions.", **extra):
    connection.reply = {
        "response": "Thank you for explaining your preference.",
        "question": "What pace feels comfortable?" if area else "",
        "area": area,
        "observations": [],
        **extra,
    }
    return service.send(
        {
            "session_id": session["id"],
            "expected_revision": session["revision"],
            "text": text,
            "language": "en",
            "model": "synthetic",
            "cloud_consent": True,
            "included_plan_confirmed": True,
        }
    )


def command(service, session, action, **extra):
    return service.interview_control(
        {
            "session_id": session["id"],
            "expected_revision": session["revision"],
            "action": action,
            "confirmed": True,
            **extra,
        }
    )


def test_opening_is_counted_and_ninth_question_cannot_escape_after_restart(tmp_path):
    service, connection, session = setup(tmp_path)
    assert session["interview"]["question_count"] == 1
    assert "关系" in session["messages"][0]["content"]
    for area in INITIAL_AREAS[1:]:
        session = send(service, connection, session, area)
    assert session["interview"]["question_count"] == 8
    restarted = WebCompanion(tmp_path / "state", connection)
    restarted.initialize({"confirmed": True})
    session = send(restarted, connection, session, "goal")
    assert "?" not in session["messages"][-1]["content"]
    assert session["interview"]["phase"] == "draft"
    assert session["interview"]["question_count"] == 8
    assert restarted._ready().read_profile().revision == 0


@pytest.mark.parametrize(
    "action,status",
    [("skip", "skipped"), ("unknown", "unknown"), ("inexperienced", "inexperienced")],
)
def test_skip_states_survive_selected_reuse_and_model_cannot_overwrite(tmp_path, action, status):
    service, connection, session = setup(tmp_path)
    session = command(service, session, action)
    copied = service.create_session(
        {"topic": "dating", "guided": True, "reuse_session_id": session["id"]}
    )
    assert copied["messages"] == []
    copied = send(
        service,
        connection,
        copied,
        "goal",
        observations=[{"area": "goal", "text": "New conclusion", "quote": "slow"}],
        clarification=True,
    )
    assert copied["interview"]["notes"]["goal"]["status"] == status
    assert "?" not in copied["messages"][-1]["content"]
    assert status in str(connection.reviewed_request.system)
    fresh = service.create_session({"topic": "dating", "guided": True})
    assert fresh["interview"]["notes"] == {}
    with pytest.raises(CompanionError, match="reuse_mismatch"):
        service.create_session(
            {"topic": "friendship", "guided": True, "reuse_session_id": session["id"]}
        )


def test_review_remove_pause_and_draft_are_zero_model_calls(tmp_path):
    service, connection, session = setup(tmp_path)
    session = command(service, session, "review", area="pace", text="Only weekends work.")
    session = command(service, session, "pause")
    with pytest.raises(CompanionError, match="paused"):
        send(service, connection, session)
    session = command(service, session, "resume")
    session = command(service, session, "draft")
    assert connection.calls == 0
    session = send(
        service,
        connection,
        session,
        "pace",
        observations=[{"area": "pace", "text": "Every day", "quote": "slow"}],
        clarification=True,
    )
    assert session["interview"]["notes"]["pace"]["text"] == "Only weekends work."
    assert "?" not in session["messages"][-1]["content"]
    session = command(service, session, "remove", area="pace")
    session = send(
        service,
        connection,
        session,
        None,
        observations=[{"area": "pace", "text": "Restored", "quote": "slow"}],
    )
    assert session["interview"]["notes"]["pace"]["text"] == ""
    assert service._ready().read_profile().revision == 0


def test_exact_source_and_single_question_checked_before_state_change(tmp_path):
    service, connection, session = setup(tmp_path)
    with pytest.raises(ValueError, match="unsupported_interview_evidence"):
        send(
            service,
            connection,
            session,
            observations=[{"area": "pace", "text": "Unfounded", "quote": "not supplied"}],
        )
    stored = service.read_session({"session_id": session["id"]})
    assert stored.revision == 1
    assert stored.interview.notes == {} and stored.interview.question_count == 1
    with pytest.raises(ValueError, match="multiple_interview_questions"):
        accept_reply(
            InterviewState(),
            json.dumps({"response": "OK", "area": "pace", "question": "Why? How?"}),
            "hello",
        )
    with pytest.raises(ValueError, match="question_outside"):
        accept_reply(InterviewState(), json.dumps({"response": "Why?"}), "hello")


def test_one_answer_can_fill_multiple_areas_without_profile_publication(tmp_path):
    service, connection, session = setup(tmp_path)
    text = "I want a committed relationship. I am only free on weekends."
    session = send(
        service,
        connection,
        session,
        "care",
        text,
        observations=[
            {"area": "goal", "text": "A committed relationship", "quote": "committed relationship"},
            {"area": "availability", "text": "Weekends", "quote": "only free on weekends"},
        ],
    )
    assert set(session["interview"]["notes"]) == {"goal", "availability"}
    assert all(n["status"] == "draft" for n in session["interview"]["notes"].values())
    assert service._ready().read_profile().revision == 0


def test_life_lenses_are_opt_in_and_control_is_revision_guarded(tmp_path):
    service, connection, session = setup(tmp_path)
    before = session
    session = send(service, connection, session, "mind")
    assert "?" not in session["messages"][-1]["content"]
    with pytest.raises(CompanionError, match="revision_conflict"):
        command(service, before, "draft")
    session = command(service, session, "explore", area="mind")
    session = send(service, connection, session, "mind")
    assert "?" in session["messages"][-1]["content"]
    assert session["interview"]["question_count"] == 1
    connection.identity = "synthetic-other"
    with pytest.raises(CompanionError, match="account_changed"):
        command(service, session, "draft")


@pytest.mark.parametrize("text", ["暂停", "skip", "先看草稿", "没有经验"])
def test_short_natural_controls_do_not_spend_model_calls(tmp_path, text):
    service, connection, session = setup(tmp_path)
    session = send(service, connection, session, text=text)
    assert connection.calls == 0
    assert session["interview"]["question_count"] == 1
