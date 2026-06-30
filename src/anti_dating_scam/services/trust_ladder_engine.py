from anti_dating_scam.core.safety_policy import SafetyPolicy
from anti_dating_scam.models.risk import RiskLevel
from anti_dating_scam.models.trust_ladder import (
    LadderAction,
    TrustLadderEvaluationRequest,
    TrustLadderEvaluationResponse,
    TrustStage,
)
from anti_dating_scam.services.consent_manager import ConsentManager
from anti_dating_scam.services.scam_risk_analyzer import RISK_RULES

# Rule names from RISK_RULES that should force trust back to UNKNOWN_STRANGER
# whenever they appear in free-text events, kept in sync with the same
# regex taxonomy the risk analyzer uses (instead of a separately maintained,
# narrower hardcoded substring list that can silently drift out of sync).
_HIGH_RISK_RULE_NAMES = frozenset(
    {
        "money_or_payment_request",
        "investment_or_pig_butchering_pattern",
        "private_images_or_sensitive_information_request",
    }
)

# Rule names that represent boundary pressure, verification avoidance, or
# manipulation tactics -- these should hold the trust stage steady (slow down)
# even when they don't independently trigger a HIGH risk level.
_BOUNDARY_PRESSURE_RULE_NAMES = frozenset(
    {
        "refusal_to_verify_or_meet",
        "repeated_boundary_violation",
        "isolation_pressure",
        "guilt_or_fear_pressure",
        "pressure_to_move_off_platform",
        "inconsistent_biography",
        "rapid_emotional_escalation",
        "emergency_story",
    }
)

_HIGH_RISK_PATTERNS = tuple(
    pattern
    for rule in RISK_RULES
    if rule.name in _HIGH_RISK_RULE_NAMES
    for pattern in rule.patterns
)
_BOUNDARY_PRESSURE_PATTERNS = tuple(
    pattern
    for rule in RISK_RULES
    if rule.name in _BOUNDARY_PRESSURE_RULE_NAMES
    for pattern in rule.patterns
)

# Legacy, more conversational phrasing used in earlier trust-ladder-only
# language (e.g. event summaries written by the engine.trust_ladder_engine
# facade) that may not exactly match the risk-analyzer regexes. Kept as a
# supplementary substring check so existing callers don't regress.
_LEGACY_HIGH_RISK_TERMS = (
    "asked for money",
    "gift card",
    "crypto",
    "investment",
    "bank details",
    "private photos",
    "passport",
    "ssn",
)
_LEGACY_PRESSURE_TERMS = (
    "ignored my boundary",
    "boundary violation",
    "refused video call",
    "love-bombing",
    "wanted to move to whatsapp immediately",
    "kept asking",
    "pressured me",
    "inconsistent story",
)


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

        if request.risk_level == RiskLevel.HIGH or self._has_high_risk_event(
            request.observed_events, lowered_events
        ):
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

        if self._has_boundary_or_pressure_event(request.observed_events, lowered_events):
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

    def _has_high_risk_event(self, raw_events: list[str], lowered_events: list[str]) -> bool:
        if any(pattern.search(event) for event in raw_events for pattern in _HIGH_RISK_PATTERNS):
            return True
        return any(
            any(term in event for term in _LEGACY_HIGH_RISK_TERMS) for event in lowered_events
        )

    def _has_boundary_or_pressure_event(
        self, raw_events: list[str], lowered_events: list[str]
    ) -> bool:
        if any(
            pattern.search(event) for event in raw_events for pattern in _BOUNDARY_PRESSURE_PATTERNS
        ):
            return True
        return any(
            any(term in event for term in _LEGACY_PRESSURE_TERMS) for event in lowered_events
        )

    def offline_meeting_safety_checklist(self) -> list[str]:
        return [
            "Meet in a public place.",
            "Tell a trusted person where you are going.",
            "Use independent transportation.",
            "Do not share financial or identity documents.",
            "Leave if boundaries are pressured or ignored.",
        ]
