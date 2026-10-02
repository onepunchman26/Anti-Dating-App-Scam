"""Strict local artifact contracts shared by browser and desktop orchestration.

Validation establishes structure, explicit evidence fields, and uncertainty fields.
It cannot establish factual truth, faithful quotations, consent, or semantic safety.
Nothing is read, saved, signed, exported, or sent by this module.
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

Text = Annotated[str, Field(min_length=1, max_length=8_000, pattern=r"\S")]
ShortText = Annotated[str, Field(min_length=1, max_length=1_000, pattern=r"\S")]
TextList = Annotated[list[Text], Field(max_length=50)]
Confidence = Literal["low", "medium", "high"]


class ArtifactValidationError(ValueError):
    """Artifact rejected without including the submitted content in the message."""


class ArtifactModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class BilingualText(ArtifactModel):
    en: Text
    zh: Text


class Evidence(ArtifactModel):
    quote: Text
    source: ShortText


EvidenceList = Annotated[list[Evidence], Field(min_length=1, max_length=20)]


class Claim(ArtifactModel):
    topic: Literal[
        "values", "wants", "communication", "boundaries", "market_stance", "presentation", "pattern"
    ]
    claim: Text
    evidence: EvidenceList
    type: Literal["observation", "inference", "speculation"]
    confidence: Confidence


class Coverage(ArtifactModel):
    sources_read: Annotated[list[ShortText], Field(max_length=100)]
    covered: TextList
    not_covered: TextList


class ConsistencyFinding(ArtifactModel):
    kind: Literal[
        "stated_vs_revealed", "front_vs_back", "internal_logic", "double_standard",
        "temporal_drift", "embellishment",
    ]
    stated: Text
    contradicting: Text
    quotes: Annotated[list[Evidence], Field(min_length=2, max_length=20)]
    confidence: Confidence
    framing: Text
    clarifying_question: Text
    alt_benign_explanation: Text


class SocialSelfPortrait(ArtifactModel):
    schema_version: Literal["0.2"]
    generated_at: ShortText | None = None  # caller replaces provider timestamps before saving
    data_coverage: Coverage
    claims: Annotated[list[Claim], Field(max_length=100)]
    consistency_findings: Annotated[list[ConsistencyFinding], Field(max_length=40)]
    open_questions: TextList
    caveats: Annotated[list[Text], Field(min_length=1, max_length=30)]


class SelfPortrait(SocialSelfPortrait):
    report_type: Literal["self_portrait"] = "self_portrait"
    headline: BilingualText | None = None
    summary: BilingualText | None = None


class MateCriteria(ArtifactModel):
    schema_version: Literal["0.1"]
    report_type: Literal["mate_criteria"] = "mate_criteria"
    stated: Annotated[list[Claim], Field(max_length=50)]
    revealed: Annotated[list[Claim], Field(max_length=50)]
    open_questions: TextList
    caveats: Annotated[list[Text], Field(min_length=1, max_length=30)]


class FictionalCandidate(ArtifactModel):
    synthetic_id: ShortText
    age: Annotated[int, Field(ge=18, le=120)]
    fictional: Literal[True]
    description: Text
    choice_reason: Text | None
    evidence: Annotated[list[Evidence], Field(max_length=20)]
    uncertainty_notes: Text

    @field_validator("fictional", mode="before")
    @classmethod
    def explicitly_fictional(cls, value):
        if value is not True:
            raise ValueError("Candidates must be explicitly fictional.")
        return value

    @model_validator(mode="after")
    def choice_needs_evidence(self):
        if self.choice_reason is not None and not self.evidence:
            raise ValueError("A reported user choice needs interview evidence.")
        return self


class IdealProfiles(ArtifactModel):
    schema_version: Literal["0.1"]
    candidates: Annotated[list[FictionalCandidate], Field(max_length=20)]
    caveats: Annotated[list[Text], Field(min_length=1, max_length=30)]


class PlanStage(ArtifactModel):
    name: ShortText
    goal: Text
    actions: Annotated[list[Text], Field(min_length=1, max_length=10)]
    example_lines: TextList
    cautions: Annotated[list[Text], Field(min_length=1, max_length=10)]
    ready_when: Text


class RelationshipPlan(ArtifactModel):
    stages: Annotated[list[PlanStage], Field(min_length=1, max_length=12)]
    uncertainty_notes: Text
    generated_at: ShortText | None = None


class SelfModel(ArtifactModel):
    values: Annotated[list[ShortText], Field(min_length=1, max_length=20)]
    life_goals: Text
    communication_style: Text
    boundaries: Text
    uncertainty_notes: Text
    evidence_notes: Text


class CompatibilityCard(ArtifactModel):
    schema_version: Literal["0.1"]
    tier2_summary: SelfModel
    source: Literal["self_model_from_ai_analysis_of_own_data"]


_MODELS: dict[str, type[ArtifactModel]] = {
    "social_self_portrait": SocialSelfPortrait,
    "self_portrait": SelfPortrait,
    "mate_criteria": MateCriteria,
    "ideal_profiles": IdealProfiles,
    "relationship_plan": RelationshipPlan,
    "self_model": SelfModel,
    "compatibility_card": CompatibilityCard,
}
MAX_ARTIFACT_BYTES = 512_000


def validate_local_artifact(payload: Any, expected_type: str) -> dict[str, Any]:
    """Reject malformed artifacts before any writes, fingerprinting, signing or export.

    Preserve supplied fields exactly rather than silently migrating old artifacts.
    Prior legacy files remain readable by existing viewers, but saving them under
    this contract requires explicit regeneration/correction of missing fields.
    """
    model = _MODELS.get(expected_type)
    if model is None:
        raise ArtifactValidationError("Unknown artifact contract.")
    try:
        serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        if len(serialized.encode("utf-8")) > MAX_ARTIFACT_BYTES:
            raise ArtifactValidationError("Artifact exceeds the allowed size.")
        checked = model.model_validate(payload)
    except (ValidationError, ValueError, TypeError, RecursionError, UnicodeError):
        # Do not format Pydantic errors: their representation embeds rejected user input.
        raise ArtifactValidationError(
            f"Invalid {expected_type} artifact. Required evidence, uncertainty, fields or types "
            "are missing or unsupported; review or regenerate before saving."
        ) from None
    return checked.model_dump(mode="json", exclude_unset=True)


def artifact_schema_prompt(expected_type: str) -> str:
    model = _MODELS.get(expected_type)
    if model is None:
        raise ArtifactValidationError("Unknown artifact contract.")
    return (
        "\nThe JSON companion must satisfy this strict schema. No extra fields, scores, "
        "rankings or diagnoses. Do not invent evidence or fabricate confidence. Use empty "
        "claim lists when evidence is absent, with explicit coverage gaps and caveats. "
        "Fictional candidates are adults only. JSON schema:\n"
        + json.dumps(model.model_json_schema(), ensure_ascii=False)
    )
