from enum import StrEnum

from pydantic import BaseModel, Field

from anti_dating_scam.core.safety_policy import SAFETY_DISCLAIMER
from anti_dating_scam.models.risk import RiskLevel


class TrustStage(StrEnum):
    UNKNOWN_STRANGER = "UNKNOWN_STRANGER"
    LOW_PRESSURE_CHAT = "LOW_PRESSURE_CHAT"
    REPEATED_CONSISTENT_INTERACTION = "REPEATED_CONSISTENT_INTERACTION"
    BOUNDARY_RESPECT_VERIFIED = "BOUNDARY_RESPECT_VERIFIED"
    SAFETY_CHECKED_OFFLINE_MEETING = "SAFETY_CHECKED_OFFLINE_MEETING"
    DEEPER_RELATIONSHIP_EXPLORATION = "DEEPER_RELATIONSHIP_EXPLORATION"


class LadderAction(StrEnum):
    STAY_AT_CURRENT_STAGE = "stay_at_current_stage"
    SLOW_DOWN = "slow_down"
    STEP_BACK = "step_back"
    GATHER_MORE_INFORMATION = "gather_more_information"
    USE_SAFETY_CHECKLIST = "use_safety_checklist"
    STOP_INTERACTION = "stop_interaction"


class TrustLadderEvaluationRequest(BaseModel):
    current_stage: TrustStage = TrustStage.UNKNOWN_STRANGER
    observed_events: list[str] = Field(default_factory=list)
    risk_level: RiskLevel | None = None
    consent_confirmed: bool = False


class TrustLadderEvaluationResponse(BaseModel):
    current_stage: TrustStage
    recommended_stage: TrustStage
    recommended_actions: list[LadderAction]
    rationale: list[str]
    safety_checklist: list[str] = Field(default_factory=list)
    disclaimer: str = SAFETY_DISCLAIMER
