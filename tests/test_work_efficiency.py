"""Bounded outputs preserve revisions/consent without exposing irrelevant private text."""

import json

import pytest

from anti_dating_scam.services.work_profile import WorkProfileError
from anti_dating_scam.work_cli import dispatch


def update(text, revision=0, topic="values", **extra):
    return {
        "expected_revision": revision,
        "confirmed": True,
        "changes": [{"action": "upsert", "claim": {
            "topic": topic, "text": text,
            "source": {"source_type": "self_report", "reference": "synthetic-test"},
            "confirmation": "confirmed", "uncertainty": "Self-report only",
        }}],
        **extra,
    }


def test_index_reflects_correction_and_removal_without_private_text(tmp_path):
    path = tmp_path / "private"
    dispatch("profile-update", update("SYNTHETIC_PRIVATE_MARKER"), path)
    state = dispatch("profile-index", {}, path)
    assert state["revision"] == 1
    assert state["topics"] == {"values": {"count": 1, "needs_confirmation": 0}}
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(state)
    saved = dispatch("profile-read", {}, path)
    claim = saved["claims"][0]
    request = {"expected_revision": 1, "confirmed": True, "changes": [
        {"action": "remove", "claim_id": claim["id"]}
    ], "response": "changes"}
    removed = dispatch("profile-update", request, path)
    assert removed["revision"] == 2 and removed["claims"] == []
    assert removed["removed_ids"] == [claim["id"]]
    assert dispatch("profile-index", {}, path)["claim_count"] == 0


def test_changed_response_does_not_repeat_unrelated_history_and_keeps_full_state(tmp_path):
    path = tmp_path / "private"
    dispatch("profile-update", update("SYNTHETIC_UNRELATED_PRIVATE"), path)
    changed = dispatch("profile-update", update(
        "SYNTHETIC_NEW_FRIEND_NEED", 1, "friend_needs", response="changes"
    ), path)
    assert changed["revision"] == 2 and len(changed["claims"]) == 1
    assert changed["selection"] == {"complete": False, "changed_only": True}
    assert "SYNTHETIC_UNRELATED_PRIVATE" not in json.dumps(changed)
    assert len(dispatch("profile-read", {}, path)["claims"]) == 2
    with pytest.raises(WorkProfileError, match="revision_conflict"):
        dispatch("profile-update", update("stale", 0, response="changes"), path)


def test_selective_schema_has_no_storage_side_effect_or_unrelated_schema(tmp_path):
    path = tmp_path / "not-created"
    compact = dispatch("schema", {"compact": True}, path)
    selected = dispatch("schema", {"operation": "profile-update"}, path)
    assert "profile-index" in compact["operations"]
    assert "MeetingPlan" not in json.dumps(selected)
    assert selected["schema"]["properties"]["response"]["enum"] == ["full", "changes"]
    assert not path.exists()
    assert len(json.dumps(compact)) < len(json.dumps(dispatch("schema", {}, path)))


@pytest.mark.parametrize("args", [
    {"operation": "unknown"}, {"operation": []}, {"object": "unknown"},
    {"compact": "true"}, {"compact": 1},
    {"compact": True, "object": "PrivateProfile"},
])
def test_schema_selection_is_strict(args):
    with pytest.raises(WorkProfileError):
        dispatch("schema", args)
