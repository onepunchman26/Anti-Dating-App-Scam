from anti_dating_scam.models.risk import RiskAnalysisRequest
from anti_dating_scam.services.scam_risk_analyzer import ScamRiskAnalyzer as ServiceRiskAnalyzer

SAFETY_DISCLAIMER = (
    "This is a risk-support tool, not a legal, criminal, psychological, or medical judgment."
)


class ScamRiskAnalyzer:
    def __init__(self) -> None:
        self._service = ServiceRiskAnalyzer()

    def analyze(
        self,
        conversation_text: str,
        *,
        user_notes: str | None = None,
        consent_confirmed: bool = True,
    ) -> dict:
        response = self._service.analyze(
            RiskAnalysisRequest(
                conversation_text=conversation_text,
                user_notes=user_notes,
                consent_confirmed=consent_confirmed,
            )
        )
        return {
            "risk_level": response.risk_level.value,
            "risk_signals": [
                {
                    "name": signal.name,
                    "severity": signal.severity.value,
                    "evidence": signal.evidence,
                    "explanation": signal.explanation,
                }
                for signal in response.risk_signals
            ],
            "uncertainty_notes": response.uncertainty,
            "recommended_next_steps": response.recommended_next_steps,
            "safety_disclaimer": SAFETY_DISCLAIMER,
        }
