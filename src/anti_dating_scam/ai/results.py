"""Small provider-neutral receipts; never store prompts or raw provider errors."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider: str = Field(min_length=1, max_length=80)
    requested_model: str = Field(min_length=1, max_length=200)
    reported_model: str | None = Field(default=None, max_length=200)
    response_id: str | None = Field(default=None, max_length=200)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    completion: Literal["completed"] = "completed"

    @property
    def model_agreement(self) -> str:
        if self.reported_model is None:
            return "unreported"
        return "exact" if self.requested_model == self.reported_model else "different"


class ChatResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str = Field(min_length=1, max_length=256_000)
    provenance: AIProvenance
