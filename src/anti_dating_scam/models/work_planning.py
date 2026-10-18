"""Minimal shared activity contracts. No private profile, transcript or report fields."""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timedelta
from typing import Annotated, Literal
from urllib.parse import unquote, urlsplit

from pydantic import Field, model_validator

from .work_profile import (
    PRIVATE_LABEL_TERMS,
    PUBLIC_LABEL_PATTERN,
    ApprovedRequest,
    Digest,
    Identifier,
    InterestToken,
    MatchingMode,
    WorkModel,
)

Stamp = Annotated[str, Field(min_length=20, max_length=40)]
Currency = Literal["USD", "CAD", "EUR", "GBP", "CNY", "AUD", "JPY"]
PLACE_PATTERN = (
    r"^[A-Za-z0-9\u00C0-\u024F\u3400-\u9FFF][A-Za-z0-9\u00C0-\u024F\u3400-\u9FFF '\u2019.,()&/-]*$"
)
PlaceLabel = Annotated[str, Field(min_length=1, max_length=160, pattern=PLACE_PATTERN)]
Fact = Literal["address", "hours", "admission_price", "event_date"]
Unknown = Literal[
    "availability_not_checked",
    "booking_not_made",
    "opening_hours_may_change",
    "price_may_change",
    "accessibility_to_confirm",
    "weather_to_check",
    "travel_time_unknown",
    "all_details_unverified",
]


def timestamp(value: str) -> datetime:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value):
        raise ValueError("utc_timestamp_required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("utc_timestamp_required")
    return parsed


def public_url(value: str) -> str:
    if re.search(r"[\s\\\x00-\x1f\x7f]|%(?:0[0-9a-f]|1[0-9a-f]|7f)", value, re.I):
        raise ValueError("public_https_source_required")
    parsed = urlsplit(value)
    if re.search(r"%(?![0-9a-f]{2})", parsed.path, re.I):
        raise ValueError("public_https_source_required")
    if re.search(PRIVATE_LABEL_TERMS, unquote(parsed.path, errors="strict"), re.I):
        raise ValueError("public_source_path_rejected")
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
        or parsed.fragment
        or parsed.query
        or len(value) > 400
    ):
        raise ValueError("public_https_source_required")
    if (
        host == "localhost"
        or "." not in host
        or host.endswith((".local", ".internal", ".localhost", ".test", ".invalid"))
    ):
        raise ValueError("public_https_source_required")
    labels = host.split(".")
    if not re.fullmatch(r"[A-Za-z]{2,63}", labels[-1]) or any(
        not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
        for label in labels
    ):
        raise ValueError("public_https_source_required")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("public_https_source_required")
    return value


class Window(WorkModel):
    start_at: Stamp
    end_at: Stamp

    @model_validator(mode="after")
    def ordered(self):
        if timestamp(self.start_at) >= timestamp(self.end_at):
            raise ValueError("invalid_window")
        return self


class Budget(WorkModel):
    currency: Currency
    max_per_person_minor: int = Field(ge=0, le=100000)


class SourceAdmission(WorkModel):
    currency: Currency
    amount_minor: int = Field(ge=0, le=100000)


Environment = Literal[
    "public_place", "quiet", "outdoors", "indoors", "alcohol_free", "easy_exit", "step_free"
]
ArrangementNeed = Literal[
    "vegetarian",
    "vegan",
    "halal_options",
    "allergen_menu",
    "step_free_access",
    "accessible_toilet",
    "quiet_space",
    "short_walk",
]


class PlanningRequirements(WorkModel):
    environment: list[Environment] = Field(min_length=1, max_length=7)
    arrangement_needs: list[ArrangementNeed] = Field(max_length=8)
    status: Literal["confirm_venue_suitability_before_agreeing"]

    @model_validator(mode="after")
    def unique(self):
        if len(set(self.environment)) != len(self.environment) or len(
            set(self.arrangement_needs)
        ) != len(self.arrangement_needs):
            raise ValueError("duplicate_requirements")
        return self


class SharedPlanningPreferences(WorkModel):
    schema_version: Literal["1.0"]
    mode: MatchingMode
    areas: list[
        Annotated[str, Field(min_length=2, max_length=60, pattern=PUBLIC_LABEL_PATTERN)]
    ] = Field(min_length=1, max_length=5)
    availability: list[Window] = Field(min_length=1, max_length=5)
    budget: Budget
    duration_minutes: int = Field(ge=15, le=480)
    interests: list[InterestToken] = Field(min_length=1, max_length=8)
    environment: list[Environment] = Field(min_length=1, max_length=5)
    arrangement_needs: list[ArrangementNeed] = Field(max_length=6)
    expires_at: Stamp

    @model_validator(mode="after")
    def coherent(self):
        expiry = timestamp(self.expires_at)
        for window in self.availability:
            if timestamp(window.end_at) > expiry:
                raise ValueError("window_after_expiry")
        for area in self.areas:
            if re.search(PRIVATE_LABEL_TERMS, area, re.I):
                raise ValueError("public_label_rejected")
        for values in [self.areas, self.interests, self.environment, self.arrangement_needs]:
            if len(set(values)) != len(values):
                raise ValueError("duplicate_choices")
        return self


class SharedParticipant(WorkModel):
    public_id: Identifier
    preferences: SharedPlanningPreferences
    approved_digest: Digest


class JointPlanningContext(WorkModel):
    schema_version: Literal["1.0"]
    planning_id: Identifier
    mode: MatchingMode
    revision: int = Field(ge=1, le=9007199254740991)
    participants: list[SharedParticipant] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def separate(self):
        ids = [p.public_id for p in self.participants]
        if (
            len(set(ids)) != 2
            or ids != sorted(ids)
            or any(p.preferences.mode != self.mode for p in self.participants)
        ):
            raise ValueError("joint_context_mismatch")
        return self


class PlaceEvidence(WorkModel):
    activity_type: Literal[
        "cafe_walk", "museum", "gallery", "park_walk", "board_games", "volunteer", "online_chat"
    ]
    place_name: Annotated[str, Field(min_length=1, max_length=80, pattern=PLACE_PATTERN)]
    address_or_area: PlaceLabel
    planning_area: Annotated[str, Field(min_length=2, max_length=60, pattern=PUBLIC_LABEL_PATTERN)]
    source_urls: list[Annotated[str, Field(min_length=8, max_length=400)]] = Field(
        min_length=1, max_length=3
    )
    checked_at: Stamp
    verification: Literal["official_source_checked", "not_verified"]
    verified_facts: list[Fact] = Field(max_length=4)
    unknowns: list[Unknown] = Field(min_length=1, max_length=8)
    source_open_window: Window | None = None
    source_admission: SourceAdmission | None = None
    source_event_at: Stamp | None = None

    @model_validator(mode="after")
    def safe_evidence(self):
        for label in [self.place_name, self.address_or_area, self.planning_area]:
            if not re.fullmatch(PLACE_PATTERN, label) or re.search(
                PRIVATE_LABEL_TERMS, label, re.I
            ):
                raise ValueError("public_place_label_required")
        for url in self.source_urls:
            public_url(url)
        timestamp(self.checked_at)
        if self.source_event_at is not None:
            timestamp(self.source_event_at)
        if self.verification == "not_verified" and (
            self.verified_facts or "all_details_unverified" not in self.unknowns
        ):
            raise ValueError("unverified_facts")
        for fact, value in (
            ("hours", self.source_open_window),
            ("admission_price", self.source_admission),
            ("event_date", self.source_event_at),
        ):
            if fact in self.verified_facts and value is None:
                raise ValueError("verified_fact_value_required")
            if value is not None and (
                fact not in self.verified_facts or self.verification != "official_source_checked"
            ):
                raise ValueError("source_value_requires_checked_fact")
        if len(set(self.verified_facts)) != len(self.verified_facts):
            raise ValueError("duplicate_facts")
        return self


class MeetingOption(PlaceEvidence):
    option_id: Literal["a", "b", "c"]
    start_at: Stamp
    duration_minutes: int = Field(ge=15, le=480)
    estimated_budget_minor: int = Field(ge=0, le=100000)
    currency: Currency
    sequence: list[
        Literal[
            "meet_public",
            "coffee",
            "walk",
            "visit_exhibit",
            "play_game",
            "meal",
            "online_conversation",
            "leave_independently",
        ]
    ] = Field(min_length=1, max_length=5)
    shared_interest_reasons: list[InterestToken] = Field(min_length=1, max_length=8)
    conversation_starters: list[
        Literal[
            "shared_hobby",
            "recent_learning",
            "preferred_pace",
            "next_activity",
            "weekend_interests",
        ]
    ] = Field(min_length=1, max_length=3)
    arrival_exit: Literal["independent_arrival_easy_exit"]
    fallback: Literal[
        "reschedule", "public_indoor_alternative", "online_chat", "end_without_pressure"
    ]
    booking_status: Literal["not_booked"]

    @model_validator(mode="after")
    def supported_times_and_price(self):
        start = timestamp(self.start_at)
        end = start + timedelta(minutes=self.duration_minutes)
        if self.source_open_window and (
            start < timestamp(self.source_open_window.start_at)
            or end > timestamp(self.source_open_window.end_at)
        ):
            raise ValueError("outside_checked_open_window")
        if self.source_admission and (
            self.source_admission.currency != self.currency
            or self.source_admission.amount_minor > self.estimated_budget_minor
        ):
            raise ValueError("admission_exceeds_budget_ceiling")
        if self.source_event_at and start != timestamp(self.source_event_at):
            raise ValueError("event_time_mismatch")
        return self


class MeetingPlan(WorkModel):
    schema_version: Literal["1.0"]
    mode: MatchingMode
    context_digest: Digest
    version: int = Field(ge=1, le=9007199254740991)
    expires_at: Stamp
    options: list[MeetingOption] = Field(min_length=2, max_length=3)
    budget_basis: Literal["shared_budget_ceiling_not_verified_price"]
    requirements: PlanningRequirements

    @model_validator(mode="after")
    def coherent(self):
        expiry = timestamp(self.expires_at)
        if len({o.option_id for o in self.options}) != len(self.options):
            raise ValueError("duplicate_options")
        for option in self.options:
            if timestamp(option.start_at) + timedelta(minutes=option.duration_minutes) > expiry:
                raise ValueError("plan_after_expiry")
        return self


class SharedFeedback(WorkModel):
    schema_version: Literal["1.0"]
    mode: MatchingMode
    planning_id: Identifier
    plan_version: int = Field(ge=1, le=9007199254740991)
    choice: Literal["again", "undecided", "not_now", "no_again"]
    expires_at: Stamp


class SharingDraftRequest(WorkModel):
    destination: str = Field(max_length=300)
    recipient_public_id: Identifier
    content: SharedPlanningPreferences | MeetingPlan | SharedFeedback


class SharingDraft(SharingDraftRequest):
    draft_id: Identifier
    digest: Digest
    purpose: Literal["activity_preferences", "meeting_proposal", "meeting_feedback"]
    created_at: str
    status: Literal["draft", "approved", "withdrawn"]
    approved_at: str | None = None

    @model_validator(mode="after")
    def correct_purpose(self):
        purpose = (
            "activity_preferences"
            if isinstance(self.content, SharedPlanningPreferences)
            else "meeting_feedback"
            if isinstance(self.content, SharedFeedback)
            else "meeting_proposal"
        )
        if self.purpose != purpose or (self.status == "approved" and not self.approved_at):
            raise ValueError("approval_purpose_mismatch")
        return self


class SharingApproval(ApprovedRequest):
    draft_id: Identifier
    digest: Digest
    destination: str = Field(max_length=300)
    recipient_public_id: Identifier
    purpose: Literal["activity_preferences", "meeting_proposal", "meeting_feedback"]


class PlanningSuggestRequest(WorkModel):
    context: JointPlanningContext
    places: list[PlaceEvidence] = Field(min_length=2, max_length=3)
    version: int = Field(ge=1, le=9007199254740991)


def planning_schema(model):
    schema = model.model_json_schema()
    schema["x-slowmatch-label-forbidden-pattern"] = PRIVATE_LABEL_TERMS
    return schema
