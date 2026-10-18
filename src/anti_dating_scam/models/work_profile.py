"""Contracts for native ChatGPT work and its separate, minimal Sites boundary.

Private models never subclass the publishable model. Text in private/peer artifacts
is data, not a tool instruction. No personal answers are provided as defaults.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Text = Annotated[str, Field(min_length=1, max_length=2000, pattern=r"\S")]
ShortText = Annotated[str, Field(min_length=1, max_length=300, pattern=r"\S")]
Topic = Literal[
    "values",
    "life_direction",
    "relationship_goal",
    "partner_needs",
    "communication",
    "boundaries",
    "lifestyle",
    "action_plan",
    "open_question",
]
AgeBand = Literal["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
Goal = Literal["long_term", "companionship", "exploring"]
ValueToken = Literal[
    "honesty",
    "kindness",
    "autonomy",
    "curiosity",
    "family",
    "community",
    "growth",
    "stability",
    "creativity",
    "adventure",
]
DirectionToken = Literal[
    "build_family",
    "childfree",
    "career_focus",
    "community_life",
    "creative_life",
    "travel",
    "settled_life",
    "still_exploring",
]
CommunicationToken = Literal[
    "direct",
    "reflective",
    "frequent_checkins",
    "space_between_chats",
    "discuss_conflict_calmly",
    "gradual_disclosure",
]
InterestToken = Literal[
    "reading",
    "music",
    "art",
    "outdoors",
    "cooking",
    "games",
    "travel",
    "sport",
    "learning",
    "volunteering",
]
PreferenceToken = ValueToken | DirectionToken | CommunicationToken | InterestToken
PUBLIC_LABEL_PATTERN = (
    r"^[A-Za-z\u00C0-\u024F\u3400-\u9FFF][A-Za-z\u00C0-\u024F\u3400-\u9FFF '\u2019.,-]*$"
)
PRIVATE_LABEL_TERMS = (
    r"https?|www\.|private|secret|token|password|ignore|upload|system|"
    r"instruction|prompt|trauma|diagnos|therapy|sexual|abuse|"
    r"隐私|私密|密码|令牌|忽略|上传|指令|创伤|诊断|治疗|性生活|住址"
)


class WorkModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ApprovedRequest(WorkModel):
    confirmed: Literal[True]

    @field_validator("confirmed", mode="before")
    @classmethod
    def exact_approval(cls, value):
        if value is not True:
            raise ValueError("approval_required")
        return value


class SourceReference(WorkModel):
    source_type: Literal["self_report", "observed_fact", "model_inference", "unknown"]
    reference: ShortText
    quote: str = Field(default="", max_length=2000)
    legacy_kind: (
        Literal[
            "preference",
            "self_report",
            "interpretation",
            "event",
            "goal",
            "boundary",
            "pattern",
            "open_question",
        ]
        | None
    ) = None
    legacy_context: str = Field(default="", max_length=250)
    legacy_basis: str = Field(default="", max_length=350)


class ProfileClaim(WorkModel):
    id: Identifier
    topic: Topic
    text: Text
    source: SourceReference
    confirmation: Literal["unconfirmed", "confirmed", "corrected", "questioned"]
    uncertainty: ShortText
    alternatives: list[ShortText] = Field(default_factory=list, max_length=5)
    sensitive: bool = True
    updated_at: str = Field(min_length=20, max_length=40)

    @model_validator(mode="after")
    def inferred_is_tentative(self):
        if self.source.source_type == "model_inference" and not self.alternatives:
            raise ValueError("inference_alternative_required")
        return self


class ClaimInput(WorkModel):
    id: Identifier | None = None
    topic: Topic
    text: Text
    source: SourceReference
    confirmation: Literal["unconfirmed", "confirmed", "corrected", "questioned"]
    uncertainty: ShortText
    alternatives: list[ShortText] = Field(default_factory=list, max_length=5)
    sensitive: bool = True


class ProfileChange(WorkModel):
    action: Literal["upsert", "remove"]
    claim: ClaimInput | None = None
    claim_id: Identifier | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.action == "upsert" and (self.claim is None or self.claim_id is not None):
            raise ValueError("claim_required")
        if self.action == "remove" and (self.claim_id is None or self.claim is not None):
            raise ValueError("claim_id_required")
        return self


class ProfileUpdate(WorkModel):
    expected_revision: int = Field(ge=0)
    confirmed: Literal[True]
    changes: list[ProfileChange] = Field(min_length=1, max_length=30)
    unknowns: list[ShortText] | None = Field(default=None, max_length=30)
    contradictions: list[ShortText] | None = Field(default=None, max_length=30)

    @field_validator("confirmed", mode="before")
    @classmethod
    def exact_approval(cls, value):
        if value is not True:
            raise ValueError("approval_required")
        return value


class PrivateProfile(WorkModel):
    schema_version: Literal["1.0"] = "1.0"
    revision: int = Field(default=0, ge=0)
    claims: list[ProfileClaim] = Field(default_factory=list, max_length=500)
    unknowns: list[ShortText] = Field(default_factory=list, max_length=30)
    contradictions: list[ShortText] = Field(default_factory=list, max_length=30)
    updated_at: str = ""


class ShareableSummary(WorkModel):
    """Only this allowlisted object may leave local storage for the matching site."""

    schema_version: Literal["1.0"]
    summary_id: Identifier
    version: int = Field(ge=1, le=9_007_199_254_740_991)
    alias: str = Field(min_length=1, max_length=40, pattern=PUBLIC_LABEL_PATTERN)
    age_band: AgeBand
    city: str = Field(min_length=2, max_length=60, pattern=PUBLIC_LABEL_PATTERN)
    areas: list[
        Annotated[
            str,
            Field(
                min_length=2,
                max_length=60,
                pattern=PUBLIC_LABEL_PATTERN,
            ),
        ]
    ] = Field(max_length=5)
    relationship_goal: Goal
    accepted_goals: list[Goal] = Field(min_length=1, max_length=3)
    accepted_age_bands: list[AgeBand] = Field(min_length=1, max_length=6)
    values: list[ValueToken] = Field(max_length=5)
    life_directions: list[DirectionToken] = Field(max_length=5)
    communication_preferences: list[CommunicationToken] = Field(max_length=5)
    interests: list[InterestToken] = Field(max_length=8)
    preferences: list[PreferenceToken] = Field(max_length=5)
    visibility: Literal["participants"]
    discoverable: bool

    @model_validator(mode="after")
    def only_public_labels(self):
        for value in [self.alias, self.city, *self.areas]:
            # Deliberately narrow v1: no bios, URLs, contact info, multiline text,
            # instruction punctuation, exact location or arbitrary private labels.
            if not re.fullmatch(PUBLIC_LABEL_PATTERN, value):
                raise ValueError("coarse_public_label_required")
            if re.search(PRIVATE_LABEL_TERMS, value, re.I):
                raise ValueError("public_label_rejected")
        for name in (
            "areas",
            "accepted_goals",
            "accepted_age_bands",
            "values",
            "life_directions",
            "communication_preferences",
            "interests",
            "preferences",
        ):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError("duplicate_choices")
        return self

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        schema = super().model_json_schema(*args, **kwargs)
        schema["x-slowmatch-label-forbidden-pattern"] = PRIVATE_LABEL_TERMS
        for prop in schema["properties"].values():
            if prop.get("type") == "array":
                prop["uniqueItems"] = True
        return schema


class ShareableProfileDraft(WorkModel):
    schema_version: Literal["1.0"] = "1.0"
    draft_id: Identifier
    source_revision: int = Field(ge=0)
    destination: str
    audience: Literal["participants"] = "participants"
    summary: ShareableSummary
    summary_digest: Digest
    created_at: str


class PublishedProfile(WorkModel):
    """Local approval receipt; approved is not evidence of remote publication."""

    schema_version: Literal["1.0"] = "1.0"
    publication_id: Identifier
    draft_id: Identifier
    source_revision: int
    destination: str
    audience: Literal["participants"] = "participants"
    summary: ShareableSummary
    summary_digest: Digest
    approved_at: str
    status: Literal["approved", "published", "withdrawn"] = "approved"
    published_at: str | None = None
    remote_version: int | None = None


class AssessmentPoint(WorkModel):
    text: Text
    own_claim_ids: list[Identifier] = Field(min_length=1, max_length=10)
    peer_fields: list[
        Literal[
            "age_band",
            "city",
            "areas",
            "relationship_goal",
            "accepted_goals",
            "accepted_age_bands",
            "values",
            "life_directions",
            "communication_preferences",
            "interests",
            "preferences",
        ]
    ] = Field(min_length=1, max_length=10)
    uncertainty: ShortText


class PrivateMatchAssessment(WorkModel):
    schema_version: Literal["1.0"] = "1.0"
    assessment_id: Identifier
    own_revision: int = Field(ge=0)
    peer_summary_digest: Digest
    basis: Literal["own_private_profile_and_peer_shared_summary"]
    possible_alignment: list[AssessmentPoint] = Field(max_length=10)
    questions_and_tensions: list[AssessmentPoint] = Field(max_length=10)
    unknowns: list[ShortText] = Field(min_length=1, max_length=20)
    respectful_questions: list[ShortText] = Field(max_length=10)
    caveats: list[ShortText] = Field(min_length=1, max_length=10)
    created_at: str


class SummaryDraftRequest(WorkModel):
    adult_confirmed: Literal[True]
    expected_revision: int = Field(ge=0)
    destination: str = Field(max_length=300)
    summary: ShareableSummary

    @field_validator("adult_confirmed", mode="before")
    @classmethod
    def explicit_adult_declaration(cls, value):
        if value is not True:
            raise ValueError("adult_confirmation_required")
        return value


class SummaryApprovalRequest(ApprovedRequest):
    draft_id: Identifier
    expected_revision: int = Field(ge=0)
    summary_digest: Digest
    destination: str = Field(max_length=300)
    audience: Literal["participants"]


class SummaryExportRequest(WorkModel):
    publication_id: Identifier
    summary_digest: Digest
    destination: str = Field(max_length=300)


class PublicationReceiptRequest(ApprovedRequest):
    publication_id: Identifier
    summary_digest: Digest
    destination: str = Field(max_length=300)
    status: Literal["published", "withdrawn"]
    remote_version: int = Field(ge=1)


class IdentifierRequest(WorkModel):
    id: Identifier


class ProfileReadRequest(WorkModel):
    topics: list[Topic] = Field(default_factory=list, max_length=9)


class RecoverProfileRequest(ApprovedRequest):
    expected_revision: int = Field(ge=0)
    restore_revision: int = Field(ge=1)


class MemoryImportRequest(ApprovedRequest):
    expected_revision: int = Field(ge=0)
    source_vault: str = Field(min_length=1, max_length=2000)
    entry_ids: list[Identifier] = Field(min_length=1, max_length=20)


class AssessmentPrepareRequest(WorkModel):
    expected_revision: int = Field(ge=0)
    peer_summary: ShareableSummary


class AssessmentSaveRequest(ApprovedRequest):
    context_id: Identifier
    own_revision: int = Field(ge=0)
    peer_summary_digest: Digest
    possible_alignment: list[AssessmentPoint] = Field(max_length=10)
    questions_and_tensions: list[AssessmentPoint] = Field(max_length=10)
    unknowns: list[ShortText] = Field(min_length=1, max_length=20)
    respectful_questions: list[ShortText] = Field(max_length=10)
    caveats: list[ShortText] = Field(min_length=1, max_length=10)


class AssessmentContext(WorkModel):
    context_id: Identifier
    own_revision: int = Field(ge=0)
    peer_summary: ShareableSummary
    peer_summary_digest: Digest
    created_at: str
