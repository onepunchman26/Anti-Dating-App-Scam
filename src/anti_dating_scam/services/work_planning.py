"""Local approval receipts and deterministic shared-only planning, with no network IO."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from anti_dating_scam.models.work_planning import (
    MeetingPlan,
    PlanningSuggestRequest,
    SharedFeedback,
    SharedPlanningPreferences,
    SharingApproval,
    SharingDraft,
    SharingDraftRequest,
    timestamp,
)
from anti_dating_scam.models.work_profile import IdentifierRequest
from anti_dating_scam.services.report_review import _encode, _hash
from anti_dating_scam.services.work_profile import (
    WorkProfileError,
    WorkProfileService,
    _destination,
    now,
    safe_operation,
)


class WorkPlanningService:
    @safe_operation
    def __init__(self, data_dir: Path | None = None):
        self.io = WorkProfileService(data_dir)
        self.directory = self.io.root / "shared-planning"
        self.io.store._mkdir(self.directory)

    def _path(self, identifier):
        return self.directory / (identifier + ".json")

    def _read(self, identifier):
        item = self.io._read(self._path(identifier), SharingDraft)
        if item.draft_id != identifier:
            raise WorkProfileError("approval_mismatch")
        return item

    def _valid(self, item):
        expiry = timestamp(item.content.expires_at)
        if expiry <= datetime.now(UTC):
            raise WorkProfileError("sharing_expired")
        if expiry > datetime.now(UTC) + timedelta(days=30):
            raise WorkProfileError("sharing_expiry_too_long")
        if _hash(_encode(item.content.model_dump())) != item.digest:
            raise WorkProfileError("approval_mismatch")
        if item.status == "withdrawn":
            raise WorkProfileError("approval_withdrawn")
        if isinstance(item.content, MeetingPlan):
            for option in item.content.options:
                if timestamp(option.checked_at) > datetime.now(UTC):
                    raise WorkProfileError("future_source_check")
                if timestamp(option.start_at) <= datetime.now(UTC):
                    raise WorkProfileError("plan_start_expired")
        if isinstance(item.content, SharedPlanningPreferences):
            if not all(
                timestamp(window.start_at) > datetime.now(UTC)
                for window in item.content.availability
            ):
                raise WorkProfileError("availability_expired")

    @safe_operation
    def draft(self, arguments):
        request = SharingDraftRequest.model_validate(arguments)
        purpose = (
            "activity_preferences"
            if isinstance(request.content, SharedPlanningPreferences)
            else "meeting_feedback"
            if isinstance(request.content, SharedFeedback)
            else "meeting_proposal"
        )
        item = SharingDraft(
            **(request.model_dump() | {"destination": _destination(request.destination)}),
            draft_id=uuid4().hex,
            digest=_hash(_encode(request.content.model_dump())),
            purpose=purpose,
            created_at=now(),
            status="draft",
        )
        self._valid(item)
        with self.io.store._writer(self.io.root):
            self.io.store._write_new(self._path(item.draft_id), _encode(item.model_dump()))
        return item

    @safe_operation
    def read(self, arguments):
        request = IdentifierRequest.model_validate(arguments)
        return self._read(request.id)

    @safe_operation
    def approve(self, arguments):
        request = SharingApproval.model_validate(arguments)
        with self.io.store._writer(self.io.root):
            item = self._read(request.draft_id)
            self._valid(item)
            if (item.digest, item.destination, item.recipient_public_id, item.purpose) != (
                request.digest,
                _destination(request.destination),
                request.recipient_public_id,
                request.purpose,
            ):
                raise WorkProfileError("approval_mismatch")
            item = SharingDraft.model_validate(
                item.model_dump() | {"status": "approved", "approved_at": item.approved_at or now()}
            )
            self.io._atomic(self._path(item.draft_id), item.model_dump())
            return item

    @safe_operation
    def export(self, arguments):
        request = SharingApproval.model_validate(arguments)
        with self.io.store._writer(self.io.root):
            item = self._read(request.draft_id)
            self._valid(item)
            if item.status != "approved" or (
                item.digest,
                item.destination,
                item.recipient_public_id,
                item.purpose,
            ) != (
                request.digest,
                _destination(request.destination),
                request.recipient_public_id,
                request.purpose,
            ):
                raise WorkProfileError("approval_mismatch")
            # Only this selected shared receipt is read, never profile/support files.
            return {
                "status": "approved_for_upload_not_sent",
                "purpose": item.purpose,
                "destination": item.destination,
                "recipient_public_id": item.recipient_public_id,
                "approved_digest": item.digest,
                "content": item.content.model_dump(),
            }

    @safe_operation
    def withdraw(self, arguments):
        request = SharingApproval.model_validate(arguments)
        with self.io.store._writer(self.io.root):
            item = self._read(request.draft_id)
            if (item.digest, item.destination, item.recipient_public_id, item.purpose) != (
                request.digest,
                _destination(request.destination),
                request.recipient_public_id,
                request.purpose,
            ):
                raise WorkProfileError("approval_mismatch")
            item = SharingDraft.model_validate(item.model_dump() | {"status": "withdrawn"})
            self.io._atomic(self._path(item.draft_id), item.model_dump())
        return {"status": "local_approval_withdrawn", "remote_withdrawal_required_if_sent": True}

    @safe_operation
    def suggest(self, arguments):
        """The entire generator input is typed shared context + public place evidence.

        No profile read, retrieval, model call, or free narrative reaches this method.
        The calling ChatGPT verifies sources through available search before supplying
        evidence. The source status is an assertion, never a claim this function browsed.
        """
        request = PlanningSuggestRequest.model_validate(arguments)
        context = request.context
        current = datetime.now(UTC)
        first, second = [p.preferences for p in context.participants]
        for participant in context.participants:
            if _hash(_encode(participant.preferences.model_dump())) != participant.approved_digest:
                raise WorkProfileError("approval_mismatch")
            if timestamp(participant.preferences.expires_at) <= current:
                raise WorkProfileError("sharing_expired")
        common = set(first.interests) & set(second.interests)
        common_areas = {area.strip().lower() for area in first.areas} & {
            area.strip().lower() for area in second.areas
        }
        if not common or not common_areas:
            raise WorkProfileError("no_shared_activity_basis")
        if first.budget.currency != second.budget.currency:
            raise WorkProfileError("currency_agreement_required")
        duration = min(first.duration_minutes, second.duration_minutes)
        windows = []
        for a in first.availability:
            for b in second.availability:
                start, end = (
                    max(
                        timestamp(a.start_at), timestamp(b.start_at), current + timedelta(minutes=5)
                    ),
                    min(timestamp(a.end_at), timestamp(b.end_at)),
                )
                if end - start >= timedelta(minutes=duration):
                    windows.append((start, end))
        if not windows:
            raise WorkProfileError("no_shared_time_window")
        expiry = min(timestamp(first.expires_at), timestamp(second.expires_at))
        if expiry > current + timedelta(days=30):
            raise WorkProfileError("sharing_expiry_too_long")
        ceiling = min(first.budget.max_per_person_minor, second.budget.max_per_person_minor)
        options = []
        for index, place in enumerate(request.places):
            if place.planning_area.strip().lower() not in common_areas:
                raise WorkProfileError("place_outside_shared_area")
            if timestamp(place.checked_at) > current:
                raise WorkProfileError("future_source_check")
            interests = {
                "museum": {"learning", "art"},
                "gallery": {"art", "learning"},
                "park_walk": {"outdoors", "sport"},
                "board_games": {"games"},
                "volunteer": {"volunteering", "learning"},
                "cafe_walk": {"reading", "cooking", "outdoors"},
                "online_chat": set(common),
            }[place.activity_type] & common
            if not interests:
                raise WorkProfileError("place_not_based_on_shared_interests")
            eligible_starts = []
            for start, end in windows:
                if place.source_open_window:
                    start = max(start, timestamp(place.source_open_window.start_at))
                    end = min(end, timestamp(place.source_open_window.end_at))
                if place.source_event_at:
                    event_time = timestamp(place.source_event_at)
                    if event_time < start:
                        continue
                    start = event_time
                if end - start >= timedelta(minutes=duration):
                    eligible_starts.append(start)
            if not eligible_starts:
                raise WorkProfileError("no_shared_time_with_venue_hours")
            if place.source_admission and (
                place.source_admission.currency != first.budget.currency
                or place.source_admission.amount_minor > ceiling
            ):
                raise WorkProfileError("admission_exceeds_shared_budget")
            activity = {
                "museum": "visit_exhibit",
                "gallery": "visit_exhibit",
                "park_walk": "walk",
                "board_games": "play_game",
                "cafe_walk": "coffee",
                "volunteer": "walk",
                "online_chat": "online_conversation",
            }[place.activity_type]
            unknowns = list(
                dict.fromkeys(
                    [
                        "booking_not_made",
                        "availability_not_checked",
                        "opening_hours_may_change",
                        "price_may_change",
                        "accessibility_to_confirm",
                        *place.unknowns,
                    ]
                )
            )
            sequence = (
                ["online_conversation"]
                if place.activity_type == "online_chat"
                else ["meet_public", activity, "leave_independently"]
            )
            options.append(
                place.model_dump()
                | {
                    "option_id": "abc"[index],
                    "start_at": min(eligible_starts).isoformat(),
                    "duration_minutes": duration,
                    "estimated_budget_minor": ceiling,
                    "currency": first.budget.currency,
                    "sequence": sequence,
                    "shared_interest_reasons": sorted(interests),
                    "conversation_starters": ["shared_hobby", "preferred_pace"],
                    "arrival_exit": "independent_arrival_easy_exit",
                    "fallback": "end_without_pressure",
                    "booking_status": "not_booked",
                    "unknowns": unknowns,
                }
            )
        requirements = {
            "environment": sorted(set(first.environment + second.environment)),
            "arrangement_needs": sorted(set(first.arrangement_needs + second.arrangement_needs)),
            "status": "confirm_venue_suitability_before_agreeing",
        }
        plan = MeetingPlan(
            schema_version="1.0",
            mode=context.mode,
            context_digest=_hash(_encode(context.model_dump())),
            version=request.version,
            expires_at=expiry.isoformat(),
            options=options,
            budget_basis="shared_budget_ceiling_not_verified_price",
            requirements=requirements,
        )
        return {
            "plan": plan.model_dump(),
            "status": "suggestion_not_approved_or_booked",
            "source_checks": "supplied_public_evidence_not_verified_by_generator",
            "context_authorization": "supplied_context_requires_current_server_verification",
            "location_basis": "supplied_coarse_region_not_geocoded",
            "budget_basis": plan.budget_basis,
            "arrangement_requirements": requirements["arrangement_needs"],
            "environment_requirements": requirements["environment"],
            "requirements_status": requirements["status"],
        }


PLANNING_OPERATIONS = {
    "sharing-draft": ("draft", SharingDraftRequest),
    "sharing-read": ("read", IdentifierRequest),
    "sharing-approve": ("approve", SharingApproval),
    "sharing-export": ("export", SharingApproval),
    "sharing-withdraw": ("withdraw", SharingApproval),
    "planning-suggest": ("suggest", PlanningSuggestRequest),
}
