"""Rendezvous service: nearby discovery + double-blind introductions.

P0 prototype of docs/12 (ADR-012): in-memory store, no persistence, no network
side effects. FastAPI routes wrap this service thinly (ADR-010). Hard rules
enforced here, not in the UI:

- The server holds no card/profile content — only fingerprints (attestation.py).
- ``nearby`` requires the requester to have an attested card, returns candidates in
  the same coarse bucket passing the *mutual* Tier-1 age and gender gates, ordered
  by registration time only — never by any score (ADR-009). Declined pairs and
  pairs with a live introduction are excluded (no guaranteed-error buttons).
- Contact channels are revealed only in a match packet after **both** sides accept.
- A declined pair cannot be re-introduced (harassment mitigation; block/report is P2).
- The initiator "declining" their own pending introduction is a *withdrawal*: the
  introduction is removed without poisoning the pair.
- ``register`` issues a per-registration access token; the API layer requires it for
  every later call (P0 stand-in for real auth — see routes_matchmaking).
- ``unregister`` deletes registration, attestation history, open introductions, and
  declined-pair records naming the pseudonym (docs/06 deletion rule applied
  server-side; the decline block is not worth keeping data about deleted users).
"""

from __future__ import annotations

import secrets
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import wraps
from threading import RLock
from typing import Any

from anti_dating_scam.matchmaking.attestation import (
    ATTESTATION_DISCLAIMER,
    AttestationService,
    CardAttestation,
    card_fingerprint,
)
from anti_dating_scam.matchmaking.geo import DEFAULT_PRECISION, is_valid_geohash, same_bucket
from anti_dating_scam.matchmaking.validation import (
    clean_text,
    validate_ages,
    validate_fingerprint,
)
from anti_dating_scam.services.consent_manager import ConsentManager, ConsentRequiredError

# Privacy bound (docs/12 threat model "location stalking"): precision 4 is the
# default bucket; anything past 6 is coordinate-grade and must never be stored.
MAX_GEOHASH_PRECISION = 6
MAX_REGISTRATIONS = 1000
MAX_ATTESTATIONS = 100
MAX_INTRODUCTIONS_PER_PERSON = 100

MATCH_DISCLAIMER = (
    "A match means only: same coarse area, mutual basic filters, and both sides "
    "chose to connect. Compatibility itself is compared locally on your own device. "
    + ATTESTATION_DISCLAIMER
)

# Tier-1 gender vocabulary (docs/11 Tier-1 basics). "Seeking" is a set of these
# values; an empty/absent set means "everyone". Orientation is expressed only as
# gender + seeking — the server never stores an orientation label.
KNOWN_GENDERS = ("woman", "man", "nonbinary")


class MatchmakingError(ValueError):
    """Domain error; API routes translate this to a 400 response."""


@dataclass
class Registration:
    pseudonym: str
    geohash: str
    contact: str
    age: int
    seeking_age_min: int | None
    seeking_age_max: int | None
    gender: str | None
    seeking_genders: tuple[str, ...] | None
    created_at: str
    token: str = ""  # per-registration access secret; never listed to other users
    attestations: list[CardAttestation] = field(default_factory=list)


@dataclass
class Introduction:
    introduction_id: str
    initiator: str
    recipient: str
    locked_fingerprints: dict[str, str]
    accepted_by: set[str]
    status: str  # "pending" | "matched" | "declined"
    created_at: str


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _age_gate_ok(seeker: Registration, candidate: Registration) -> bool:
    """One-directional Tier-1 age gate: candidate satisfies seeker's range."""
    if type(candidate.age) is not int or not 18 <= candidate.age <= 120:
        return False
    if seeker.seeking_age_min is not None and candidate.age < seeker.seeking_age_min:
        return False
    if seeker.seeking_age_max is not None and candidate.age > seeker.seeking_age_max:
        return False
    return True


def _gender_gate_ok(seeker: Registration, candidate: Registration) -> bool:
    """One-directional Tier-1 gender gate: candidate satisfies seeker's seeking set.

    Mirrors the age-gate semantics: no seeking set means "everyone"; a candidate
    who did not state a gender only passes seekers with no gender filter.
    """
    if not seeker.seeking_genders:
        return True
    if candidate.gender is None:
        return False
    return candidate.gender in seeker.seeking_genders


def _normalize_gender(gender: str | None) -> str | None:
    if gender is None:
        return None
    if not isinstance(gender, str):
        raise MatchmakingError("gender must be text or omitted.")
    value = gender.strip().lower()
    if not value:
        return None
    if value not in KNOWN_GENDERS:
        raise MatchmakingError(f"gender must be one of {', '.join(KNOWN_GENDERS)} (or omitted).")
    return value


def _require_clean_text(value: str, label: str, max_length: int) -> str:
    try:
        return clean_text(value, label, max_length)
    except ValueError as exc:
        raise MatchmakingError(str(exc)) from exc


def _validate_ages(
    age: int | None, seeking_age_min: int | None, seeking_age_max: int | None
) -> None:
    try:
        validate_ages(age, seeking_age_min, seeking_age_max)
    except ValueError as exc:
        raise MatchmakingError(str(exc)) from exc


def _normalize_seeking(
    seeking_genders: list[str] | tuple[str, ...] | None,
) -> tuple[str, ...] | None:
    if seeking_genders is None:
        return None
    if not isinstance(seeking_genders, (list, tuple)) or len(seeking_genders) > 3:
        raise MatchmakingError("seeking_genders must be a list of at most 3 entries.")
    if not seeking_genders:
        return None
    normalized: list[str] = []
    for entry in seeking_genders:
        if not isinstance(entry, str):
            raise MatchmakingError("seeking_genders entries must be text.")
        value = entry.strip().lower()
        if value not in KNOWN_GENDERS:
            raise MatchmakingError(
                f"seeking_genders entries must be one of {', '.join(KNOWN_GENDERS)}."
            )
        if value not in normalized:
            normalized.append(value)
    # Seeking every known gender is the same as no filter.
    if set(normalized) == set(KNOWN_GENDERS):
        return None
    return tuple(normalized)


def _synchronized(method):
    """Keep consent transitions and capacity checks atomic across API workers."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapped


class RendezvousService:
    def __init__(self, attestation_service: AttestationService | None = None) -> None:
        self._lock = RLock()
        self._attestations = attestation_service or AttestationService()
        self._registry: dict[str, Registration] = {}
        self._introductions: dict[str, Introduction] = {}
        self._declined_pairs: set[frozenset[str]] = set()
        self._consent = ConsentManager()

    # ---------------------------------------------------------------- registry
    @_synchronized
    def register(
        self,
        *,
        pseudonym: str,
        geohash: str,
        contact: str,
        consent_confirmed: bool,
        age: int | None = None,
        seeking_age_min: int | None = None,
        seeking_age_max: int | None = None,
        gender: str | None = None,
        seeking_genders: list[str] | tuple[str, ...] | None = None,
    ) -> Registration:
        if consent_confirmed is not True:
            raise ConsentRequiredError("Explicit consent is required for matchmaking disclosure.")
        self._consent.ensure_confirmed(consent_confirmed)
        if len(self._registry) >= MAX_REGISTRATIONS:
            raise MatchmakingError("This experimental node has reached its registration limit.")
        pseudonym = _require_clean_text(pseudonym, "pseudonym", 40)
        if not pseudonym:
            raise MatchmakingError("A pseudonym is required (never a real name).")
        if pseudonym in {".", ".."} or any(char in pseudonym for char in "/\\?#%"):
            raise MatchmakingError("pseudonym must not contain URL path or query delimiters.")
        if pseudonym in self._registry:
            raise MatchmakingError("This pseudonym is already registered.")
        if not is_valid_geohash(geohash):
            raise MatchmakingError(
                "geohash must be a client-derived geohash string; raw coordinates "
                "are never accepted."
            )
        if not DEFAULT_PRECISION <= len(geohash) <= MAX_GEOHASH_PRECISION:
            raise MatchmakingError(
                f"geohash must be {DEFAULT_PRECISION}-{MAX_GEOHASH_PRECISION} characters: "
                f"shorter can never match a bucket, longer is coordinate-grade location "
                f"and is never stored."
            )
        contact = _require_clean_text(contact, "contact", 120)
        if not contact:
            raise MatchmakingError("A contact channel is required (revealed only on match).")
        _validate_ages(age, seeking_age_min, seeking_age_max)
        registration = Registration(
            pseudonym=pseudonym,
            geohash=geohash,
            contact=contact,
            age=age,
            seeking_age_min=seeking_age_min,
            seeking_age_max=seeking_age_max,
            gender=_normalize_gender(gender),
            seeking_genders=_normalize_seeking(seeking_genders),
            created_at=_now(),
            token=secrets.token_urlsafe(24),
        )
        self._registry[pseudonym] = registration
        return registration

    @_synchronized
    def unregister(self, pseudonym: str) -> None:
        self._require_registered(pseudonym)
        del self._registry[pseudonym]
        stale = [
            intro_id
            for intro_id, intro in list(self._introductions.items())
            if pseudonym in (intro.initiator, intro.recipient)
        ]
        for intro_id in stale:
            del self._introductions[intro_id]
        # docs/06 deletion rule: no server state may keep naming a deleted pseudonym,
        # including decline records (harassment mitigation loses to the deletion right).
        self._declined_pairs = {
            pair for pair in self._declined_pairs if pseudonym not in pair
        }

    def _require_registered(self, pseudonym: str) -> Registration:
        registration = self._registry.get(pseudonym)
        if registration is None:
            raise MatchmakingError("Unknown pseudonym; register first.")
        return registration

    @_synchronized
    def authenticate(self, pseudonym: str, token: str) -> Registration:
        """Check the per-registration access token (P0 stand-in for real auth).

        The API layer calls this before every non-register operation so that
        inboxes, match packets (contact channels!), and deletions cannot be
        read or triggered by a caller merely *claiming* a pseudonym.
        """
        registration = self._require_registered(pseudonym)
        if (not isinstance(token, str) or not token.isascii() or len(token) > 128
                or not token or not secrets.compare_digest(registration.token, token)):
            raise MatchmakingError(
                "Invalid or missing access token for this pseudonym. The token is "
                "issued once at registration; if you lost it, the registration "
                "cannot be reused until the node operator resets state (P0 limit)."
            )
        return registration

    @contextmanager
    def authenticated_operation(self, pseudonym: str, token: str):
        """Hold identity stable between the API's token check and its operation.

        Otherwise a concurrent deletion/re-registration could transfer an already
        authenticated request to a different registration using the same pseudonym.
        """
        with self._lock:
            self.authenticate(pseudonym, token)
            yield

    # ------------------------------------------------------------- attestation
    @_synchronized
    def attest_card(
        self,
        pseudonym: str,
        card: dict[str, Any] | None = None,
        *,
        fingerprint: str | None = None,
    ) -> CardAttestation:
        """Attest a card fingerprint.

        HTTP clients must hash locally and submit only ``fingerprint``. The card
        argument supports UI-independent local callers; it is never accepted by
        the public HTTP protocol.
        """
        registration = self._require_registered(pseudonym)
        if len(registration.attestations) >= MAX_ATTESTATIONS:
            raise MatchmakingError("This registration has reached its attestation limit.")
        if (card is None) == (fingerprint is None):
            raise MatchmakingError("Provide exactly one of card or fingerprint.")
        if fingerprint is not None:
            try:
                fingerprint = validate_fingerprint(fingerprint)
            except ValueError as exc:
                raise MatchmakingError(str(exc)) from exc
        else:
            assert card is not None
            fingerprint = card_fingerprint(card)
        attestation = self._attestations.attest(
            pseudonym, fingerprint, version=len(registration.attestations) + 1
        )
        registration.attestations.append(attestation)
        return attestation

    def _attestation_summary(self, registration: Registration) -> dict[str, Any]:
        """Plain facts about a card's history — never folded into any score."""
        history = registration.attestations
        return {
            "version_count": len(history),
            "first_attested_at": history[0].attested_at if history else None,
            "last_attested_at": history[-1].attested_at if history else None,
        }

    # --------------------------------------------------------------- discovery
    @_synchronized
    def nearby(self, pseudonym: str, precision: int = DEFAULT_PRECISION) -> list[dict[str, Any]]:
        if type(precision) is not int or not 3 <= precision <= 6:
            raise MatchmakingError("precision must be between 3 and 6.")
        seeker = self._require_registered(pseudonym)
        if not seeker.attestations:
            raise MatchmakingError(
                "Attest your own compatibility card before browsing nearby users."
            )
        candidates = []
        # list(): snapshot against concurrent registration (sync routes run on a
        # threadpool; iterating the live dict can raise RuntimeError mid-request).
        for other in list(self._registry.values()):
            if other.pseudonym == pseudonym or not other.attestations:
                continue
            if not same_bucket(seeker.geohash, other.geohash, precision):
                continue
            if not (_age_gate_ok(seeker, other) and _age_gate_ok(other, seeker)):
                continue
            if not (_gender_gate_ok(seeker, other) and _gender_gate_ok(other, seeker)):
                continue
            pair = frozenset((pseudonym, other.pseudonym))
            if pair in self._declined_pairs:
                continue  # a declined pair would only render a guaranteed-error button
            if self._live_introduction(pair) is not None:
                continue  # already pending/matched — it lives in the inbox, not here
            candidates.append(other)
        candidates.sort(key=lambda registration: registration.created_at)
        return [
            {
                "pseudonym": other.pseudonym,
                "bucket": other.geohash[:precision],
                "attestation_summary": self._attestation_summary(other),
            }
            for other in candidates
        ]

    # ----------------------------------------------------------- introductions
    def _live_introduction(self, pair: frozenset[str]) -> Introduction | None:
        """The pair's pending or matched introduction, if one exists (snapshot scan)."""
        for intro in list(self._introductions.values()):
            if {intro.initiator, intro.recipient} == set(pair) and intro.status in (
                "pending",
                "matched",
            ):
                return intro
        return None

    @_synchronized
    def request_introduction(self, initiator: str, recipient: str) -> Introduction:
        first = self._require_registered(initiator)
        second = self._require_registered(recipient)
        if initiator == recipient:
            raise MatchmakingError("Cannot request an introduction to yourself.")
        if not first.attestations or not second.attestations:
            raise MatchmakingError("Both sides need an attested card before introductions.")
        if not (_age_gate_ok(first, second) and _age_gate_ok(second, first)
                and _gender_gate_ok(first, second) and _gender_gate_ok(second, first)):
            raise MatchmakingError("Both participants must satisfy each other's basic filters.")
        if not same_bucket(first.geohash, second.geohash, 3):
            raise MatchmakingError("Introductions require the same coarse search area.")
        for person in (initiator, recipient):
            if len(self.introductions_for(person)) >= MAX_INTRODUCTIONS_PER_PERSON:
                raise MatchmakingError("A participant has reached the introduction limit.")
        pair = frozenset((initiator, recipient))
        if pair in self._declined_pairs:
            raise MatchmakingError("This introduction was declined and cannot be re-requested.")
        live = self._live_introduction(pair)
        if live is not None:
            raise MatchmakingError(
                f"An introduction between this pair is already {live.status}."
            )
        introduction = Introduction(
            introduction_id=secrets.token_hex(8),
            initiator=initiator,
            recipient=recipient,
            locked_fingerprints={
                initiator: first.attestations[-1].fingerprint,
                recipient: second.attestations[-1].fingerprint,
            },
            accepted_by={initiator},
            status="pending",
            created_at=_now(),
        )
        self._introductions[introduction.introduction_id] = introduction
        return introduction

    def _require_introduction(self, introduction_id: str, pseudonym: str) -> Introduction:
        introduction = self._introductions.get(introduction_id)
        if introduction is None:
            raise MatchmakingError("Unknown introduction id.")
        if pseudonym not in (introduction.initiator, introduction.recipient):
            raise MatchmakingError("You are not part of this introduction.")
        return introduction

    @_synchronized
    def respond(self, pseudonym: str, introduction_id: str, accept: bool) -> Introduction:
        if type(accept) is not bool:
            raise MatchmakingError("accept must be an explicit boolean choice.")
        self._require_registered(pseudonym)
        introduction = self._require_introduction(introduction_id, pseudonym)
        if introduction.status != "pending":
            raise MatchmakingError(f"This introduction is already {introduction.status}.")
        if not accept:
            if pseudonym == introduction.initiator:
                # Withdrawal, not a decline: the initiator taking back their own
                # request must not poison the pair for a future genuine attempt.
                introduction.status = "withdrawn"
                del self._introductions[introduction.introduction_id]
                return introduction
            introduction.status = "declined"
            self._declined_pairs.add(frozenset((introduction.initiator, introduction.recipient)))
            return introduction
        introduction.accepted_by.add(pseudonym)
        if introduction.accepted_by == {introduction.initiator, introduction.recipient}:
            introduction.status = "matched"
        return introduction

    @_synchronized
    def introductions_for(self, pseudonym: str) -> list[dict[str, Any]]:
        """The caller's own introduction inbox (both directions).

        Without this a recipient can never learn a pending introduction exists —
        the double-blind flow could not complete outside of tests. Exposes only
        metadata the caller is already party to; contact stays in the match packet.
        """
        self._require_registered(pseudonym)
        entries = [
            {
                "introduction_id": intro.introduction_id,
                "counterpart_pseudonym": (
                    intro.recipient if pseudonym == intro.initiator else intro.initiator
                ),
                "direction": "sent" if pseudonym == intro.initiator else "received",
                "status": intro.status,
                "awaiting_you": (
                    intro.status == "pending" and pseudonym not in intro.accepted_by
                ),
                "created_at": intro.created_at,
            }
            for intro in list(self._introductions.values())
            if pseudonym in (intro.initiator, intro.recipient)
        ]
        entries.sort(key=lambda entry: entry["created_at"])
        return entries

    # ------------------------------------------------------------ match packet
    @_synchronized
    def match_packet(self, pseudonym: str, introduction_id: str) -> dict[str, Any]:
        """Contact + verification material, available only after a mutual accept."""
        self._require_registered(pseudonym)
        introduction = self._require_introduction(introduction_id, pseudonym)
        if introduction.status != "matched":
            raise MatchmakingError("Contact is revealed only after both sides accept.")
        other_name = (
            introduction.recipient
            if pseudonym == introduction.initiator
            else introduction.initiator
        )
        other = self._require_registered(other_name)
        return {
            "introduction_id": introduction.introduction_id,
            "counterpart_pseudonym": other_name,
            "counterpart_contact": other.contact,
            "locked_fingerprint": introduction.locked_fingerprints[other_name],
            "attestation_summary": self._attestation_summary(other),
            "how_to_verify": (
                "When their card arrives (by email/QR/file), recompute "
                "sha256(canonical_json(card)) and compare it to locked_fingerprint. "
                "A mismatch means the card changed after you matched."
            ),
            "disclaimer": MATCH_DISCLAIMER,
        }

    @_synchronized
    def verify_card_for_match(
        self, pseudonym: str, introduction_id: str, card: dict[str, Any] | None = None,
        *, fingerprint: str | None = None,
    ) -> dict[str, Any]:
        """Check a received card against the fingerprint locked at introduction time."""
        self._require_registered(pseudonym)
        introduction = self._require_introduction(introduction_id, pseudonym)
        if introduction.status != "matched":
            # No fingerprint oracle before a mutual accept; cards are only ever
            # exchanged (and thus verified) after both sides said yes.
            raise MatchmakingError("Cards can be verified only after both sides accept.")
        other_name = (
            introduction.recipient
            if pseudonym == introduction.initiator
            else introduction.initiator
        )
        locked = introduction.locked_fingerprints[other_name]
        if (card is None) == (fingerprint is None):
            raise MatchmakingError("Provide exactly one of card or fingerprint.")
        try:
            actual = validate_fingerprint(fingerprint) if fingerprint is not None else (
                card_fingerprint(card)
            )
        except ValueError as exc:
            raise MatchmakingError(str(exc)) from exc
        if actual == locked:
            return {
                "valid": True,
                "reason": "Card matches the fingerprint attested before your match.",
                "disclaimer": ATTESTATION_DISCLAIMER,
            }
        return {
            "valid": False,
            "reason": (
                "Card does NOT match the fingerprint locked for this introduction. "
                "It may be a different card, changed content, or incompatible canonicalization; "
                "this does not establish deception."
            ),
            "disclaimer": ATTESTATION_DISCLAIMER,
        }
