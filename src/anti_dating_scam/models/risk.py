from enum import StrEnum

from pydantic import BaseModel, Field

from anti_dating_scam.core.safety_policy import SAFETY_DISCLAIMER


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class SignalSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskSignal(BaseModel):
    name: str
    severity: SignalSeverity
    evidence: str
    explanation: str


class RiskAnalysisRequest(BaseModel):
    conversation_text: str = Field(min_length=1)
    user_notes: str | None = None
    event_log: list[str] = Field(default_factory=list)
    consent_confirmed: bool = False


class RiskAnalysisResponse(BaseModel):
    risk_level: RiskLevel
    risk_signals: list[RiskSignal]
    uncertainty: list[str]
    recommended_next_steps: list[str]
    do_not_conclude: list[str] = Field(default_factory=list)
    disclaimer: str = SAFETY_DISCLAIMER
