import pytest

from anti_dating_scam.engine.scam_risk_analyzer import ScamRiskAnalyzer
from anti_dating_scam.services.consent_manager import ConsentRequiredError


def test_engine_risk_analyzer_high_risk_money_request() -> None:
    result = ScamRiskAnalyzer().analyze(
        "I love you. Please send me money by wire transfer for my emergency.",
        consent_confirmed=True,
    )

    assert result["risk_level"] == "HIGH"
    assert any(signal["name"] == "money_or_payment_request" for signal in result["risk_signals"])


def test_engine_risk_analyzer_low_risk_normal_conversation() -> None:
    result = ScamRiskAnalyzer().analyze(
        "I enjoyed talking with you. No pressure if you want to keep chatting here slowly.",
        consent_confirmed=True,
    )

    assert result["risk_level"] == "LOW"
    assert result["risk_signals"] == []


def test_engine_risk_analyzer_rejects_without_consent() -> None:
    with pytest.raises(ConsentRequiredError):
        ScamRiskAnalyzer().analyze("Please analyze this.", consent_confirmed=False)
