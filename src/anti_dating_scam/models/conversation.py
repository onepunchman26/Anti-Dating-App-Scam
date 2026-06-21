from datetime import datetime

from pydantic import BaseModel, Field

from anti_dating_scam.core.safety_policy import SAFETY_DISCLAIMER
from anti_dating_scam.models.risk import RiskLevel, RiskSignal


class ConversationSubmission(BaseModel):
    conversation_text: str = Field(min_length=1)
    user_notes: str | None = None
    consent_confirmed: bool = False


class JournalEntry(BaseModel):
    event_text: str = Field(min_length=1)
    occurred_at: datetime | None = None
    user_note: str | None = None


class JournalSummaryRequest(BaseModel):
    entries: list[JournalEntry] = Field(default_factory=list)
    consent_confirmed: bool = False


class JournalSummaryResponse(BaseModel):
    overall_risk_level: RiskLevel
    pattern_summary: list[str]
    recurring_risk_signals: list[RiskSignal]
    positive_trust_indicators: list[str]
    uncertainty: list[str]
    recommended_next_steps: list[str]
    disclaimer: str = SAFETY_DISCLAIMER
