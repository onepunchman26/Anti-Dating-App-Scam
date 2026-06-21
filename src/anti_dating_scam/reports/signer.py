from datetime import UTC, datetime
from typing import Any

from anti_dating_scam.reports.canonical_json import document_hash, without_signature
from anti_dating_scam.reports.schema_validator import validate_document

SIGNATURE_ALGORITHM = "SHA256-CANONICAL-HASH-MVP"


def sign_report(report: dict[str, Any], signer_id: str = "local_hash_mvp") -> dict[str, Any]:
    """Attach a hash-based MVP signature block.

    This is an integrity MVP, not a cryptographic identity system. It proves whether
    canonical report content changed after signing.
    """

    unsigned_report = without_signature(report)
    validate_document(unsigned_report, "risk_report.schema.json")
    signed_report = dict(unsigned_report)
    signed_report["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "signed_at": datetime.now(UTC).isoformat(),
        "signer_id": signer_id,
        "content_hash": document_hash(unsigned_report),
    }
    validate_document(signed_report, "risk_report.schema.json")
    return signed_report
