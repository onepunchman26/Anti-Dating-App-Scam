from anti_dating_scam.core.safety_policy import SafetyPolicy
from anti_dating_scam.models.risk import RiskLevel
from anti_dating_scam.models.trust_ladder import (
    LadderAction,
    TrustLadderEvaluationRequest,
    TrustLadderEvaluationResponse,
    TrustStage,
)
from anti_dating_scam.services.consent_manager import ConsentManager


class TrustLadderEngine:
    def __init__(
        self,
        consent_manager: ConsentManager | None = None,
        safety_policy: SafetyPolicy | None = None,
    ) -> None:
        self.consent_manager = consent_manager or ConsentManager()
        self.safety_policy = safety_policy or SafetyPolicy()

    def evaluate(self, request: TrustLadderEvaluationRequest) -> TrustLadderEvaluationResponse:
        self.consent_manager.ensure_confirmed(request.consent_confirmed)
        event_text = "\n".join(request.observed_events)
        self.safety_policy.ensure_allowed(event_text)

        lowered_events = [event.lower() for event in request.observed_events]

        if request.risk_level == RiskLevel.HIGH or self._has_high_risk_event(lowered_events):
            return TrustLadderEvaluationResponse(
                current_stage=request.current_stage,
                recommended_stage=TrustStage.UNKNOWN_STRANGER,
                recommended_actions=[
                    LadderAction.STOP_INTERACTION,
                    LadderAction.STEP_BACK,
                    LadderAction.GATHER_MORE_INFORMATION,
                ],
                rationale=[
                    "High-risk signals should override trust progression.",
                    (
                        "The system should not encourage intimacy, commitment, or offline "
                        "escalation in this state."
                    ),
                ],
            )

        if self._has_boundary_or_pressure_event(lowered_events):
            return TrustLadderEvaluationResponse(
                current_stage=request.current_stage,
                recommended_stage=request.current_stage,
                recommended_actions=[
                    LadderAction.SLOW_DOWN,
                    LadderAction.GATHER_MORE_INFORMATION,
                    LadderAction.STAY_AT_CURRENT_STAGE,
                ],
                rationale=[
                    "Boundary pressure or verification avoidance means trust should not escalate.",
                    (
                        "Consider whether the pattern repeats over time before moving to "
                        "a higher stage."
                    ),
                ],
            )

        if request.current_stage == TrustStage.SAFETY_CHECKED_OFFLINE_MEETING:
            return TrustLadderEvaluationResponse(
                current_stage=request.current_stage,
                recommended_stage=request.current_stage,
                recommended_actions=[
                    LadderAction.USE_SAFETY_CHECKLIST,
                    LadderAction.STAY_AT_CURRENT_STAGE,
                ],
                rationale=[
                    "Offline meeting planning requires a safety checklist and outside awareness."
                ],
                safety_checklist=self.offline_meeting_safety_checklist(),
            )

        return TrustLadderEvaluationResponse(
            current_stage=request.current_stage,
            recommended_stage=request.current_stage,
            recommended_actions=[LadderAction.STAY_AT_CURRENT_STAGE],
            rationale=[
                "No major escalation is recommended from this single evaluation.",
                "Trust should grow through repeated, normal, boundary-respecting interaction.",
            ],
        )

    def _has_high_risk_event(self, events: list[str]) -> bool:
        high_risk_terms = (
            "asked for money",
            "gift card",
            "crypto",
            "investment",
            "bank details",
            "private photos",
            "passport",
            "ssn",
        )
        return any(any(term in event for term in high_risk_terms) for event in events)

    def _has_boundary_or_pressure_event(self, events: list[str]) -> bool:
        pressure_terms = (
            "ignored my boundary",
            "boundary violation",
            "refused video call",
            "love-bombing",
            "wanted to move to whatsapp immediately",
            "kept asking",
            "pressured me",
            "inconsistent story",
        )
        return any(any(term in event for term in pressure_terms) for event in events)

    def offline_meeting_safety_checklist(self) -> list[str]:
        return [
            "Meet in a public place.",
            "Tell a trusted person where you are going.",
            "Use independent transportation.",
            "Do not share financial or identity documents.",
            "Leave if boundaries are pressured or ignored.",
        ]
