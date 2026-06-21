from typing import Any

from anti_dating_scam.reports.canonical_json import document_hash
from anti_dating_scam.reports.schema_validator import SchemaValidationError, validate_document
from anti_dating_scam.reports.signer import SIGNATURE_ALGORITHM

SIGNATURE_DISCLAIMER = (
    "A valid report signature only means the report file was not modified after "
    "signing and conforms to the project schema. It does not prove that the "
    "submitted conversation is authentic or that any real person committed wrongdoing."
)


def verify_report(
    report: dict[str, Any],
    *,
    known_signers: set[str] | None = None,
) -> dict[str, Any]:
    try:
        validate_document(report, "risk_report.schema.json")
    except SchemaValidationError as exc:
        return {
            "status": "invalid_schema",
            "details": str(exc),
            "disclaimer": SIGNATURE_DISCLAIMER,
        }

    signature = report.get("signature")
    if not signature:
        return {
            "status": "unsigned",
            "details": "Report has no signature block.",
            "disclaimer": SIGNATURE_DISCLAIMER,
        }

    expected_hash = signature.get("content_hash")
    actual_hash = document_hash(report)
    if expected_hash != actual_hash or signature.get("algorithm") != SIGNATURE_ALGORITHM:
        return {
            "status": "modified",
            "details": "Report content no longer matches the signature hash.",
            "disclaimer": SIGNATURE_DISCLAIMER,
        }

    signer_id = signature.get("signer_id", "")
    if known_signers is not None and signer_id not in known_signers:
        return {
            "status": "unknown_signer",
            "details": f"Signature hash is intact, but signer is not trusted: {signer_id}",
            "disclaimer": SIGNATURE_DISCLAIMER,
        }

    return {
        "status": "valid",
        "details": "Report schema and hash integrity checks passed.",
        "disclaimer": SIGNATURE_DISCLAIMER,
    }
