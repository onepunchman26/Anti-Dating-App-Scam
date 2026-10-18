"""Synthetic shared-only planning, narrow approvals and evidence correctness."""

import copy
import json
from datetime import UTC, datetime, timedelta

import pytest

from anti_dating_scam.services import work_planning as module
from anti_dating_scam.services.report_review import _encode, _hash
from anti_dating_scam.services.work_planning import WorkPlanningService
from anti_dating_scam.services.work_profile import WorkProfileError


def stamp(delta):
    return (datetime.now(UTC).replace(microsecond=0) + delta).isoformat()


def preferences(mode="friendship"):
    return {
        "schema_version": "1.0",
        "mode": mode,
        "areas": ["Toronto"],
        "availability": [
            {"start_at": stamp(timedelta(days=1)), "end_at": stamp(timedelta(days=1, hours=4))}
        ],
        "budget": {"currency": "CAD", "max_per_person_minor": 5000},
        "duration_minutes": 60,
        "interests": ["art", "learning"],
        "environment": ["public_place", "quiet"],
        "arrangement_needs": ["step_free_access"],
        "expires_at": stamp(timedelta(days=2)),
    }


def context(mode="friendship"):
    first, second = preferences(mode), preferences(mode)
    second["environment"] = ["public_place", "easy_exit"]
    second["arrangement_needs"] = ["accessible_toilet"]
    return {
        "schema_version": "1.0",
        "planning_id": "c" * 32,
        "mode": mode,
        "revision": 1,
        "participants": [
            {"public_id": key * 32, "preferences": value, "approved_digest": _hash(_encode(value))}
            for key, value in [("a", first), ("b", second)]
        ],
    }


def place():
    return {
        "activity_type": "museum",
        "place_name": "Synthetic Museum",
        "address_or_area": "Synthetic Toronto area",
        "planning_area": "Toronto",
        "source_urls": ["https://synthetic.example.org/visit"],
        "checked_at": stamp(timedelta(hours=-1)),
        "verification": "not_verified",
        "verified_facts": [],
        "unknowns": ["all_details_unverified"],
    }


def suggestion_request():
    second = {**place(), "activity_type": "gallery", "place_name": "Synthetic Gallery"}
    return {"context": context(), "places": [place(), second], "version": 1}


@pytest.fixture
def service(tmp_path):
    return WorkPlanningService(tmp_path / "work")


def draft(service, content=None):
    return service.draft(
        {
            "destination": "https://synthetic.example.org",
            "recipient_public_id": "b" * 32,
            "content": content or preferences(),
        }
    )


def receipt(item):
    return {
        "draft_id": item.draft_id,
        "digest": item.digest,
        "destination": item.destination,
        "recipient_public_id": item.recipient_public_id,
        "purpose": item.purpose,
        "confirmed": True,
    }


def test_generator_reads_only_supplied_shared_fields_never_private_files(service, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No private profile/support read allowed")

    monkeypatch.setattr(service.io, "read_profile", forbidden)
    monkeypatch.setattr(service.io.store, "_read", forbidden)
    result = service.suggest(suggestion_request())
    assert result["status"] == "suggestion_not_approved_or_booked"
    assert (
        result["context_authorization"] == "supplied_context_requires_current_server_verification"
    )
    assert result["source_checks"] == "supplied_public_evidence_not_verified_by_generator"
    assert result["location_basis"] == "supplied_coarse_region_not_geocoded"
    assert result["plan"]["budget_basis"] == "shared_budget_ceiling_not_verified_price"
    assert result["plan"]["requirements"] == {
        "environment": ["easy_exit", "public_place", "quiet"],
        "arrangement_needs": ["accessible_toilet", "step_free_access"],
        "status": "confirm_venue_suitability_before_agreeing",
    }
    assert all(option["booking_status"] == "not_booked" for option in result["plan"]["options"])
    assert list(service.directory.iterdir()) == []


def test_export_requires_exact_receipt_and_does_not_read_private_data(service, monkeypatch):
    prepared = draft(service)
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.export(receipt(prepared))
    approved = service.approve(receipt(prepared))
    read = service.io.store._read

    def shared_file_only(path, limit):
        assert path.parent == service.directory
        return read(path, limit)

    monkeypatch.setattr(service.io.store, "_read", shared_file_only)
    exported = service.export(receipt(approved))
    assert exported["content"] == prepared.content.model_dump()
    assert exported["status"] == "approved_for_upload_not_sent"
    assert service.approve(receipt(prepared)) == approved
    assert not list((service.io.root / "outbound").iterdir())


@pytest.mark.parametrize(
    "field,value",
    [
        ("digest", "f" * 64),
        ("recipient_public_id", "d" * 32),
        ("destination", "https://other.example.org"),
        ("purpose", "meeting_feedback"),
    ],
)
def test_receipt_bound_to_content_recipient_destination_and_purpose(service, field, value):
    prepared = draft(service)
    changed = {**receipt(prepared), field: value}
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.approve(changed)
    service.approve(receipt(prepared))
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.export(changed)
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.withdraw(changed)


def test_tampered_content_and_replaced_receipt_id_cannot_reuse_approval(service):
    prepared = draft(service)
    service.approve(receipt(prepared))
    path = service._path(prepared.draft_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    original = copy.deepcopy(data)
    data["content"]["areas"] = ["Ottawa"]
    service.io._atomic(path, data)
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.export(receipt(prepared))
    original["draft_id"] = "f" * 32
    service.io._atomic(path, original)
    with pytest.raises(WorkProfileError, match="^approval_mismatch$"):
        service.export(receipt(prepared))


def test_withdrawal_is_terminal_and_explicitly_local_only(service):
    prepared = draft(service)
    service.approve(receipt(prepared))
    result = service.withdraw(receipt(prepared))
    assert result == {
        "status": "local_approval_withdrawn",
        "remote_withdrawal_required_if_sent": True,
    }
    for action in (service.approve, service.export):
        with pytest.raises(WorkProfileError, match="^approval_withdrawn$"):
            action(receipt(prepared))
    assert service.read({"id": prepared.draft_id}).status == "withdrawn"


def test_expired_authorization_is_rejected_but_can_still_be_withdrawn(service, monkeypatch):
    prepared = draft(service)
    service.approve(receipt(prepared))
    later = datetime.now(UTC) + timedelta(days=3)

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return later

    monkeypatch.setattr(module, "datetime", Later)
    with pytest.raises(WorkProfileError, match="^sharing_expired$"):
        service.export(receipt(prepared))
    assert service.withdraw(receipt(prepared))["status"] == "local_approval_withdrawn"


@pytest.mark.parametrize("kind", ["nested_private", "wrong_mode", "unbound_digest", "same_person"])
def test_joint_context_cannot_carry_private_fields_or_claim_other_basis(service, kind):
    request = suggestion_request()
    first = request["context"]["participants"][0]
    if kind == "nested_private":
        first["preferences"]["private_profile"] = "SYNTHETIC_PRIVATE"
    elif kind == "wrong_mode":
        first["preferences"]["mode"] = "dating"
    elif kind == "unbound_digest":
        first["preferences"]["areas"] = ["Ottawa"]
    else:
        first["public_id"] = "b" * 32
    with pytest.raises(WorkProfileError, match="^(invalid_data|approval_mismatch)$"):
        service.suggest(request)


@pytest.mark.parametrize(
    "url",
    [
        "file:///private.txt",
        "http://example.org/",
        "https://user:pass@example.org/",
        "https://example.org/?private=SYNTHETIC",
        "https://localhost/",
        "https://127.0.0.1/",
        "https://127.1/",
        "https://0x7f.1/",
        "https://[::1]/",
        "https://service.local/",
        "https://example.org\\private",
        "https://example.org/%0d%0aheader",
        "https://example.org/\nprivate",
        "https://example.org/#private",
    ],
)
def test_malicious_or_nonpublic_source_urls_are_rejected(service, url):
    request = suggestion_request()
    request["places"][0]["source_urls"] = [url]
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        service.suggest(request)


@pytest.mark.parametrize("fact", ["hours", "admission_price", "event_date"])
def test_claimed_source_fact_needs_actual_structured_value(service, fact):
    request = suggestion_request()
    request["places"][0].update(verification="official_source_checked", verified_facts=[fact])
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        service.suggest(request)


def test_checked_hours_and_price_constrain_plan_but_never_claim_booking(service):
    request = suggestion_request()
    start = request["context"]["participants"][0]["preferences"]["availability"][0]["start_at"]
    request["places"][0].update(
        verification="official_source_checked",
        verified_facts=["hours", "admission_price"],
        source_open_window={"start_at": start, "end_at": stamp(timedelta(days=1, hours=2))},
        source_admission={"currency": "CAD", "amount_minor": 2500},
    )
    option = service.suggest(request)["plan"]["options"][0]
    assert option["source_admission"]["amount_minor"] == 2500
    assert option["estimated_budget_minor"] == 5000
    assert "availability_not_checked" in option["unknowns"]
    assert "opening_hours_may_change" in option["unknowns"]


def test_known_closed_venue_cannot_be_recommended_by_discarding_checked_hours(service):
    request = suggestion_request()
    request["places"][0].update(
        verification="official_source_checked",
        verified_facts=["hours"],
        source_open_window={
            "start_at": stamp(timedelta(days=1, hours=8)),
            "end_at": stamp(timedelta(days=1, hours=10)),
        },
    )
    with pytest.raises(WorkProfileError, match="^no_shared_time_with_venue_hours$"):
        service.suggest(request)


@pytest.mark.parametrize("currency,price", [("CAD", 6000), ("USD", 2000)])
def test_checked_admission_price_must_fit_shared_budget_and_currency(service, currency, price):
    request = suggestion_request()
    request["places"][0].update(
        verification="official_source_checked",
        verified_facts=["admission_price"],
        source_admission={"currency": currency, "amount_minor": price},
    )
    with pytest.raises(WorkProfileError, match="^admission_exceeds_shared_budget$"):
        service.suggest(request)


def test_place_area_must_be_explicitly_shared_not_inferred_from_address(service):
    request = suggestion_request()
    request["places"][0]["planning_area"] = "Ottawa"
    with pytest.raises(WorkProfileError, match="^place_outside_shared_area$"):
        service.suggest(request)
    request["places"][0]["planning_area"] = "toronto"
    assert service.suggest(request)["location_basis"] == "supplied_coarse_region_not_geocoded"


def test_plan_export_preserves_budget_and_unverified_requirements(service):
    plan = service.suggest(suggestion_request())["plan"]
    prepared = draft(service, plan)
    assert prepared.purpose == "meeting_proposal"
    service.approve(receipt(prepared))
    exported = service.export(receipt(prepared))["content"]
    assert exported["budget_basis"] == "shared_budget_ceiling_not_verified_price"
    assert exported["requirements"]["status"] == "confirm_venue_suitability_before_agreeing"
    assert "accessible_toilet" in exported["requirements"]["arrangement_needs"]


def test_shared_feedback_has_no_private_report_or_free_text_field(service):
    content = {
        "schema_version": "1.0",
        "mode": "friendship",
        "planning_id": "c" * 32,
        "plan_version": 1,
        "choice": "undecided",
        "expires_at": stamp(timedelta(days=1)),
    }
    prepared = draft(service, content)
    assert prepared.purpose == "meeting_feedback"
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        draft(service, {**content, "private_reflection": "SYNTHETIC_PRIVATE"})


def test_approval_write_failure_keeps_draft_unapproved(service, monkeypatch):
    prepared = draft(service)

    def fail(*args):
        raise OSError("synthetic private failure")

    monkeypatch.setattr(service.io, "_atomic", fail)
    with pytest.raises(WorkProfileError, match="^storage_unavailable$"):
        service.approve(receipt(prepared))
    assert service.read({"id": prepared.draft_id}).status == "draft"


def test_timestamp_and_expiry_boundaries_match_remote_contract(service):
    value = preferences()
    value["expires_at"] = stamp(timedelta(days=31))
    with pytest.raises(WorkProfileError, match="^sharing_expiry_too_long$"):
        draft(service, value)
    value = preferences()
    value["availability"][0]["start_at"] = value["availability"][0]["start_at"].replace("T", " ")
    with pytest.raises(WorkProfileError, match="^invalid_data$"):
        draft(service, value)


def test_cli_dispatch_uses_planning_service_and_dynamic_model_schema(service):
    from anti_dating_scam.work_cli import dispatch

    assert "planning-suggest" in dispatch("schema", {}, service.io.root)["operations"]
    result = dispatch("planning-suggest", suggestion_request(), service.io.root)
    assert result["plan"]["requirements"]["status"] == "confirm_venue_suitability_before_agreeing"
