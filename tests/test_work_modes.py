"""Synthetic v2 mode separation and non-destructive legacy compatibility."""

from datetime import UTC, datetime, timedelta

import pytest

from anti_dating_scam.models.work_profile import (
    PublishedProfile,
    ShareableProfileDraft,
)
from anti_dating_scam.services import work_profile as module
from anti_dating_scam.services.report_review import _encode, _hash
from anti_dating_scam.services.work_profile import WorkProfileError, WorkProfileService


def summary(mode="dating"):
    common = {
        "schema_version": "2.0",
        "mode": mode,
        "expires_at": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "summary_id": ("a" if mode == "dating" else "b") * 32,
        "version": 1,
        "alias": "Synthetic Cedar",
        "age_band": "25-34",
        "city": "Toronto",
        "areas": [],
        "accepted_age_bands": ["25-34"],
        "values": ["honesty"],
        "communication_preferences": ["reflective"],
        "interests": ["reading"],
        "preferences": ["honesty"],
        "visibility": "participants",
        "discoverable": True,
    }
    if mode == "dating":
        return common | {
            "relationship_goal": "long_term",
            "accepted_goals": ["long_term"],
            "life_directions": ["still_exploring"],
        }
    return common | {
        "friendship_intent": "activity_companions",
        "accepted_friendship_intents": ["activity_companions", "conversation"],
        "activity_styles": ["one_on_one", "quiet"],
        "interaction_frequency": "occasional",
        "accepted_frequencies": ["occasional"],
        "boundaries": ["platonic_only", "privacy_respected"],
    }


@pytest.fixture
def service(tmp_path):
    return WorkProfileService(tmp_path / "work")


def draft(service, content):
    return service.draft_summary(
        {
            "adult_confirmed": True,
            "expected_revision": 0,
            "destination": "https://synthetic.example.org",
            "summary": content,
        }
    )


def approve_request(prepared):
    return {
        "draft_id": prepared.draft_id,
        "expected_revision": prepared.source_revision,
        "summary_digest": prepared.summary_digest,
        "destination": prepared.destination,
        "audience": "participants",
        "confirmed": True,
    }


def export_request(receipt):
    return {
        "publication_id": receipt.publication_id,
        "summary_digest": receipt.summary_digest,
        "destination": receipt.destination,
    }


def test_each_mode_has_its_own_approval_and_withdrawal_does_not_affect_other_mode(service):
    dating = service.approve_summary(approve_request(draft(service, summary("dating"))))
    friendship = service.approve_summary(approve_request(draft(service, summary("friendship"))))
    assert dating.publication_id != friendship.publication_id
    assert dating.purpose == "dating_matching" and friendship.purpose == "friendship_matching"
    service.export_summary(export_request(dating))
    service.record_publication(
        {**export_request(dating), "confirmed": True, "status": "withdrawn", "remote_version": 1}
    )
    with pytest.raises(WorkProfileError, match="^approval_withdrawn$"):
        service.export_summary(export_request(dating))
    exported = service.export_summary(export_request(friendship))
    assert exported["summary"]["mode"] == "friendship"
    assert "relationship_goal" not in exported["summary"]
    assert "life_directions" not in exported["summary"]
    assert exported["summary"]["boundaries"] == ["platonic_only", "privacy_respected"]


@pytest.mark.parametrize(
    "mode,extra",
    [
        ("friendship", {"relationship_goal": "long_term"}),
        ("friendship", {"life_directions": ["build_family"]}),
        ("dating", {"friendship_intent": "close_friendship"}),
        ("friendship", {"private_risk": "SYNTHETIC_PRIVATE"}),
    ],
)
def test_modes_reject_cross_intent_or_private_fields(service, mode, extra):
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        draft(service, summary(mode) | extra)


def test_friendship_cannot_be_approved_with_an_existing_dating_digest(service):
    dating = draft(service, summary())
    friendship = draft(service, summary("friendship"))
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.approve_summary(
            approve_request(friendship) | {"summary_digest": dating.summary_digest}
        )


def test_legacy_summary_remains_readable_but_cannot_be_new_draft_approved_or_exported(service):
    legacy = summary()
    legacy["schema_version"] = "1.0"
    legacy.pop("mode")
    legacy.pop("expires_at")
    identifier = "c" * 32
    prepared = ShareableProfileDraft(
        draft_id=identifier,
        source_revision=0,
        destination="https://synthetic.example.org",
        summary=legacy,
        summary_digest=_hash(_encode(legacy)),
        created_at="legacy-synthetic-record",
    )
    old_receipt = PublishedProfile(
        publication_id=identifier,
        draft_id=identifier,
        source_revision=0,
        destination=prepared.destination,
        summary=legacy,
        summary_digest=prepared.summary_digest,
        approved_at="legacy-synthetic-approval",
    )
    service.store._write_new(
        service.root / "drafts" / (identifier + ".json"), _encode(prepared.model_dump())
    )
    service.store._write_new(
        service.root / "publications" / (identifier + ".json"), _encode(old_receipt.model_dump())
    )
    assert service.read_summary({"id": identifier}).summary.schema_version == "1.0"
    assert service.publication_status({"id": identifier}).summary.schema_version == "1.0"
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        draft(service, legacy)
    with pytest.raises(WorkProfileError, match="^mode_upgrade_required$"):
        service.approve_summary(approve_request(prepared))
    with pytest.raises(WorkProfileError, match="^mode_upgrade_required$"):
        service.export_summary(export_request(old_receipt))


def test_v2_expiry_cannot_be_omitted_or_extended_by_reusing_approval(service):
    missing = summary("friendship")
    missing.pop("expires_at")
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        draft(service, missing)
    prepared = draft(service, summary("friendship"))
    path = service.root / "drafts" / (prepared.draft_id + ".json")
    changed = prepared.model_dump()
    changed["summary"]["expires_at"] = (datetime.now(UTC) + timedelta(days=60)).isoformat()
    service._atomic(path, changed)
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.approve_summary(approve_request(prepared))


@pytest.mark.parametrize("mode", ["dating", "friendship"])
def test_current_expired_summary_cannot_be_approved_or_exported(service, monkeypatch, mode):
    prepared = draft(service, summary(mode))
    approved = service.approve_summary(approve_request(prepared))
    future = datetime.now(UTC) + timedelta(days=31)

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return future

    monkeypatch.setattr(module, "datetime", Later)
    with pytest.raises(WorkProfileError, match="^summary_approval_expired$"):
        service.approve_summary(approve_request(prepared))
    with pytest.raises(WorkProfileError, match="^summary_approval_expired$"):
        service.export_summary(export_request(approved))


def test_mode_specific_missing_assessment_field_is_a_safe_error(service):
    profile = service.update_profile(
        {
            "confirmed": True,
            "expected_revision": 0,
            "changes": [
                {
                    "action": "upsert",
                    "claim": {
                        "topic": "communication",
                        "text": "Synthetic self report.",
                        "source": {"source_type": "self_report", "reference": "Synthetic session"},
                        "confirmation": "confirmed",
                        "uncertainty": "Self-report only.",
                    },
                }
            ],
        }
    )
    prepared = service.prepare_assessment(
        {"expected_revision": 1, "peer_summary": summary("friendship")}
    )
    metadata = prepared["context"]
    with pytest.raises(WorkProfileError, match="^unsupported_assessment_evidence$"):
        service.save_assessment(
            {
                "confirmed": True,
                "context_id": metadata["context_id"],
                "own_revision": 1,
                "peer_summary_digest": metadata["peer_summary_digest"],
                "possible_alignment": [
                    {
                        "text": "Synthetic point.",
                        "own_claim_ids": [profile.claims[0].id],
                        "peer_fields": ["relationship_goal"],
                        "uncertainty": "This dating-only field is absent.",
                    }
                ],
                "questions_and_tensions": [],
                "unknowns": ["Intent remains unknown."],
                "respectful_questions": [],
                "caveats": ["Only shared material is available."],
            }
        )


def test_fresh_private_context_rejects_expired_peer_shared_summary(service):
    peer = summary("friendship")
    peer["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    with pytest.raises(WorkProfileError, match="^summary_approval_expired$"):
        service.prepare_assessment({"expected_revision": 0, "peer_summary": peer})


def test_shared_expiry_syntax_matches_site_contract(service):
    value = summary()
    value["expires_at"] = value["expires_at"].replace("T", " ")
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        draft(service, value)
