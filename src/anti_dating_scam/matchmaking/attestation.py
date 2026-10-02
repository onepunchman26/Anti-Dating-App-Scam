"""Compatibility-card attestation: tamper-evidence, not truth.

The server never sees card content. Clients submit only a **fingerprint**
(SHA-256 of the canonical card JSON, reusing `reports/canonical_json.py`), and the
server returns a signed attestation binding {pseudonym, fingerprint, version, time}.

P0 uses HMAC-SHA256 with a server-held secret: the server (and only the server) can
verify tokens, which is enough for the prototype because introductions are brokered
server-side anyway. P1 upgrades to Ed25519 so clients can verify attestations
offline (see docs/12 §6). The fingerprint check itself — sha256(card) == locked
fingerprint — is always verifiable offline by the receiving client.

Honest limit (ADR-008/ADR-012): an attestation proves the card content did not
change since it was attested. It cannot prove the content is true.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from anti_dating_scam.reports.canonical_json import document_hash

ATTESTATION_ALGORITHM = "HMAC-SHA256-MVP"

ATTESTATION_DISCLAIMER = (
    "An attestation records a submitted card fingerprint and its registration's "
    "attestation history. A matching fingerprint supports content consistency; "
    "it does not verify age, identity, truthfulness, completeness, or personal safety. "
    "Unsubmitted edits and other registrations are not visible in this history."
)


def card_fingerprint(card: dict[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the card (signature block excluded)."""
    return document_hash(card)


@dataclass(frozen=True)
class CardAttestation:
    pseudonym: str
    fingerprint: str
    version: int
    attested_at: str
    algorithm: str
    token: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AttestationService:
    """Signs and verifies card-fingerprint attestations with a server secret."""

    def __init__(self, secret: bytes | None = None) -> None:
        # Ephemeral by default: the prototype holds no state across restarts, so a
        # per-process secret is honest. Deployment (P2) must supply a stable secret
        # from the environment / key store — never from a file in the repo.
        self._secret = secret or secrets.token_bytes(32)

    def _message(self, pseudonym: str, fingerprint: str, version: int, attested_at: str) -> bytes:
        return f"{pseudonym}|{fingerprint}|{version}|{attested_at}".encode()

    def attest(self, pseudonym: str, fingerprint: str, version: int) -> CardAttestation:
        attested_at = datetime.now(UTC).isoformat()
        token = hmac.new(
            self._secret,
            self._message(pseudonym, fingerprint, version, attested_at),
            hashlib.sha256,
        ).hexdigest()
        return CardAttestation(
            pseudonym=pseudonym,
            fingerprint=fingerprint,
            version=version,
            attested_at=attested_at,
            algorithm=ATTESTATION_ALGORITHM,
            token=token,
        )

    def verify(self, attestation: CardAttestation) -> bool:
        expected = hmac.new(
            self._secret,
            self._message(
                attestation.pseudonym,
                attestation.fingerprint,
                attestation.version,
                attestation.attested_at,
            ),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, attestation.token)
