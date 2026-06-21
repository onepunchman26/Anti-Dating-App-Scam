from copy import deepcopy

from anti_dating_scam.engine.report_generator import ReportGenerator
from anti_dating_scam.engine.scam_risk_analyzer import ScamRiskAnalyzer
from anti_dating_scam.reports.schema_validator import validate_document
from anti_dating_scam.reports.signer import sign_report
from anti_dating_scam.reports.verifier import verify_report


def test_report_json_validates() -> None:
    conversation = "I enjoyed talking with you. No pressure to meet quickly."
    analysis = ScamRiskAnalyzer().analyze(conversation, consent_confirmed=True)
    report = ReportGenerator().generate_risk_report(
        conversation_text=conversation,
        risk_analysis=analysis,
    )

    validate_document(report, "risk_report.schema.json")
    assert report["report_type"] == "risk_report"


def test_modified_report_fails_integrity_verification() -> None:
    conversation = "Please send gift cards for my emergency."
    analysis = ScamRiskAnalyzer().analyze(conversation, consent_confirmed=True)
    report = ReportGenerator().generate_risk_report(
        conversation_text=conversation,
        risk_analysis=analysis,
    )
    signed = sign_report(report)
    modified = deepcopy(signed)
    modified["risk_level"] = "LOW"

    result = verify_report(modified, known_signers={"local_hash_mvp"})

    assert result["status"] == "modified"
