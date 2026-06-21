from anti_dating_scam.models.trust_ladder import (
    TrustLadderEvaluationRequest,
    TrustStage,
)
from anti_dating_scam.services.trust_ladder_engine import (
    TrustLadderEngine as ServiceTrustLadderEngine,
)

SAFETY_DISCLAIMER = (
    "This is a risk-support tool, not a legal, criminal, psychological, or medical judgment."
)


class TrustLadderEngine:
    def __init__(self) -> None:
        self._service = ServiceTrustLadderEngine()

    def evaluate(
        self,
        *,
        current_stage: str,
        recent_events: str = "",
        boundary_concerns: str = "",
        money_or_sensitive_requested: bool = False,
        identity_verified: bool = False,
        consent_confirmed: bool = True,
    ) -> dict:
        events = [line.strip() for line in recent_events.splitlines() if line.strip()]
        if boundary_concerns.strip():
            events.append(boundary_concerns.strip())
        if money_or_sensitive_requested:
            events.append(
                "Asked for money, private photos, bank details, or sensitive information."
            )
        if identity_verified:
            events.append("Identity was verified through safe, consent-based methods.")

        response = self._service.evaluate(
            TrustLadderEvaluationRequest(
                current_stage=TrustStage(current_stage),
                observed_events=events,
                consent_confirmed=consent_confirmed,
            )
        )
        return {
            "schema_version": "0.1",
            "current_stage": response.current_stage.value,
            "recommended_stage": response.recommended_stage.value,
            "recommended_actions": [action.value for action in response.recommended_actions],
            "rationale": response.rationale,
            "safety_checklist": response.safety_checklist,
            "safety_disclaimer": SAFETY_DISCLAIMER,
        }
