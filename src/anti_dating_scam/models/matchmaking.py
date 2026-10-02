"""Pydantic contracts for the rendezvous matchmaking API (docs/12, ADR-012)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class MatchmakingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


AdultAge = Annotated[int, Field(ge=18, le=120)]
Pseudonym = Annotated[str, Field(min_length=1, max_length=40)]
Fingerprint = Annotated[str, Field(pattern=r"^[0-9a-fA-F]{64}$")]


class RegisterRequest(MatchmakingRequest):
    pseudonym: str = Field(max_length=40, description="Pseudonym only; never a real name.")
    geohash: str = Field(
        min_length=4, max_length=6,
        description="Client-derived coarse geohash bucket (4-6 chars accepted). "
        "Raw coordinates are never accepted.",
    )
    contact: str = Field(
        max_length=120, description="Contact channel; revealed only after a mutual accept."
    )
    consent_confirmed: bool = False
    age: AdultAge = Field(description="Required self-declared adult age; not verified identity.")
    seeking_age_min: AdultAge | None = None
    seeking_age_max: AdultAge | None = None
    gender: str | None = Field(
        default=None, max_length=20,
        description="Tier-1 basic: woman | man | nonbinary, or omitted."
    )
    seeking_genders: list[str] | None = Field(
        default=None, max_length=3,
        description="Tier-1 gender filter; empty/omitted means everyone. Orientation is "
        "expressed only as gender + seeking; no orientation label is stored.",
    )


class RegisterResponse(BaseModel):
    pseudonym: str
    created_at: str
    token: str = Field(
        description="Per-registration access token; required for every later call. "
        "P0 stand-in for real auth — cannot be recovered if lost."
    )


class AttestRequest(MatchmakingRequest):
    pseudonym: Pseudonym
    token: str = Field(default="", max_length=128, exclude=True)
    fingerprint: Fingerprint = Field(
        description="Client-computed SHA-256 of the canonical card JSON — "
        "the server never sees card content.",
    )


class AttestResponse(BaseModel):
    pseudonym: str
    fingerprint: str
    version: int
    attested_at: str
    algorithm: str
    token: str
    disclaimer: str


class NearbyCandidate(BaseModel):
    pseudonym: str
    bucket: str
    attestation_summary: dict[str, Any]


class NearbyResponse(BaseModel):
    candidates: list[NearbyCandidate]


class IntroduceRequest(MatchmakingRequest):
    initiator: Pseudonym
    token: str = Field(default="", max_length=128, exclude=True)
    recipient: Pseudonym


class IntroductionResponse(BaseModel):
    introduction_id: str
    status: str


class RespondRequest(MatchmakingRequest):
    pseudonym: Pseudonym
    token: str = Field(default="", max_length=128, exclude=True)
    introduction_id: str = Field(min_length=1, max_length=32)
    accept: bool


class InboxEntry(BaseModel):
    introduction_id: str
    counterpart_pseudonym: str
    direction: str  # "sent" | "received"
    status: str  # "pending" | "matched" | "declined"
    awaiting_you: bool
    created_at: str


class InboxResponse(BaseModel):
    introductions: list[InboxEntry]


class MatchPacketResponse(BaseModel):
    introduction_id: str
    counterpart_pseudonym: str
    counterpart_contact: str
    locked_fingerprint: str
    attestation_summary: dict[str, Any]
    how_to_verify: str
    disclaimer: str


class VerifyCardRequest(MatchmakingRequest):
    pseudonym: Pseudonym
    token: str = Field(default="", max_length=128, exclude=True)
    introduction_id: str = Field(min_length=1, max_length=32)
    fingerprint: Fingerprint


class VerifyCardResponse(BaseModel):
    valid: bool
    reason: str
    disclaimer: str
