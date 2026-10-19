"""Three synthetic participants; no independent account acceptance claims."""

import json
from types import SimpleNamespace

import pytest
from test_work_planning import place, preferences

from anti_dating_scam.ai.privacy import outbound_messages
from anti_dating_scam.services.report_review import _encode, _hash
from anti_dating_scam.services.web_companion import WebCompanion


def request():
    members = []
    for key in "abc":
        p = preferences() | {
            "origin_area": "Toronto",
            "max_travel_minutes": 30,
            "avoid_interests": [],
            "values": ["honesty"],
            "communication_preferences": [],
            "allow_shared_ai": True,
            "allow_romance_analysis": False,
        }
        members.append(
            {"public_id": key * 32, "preferences": p, "approved_digest": _hash(_encode(p))}
        )
    context = {
        "schema_version": "group-1.0",
        "planning_id": "d" * 32,
        "mode": "friendship",
        "revision": 1,
        "participants": members,
    }
    return {
        "context": context,
        "context_digest": _hash(_encode(context)),
        "places": [place(), place()],
        "version": 1,
        "model": "synthetic",
        "language": "en",
        "cloud_consent": True,
        "included_plan_confirmed": True,
    }


class Connection:
    calls = 0
    messages = None
    identity = "synthetic"
    change_identity = False

    def status(self):
        return SimpleNamespace(connected=True, client_id=self.identity)

    def create_backend(self, model, included_plan_confirmed):
        assert model == "synthetic" and included_plan_confirmed is True
        parent = self

        class Backend:
            recipient = "https://api.openai.com/v1/responses#synthetic"

            def set_cancel_event(self, event):
                self.event = event

            def chat_result(self, reviewed):
                parent.calls += 1
                parent.messages = outbound_messages(reviewed, recipient=self.recipient, local=False)
                if parent.change_identity:
                    parent.identity = "other"
                return SimpleNamespace(
                    text=json.dumps(
                        {
                            "discussion_points": ["Talk about a shared interest."],
                            "uncertainty": "Check the venue and route.",
                        }
                    )
                )

        return Backend()


def test_group_generation_does_not_open_a_private_vault(tmp_path, monkeypatch):
    connection = Connection()
    service = WebCompanion(tmp_path / "state", connection)
    monkeypatch.setattr(service, "_ready", lambda: pytest.fail("Private vault accessed"))
    data = request()
    result = service.dispatch("group-suggest", data)
    assert connection.calls == 1 and service.vault is None
    assert result["plan"]["context_digest"] == data["context_digest"]
    assert result["approved_digest"] == _hash(_encode({k: result[k] for k in ("plan", "analysis")}))
    assert len(result["plan"]["options"]) == 2
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(connection.messages)
    assert not list((tmp_path / "state").rglob("sessions/*.json"))


@pytest.mark.parametrize(
    "change", ["refuse", "withdraw", "budget_currency", "area", "private", "digest", "approval"]
)
def test_invalid_or_unapproved_context_never_calls_model(tmp_path, change):
    connection = Connection()
    service = WebCompanion(tmp_path / "state", connection)
    data = request()
    third = data["context"]["participants"][2]
    if change == "refuse":
        third["preferences"]["allow_shared_ai"] = False
    if change == "withdraw":
        third["preferences"]["allow_shared_ai"] = False
    if change == "budget_currency":
        third["preferences"]["budget"]["currency"] = "USD"
    if change == "area":
        third["preferences"]["areas"] = ["Ottawa"]
    if change == "private":
        third["preferences"]["private_profile"] = "SYNTHETIC_PRIVATE_MARKER"
    third["approved_digest"] = _hash(_encode(third["preferences"]))
    data["context_digest"] = _hash(_encode(data["context"]))
    if change == "digest":
        data["context_digest"] = "0" * 64
    if change == "approval":
        data["cloud_consent"] = 1
    with pytest.raises(ValueError):
        service.shared_group(data)
    assert connection.calls == 0


def test_account_change_during_generation_rejects_draft(tmp_path):
    connection = Connection()
    connection.change_identity = True
    service = WebCompanion(tmp_path / "state", connection)
    with pytest.raises(ValueError, match="account_changed"):
        service.shared_group(request())
