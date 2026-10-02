"""Serverless matching beacons — rendezvous over existing social platforms.

A beacon is a small, armored text block a user can post *manually* on any
platform where their community already lives (a Facebook group, a 小红书 post, a
Discord channel, a forum thread). Another user copies the beacon text into their
app, which parses it locally and checks mutual Tier-1 gates + coarse location.
Contact then happens through the platform itself (DM), and cards are exchanged
peer-to-peer as usual (docs/11).

Design constraints (docs/14, ADR-013):

- **No scraping, ever.** Humans post and copy beacons by hand; the app never
  fetches platform content. This keeps the project's no-scraping rule and
  platform ToS intact.
- **Minimal trust in any server** — there is none in this mode. Authenticity is
  anchored in the *platform account* that posted the beacon (the platform is the
  witness and provides the public timestamp); integrity of the pasted text is
  guarded by a checksum; and the anti-tamper lock still happens peer-side: each
  app pins the counterpart's ``card_fingerprint`` from the beacon at first
  contact, exactly like the rendezvous server locks fingerprints at
  introduction time.
- **Honest limits:** a checksum detects corruption and casual editing, not a
  determined forger — real signatures (user keypairs, P1 `cryptography` extra)
  are the upgrade path. A beacon proves nothing about truthfulness.
"""

from __future__ import annotations

import base64
import binascii
import json
import textwrap
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from anti_dating_scam.matchmaking.geo import DEFAULT_PRECISION, is_valid_geohash
from anti_dating_scam.matchmaking.validation import clean_text, validate_ages, validate_fingerprint
from anti_dating_scam.reports.canonical_json import canonical_json, sha256_text

BEACON_VERSION = 1
MAX_BEACON_TEXT = 8192
MAX_BEACON_PAYLOAD = 4096
_BEGIN = "-----BEGIN AI-SLOWMATCH BEACON-----"
_END = "-----END AI-SLOWMATCH BEACON-----"


class BeaconError(ValueError):
    """Raised when a pasted beacon cannot be parsed or fails its checksum."""


@dataclass(frozen=True)
class Beacon:
    version: int
    pseudonym: str
    bucket: str  # coarse geohash prefix, client-derived (never raw coordinates)
    card_fingerprint: str
    created_at: str
    age: int
    seeking_age_min: int | None = None
    seeking_age_max: int | None = None
    contact_hint: str = ""  # e.g. "DM me on this platform" — never an address

    def __post_init__(self) -> None:
        try:
            validate_ages(self.age, self.seeking_age_min, self.seeking_age_max)
            if type(self.version) is not int or self.version != BEACON_VERSION:
                raise ValueError("Unsupported beacon version.")
            pseudonym = clean_text(self.pseudonym, "pseudonym", 40)
            if not pseudonym:
                raise ValueError("A pseudonym is required (never a real name).")
            object.__setattr__(self, "pseudonym", pseudonym)
            object.__setattr__(
                self, "contact_hint", clean_text(self.contact_hint, "contact_hint", 120)
            )
            object.__setattr__(
                self, "card_fingerprint", validate_fingerprint(self.card_fingerprint)
            )
            if not is_valid_geohash(self.bucket) or len(self.bucket) != DEFAULT_PRECISION:
                raise ValueError("Beacon location must be exactly 4 coarse geohash characters.")
            if not isinstance(self.created_at, str) or len(self.created_at) > 40:
                raise ValueError("Beacon creation time must be an ISO timestamp with timezone.")
            created = datetime.fromisoformat(self.created_at)
            if created.tzinfo is None:
                raise ValueError("Beacon creation time must include a timezone.")
        except (ValueError, TypeError) as exc:
            raise BeaconError(str(exc)) from exc

    def to_payload(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value not in (None, "")}


def _checksum(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "checksum"}
    return sha256_text(canonical_json(unsigned))


def create_beacon(
    *,
    pseudonym: str,
    bucket: str,
    card_fingerprint: str,
    age: int | None = None,
    seeking_age_min: int | None = None,
    seeking_age_max: int | None = None,
    contact_hint: str = "",
    consent_confirmed: bool = False,
) -> str:
    """Build the armored beacon text for manual posting."""
    if consent_confirmed is not True:
        raise BeaconError("Explicit consent is required before publishing beacon fields.")
    beacon = Beacon(
        version=BEACON_VERSION,
        pseudonym=pseudonym,
        bucket=bucket,
        card_fingerprint=card_fingerprint,
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        age=age,
        seeking_age_min=seeking_age_min,
        seeking_age_max=seeking_age_max,
        contact_hint=contact_hint,
    )
    payload = beacon.to_payload()
    payload["checksum"] = _checksum(payload)
    encoded = base64.b64encode(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).decode("ascii")
    body = "\n".join(textwrap.wrap(encoded, width=64))
    return f"{_BEGIN}\n{body}\n{_END}"


def parse_beacon(text: str) -> Beacon:
    """Parse + integrity-check a pasted beacon; raise ``BeaconError`` if invalid."""
    if not isinstance(text, str) or len(text) > MAX_BEACON_TEXT:
        raise BeaconError("Beacon text exceeds the allowed size.")
    start = text.find(_BEGIN)
    end = text.find(_END)
    if start == -1 or end == -1 or end <= start or text.count(_BEGIN) != 1 or text.count(_END) != 1:
        raise BeaconError("Paste exactly one complete BEGIN...END beacon block.")
    body = "".join(text[start + len(_BEGIN) : end].split())
    try:
        decoded = base64.b64decode(body, validate=True)
        if len(decoded) > MAX_BEACON_PAYLOAD:
            raise BeaconError("Beacon payload exceeds the allowed size.")
        payload = json.loads(decoded.decode("utf-8"), object_pairs_hook=_unique_object)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise BeaconError("Beacon text is corrupted (could not decode).") from exc
    if not isinstance(payload, dict):
        raise BeaconError("Beacon payload must be an object.")
    if set(payload) - (set(Beacon.__dataclass_fields__) | {"checksum"}):
        raise BeaconError("Beacon contains unsupported fields.")
    checksum = payload.get("checksum")
    try:
        validate_fingerprint(checksum)
    except ValueError as exc:
        raise BeaconError("Beacon checksum must be a SHA-256 hex digest.") from exc
    if _checksum(payload) != checksum:
        raise BeaconError("Beacon failed its integrity check; verify the original pasted text.")
    known = {field: payload[field] for field in Beacon.__dataclass_fields__ if field in payload}
    try:
        return Beacon(**known)
    except TypeError as exc:
        raise BeaconError("Beacon is missing required fields, including adult age.") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BeaconError("Beacon contains duplicate fields.")
        result[key] = value
    return result


def _age_gate_ok(seeker: Beacon, candidate: Beacon) -> bool:
    if type(candidate.age) is not int or not 18 <= candidate.age <= 120:
        return False
    if seeker.seeking_age_min is not None and candidate.age < seeker.seeking_age_min:
        return False
    if seeker.seeking_age_max is not None and candidate.age > seeker.seeking_age_max:
        return False
    return True


def mutual_match(mine: Beacon, theirs: Beacon) -> tuple[bool, list[str]]:
    """Local mutual check: same coarse bucket + both Tier-1 age gates pass.

    Returns ``(matched, reasons)`` where reasons explain each check plainly —
    facts, never a score (ADR-009 applies here too).
    """
    reasons: list[str] = []
    matched = True
    precision = min(len(mine.bucket), len(theirs.bucket))
    if precision == 0 or mine.bucket[:precision] != theirs.bucket[:precision]:
        matched = False
        reasons.append("different coarse location buckets")
    else:
        reasons.append(f"same coarse area (bucket '{theirs.bucket[:precision]}')")
    if _age_gate_ok(mine, theirs):
        reasons.append("their profile fits your basic filters")
    else:
        matched = False
        reasons.append("their profile does not fit your basic filters")
    if _age_gate_ok(theirs, mine):
        reasons.append("your profile fits their basic filters")
    else:
        matched = False
        reasons.append("your profile does not fit their basic filters")
    return matched, reasons
