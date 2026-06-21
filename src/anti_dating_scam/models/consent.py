from enum import StrEnum

from pydantic import BaseModel, Field


class ConsentScope(StrEnum):
    LOCAL_ANALYSIS = "LOCAL_ANALYSIS"
    JOURNAL_SUMMARY = "JOURNAL_SUMMARY"
    TRUST_LADDER_EVALUATION = "TRUST_LADDER_EVALUATION"


class ConsentRecord(BaseModel):
    consent_confirmed: bool = Field(
        description="User confirms they are submitting text they are allowed to analyze."
    )
    scope: ConsentScope
    user_owns_submitted_text: bool = True
    no_hidden_scraping: bool = True
    no_public_scoring: bool = True
