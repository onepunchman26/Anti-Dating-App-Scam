"""Source-attributed batch contracts; viewing is not participation or endorsement."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

ID = Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Origin = Literal["transcript", "description", "existing_summary", "user_annotation", "title"]


def fingerprint(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Text(Model):
    en: str = Field(min_length=1, max_length=500)
    zh: str = Field(min_length=1, max_length=500)


class AdoptableText(Model):
    en: str = Field(min_length=1, max_length=250)
    zh: str = Field(min_length=1, max_length=250)


class Material(Model):
    origin: Origin
    text: str = Field(min_length=1, max_length=4000)
    provenance: str = Field(max_length=180)
    truncated: bool = False


class Video(Model):
    id: Digest
    url: str = Field(max_length=2048)
    source: Literal["youtube", "bilibili", "tiktok", "other"]
    title: str = Field(default="", max_length=300)
    collections: list[str] = Field(default_factory=list, max_length=30)
    saved_at: str = Field(default="", max_length=40)
    materials: list[Material] = Field(default_factory=list, max_length=8)

    @property
    def digest(self):
        # A derivative summary or another filename cannot multiply evidence weight.
        return fingerprint(
            [self.id, self.title, [m.model_dump(exclude={"provenance"}) for m in self.materials]]
        )

    @property
    def coverage(self):
        if any(m.origin == "transcript" and not m.truncated for m in self.materials):
            return "full"
        if self.materials:
            return "partial"
        return "metadata" if self.title else "link"


class Quote(Model):
    video_id: Digest
    origin: Origin
    quote: str = Field(min_length=1, max_length=200)


class Topic(Model):
    broad: Text
    specific: Text


class ItemAnalysis(Model):
    summary: Text
    topics: list[Topic] = Field(max_length=3)
    creator_claims: list[Text] = Field(max_length=2)
    evidence: list[Quote] = Field(min_length=1, max_length=3)
    sensitive: bool


class Item(Model):
    video: Video
    status: Literal["pending", "full", "partial", "skipped", "failed"] = "pending"
    analysis: ItemAnalysis | None = None
    error: str = Field(default="", max_length=80)
    reused: bool = False


class Finding(Model):
    id: ID = Field(default_factory=lambda: uuid4().hex)
    kind: Literal["interest", "reflection"]
    broad: Text
    specific: Text
    text: AdoptableText
    explanation: Text
    uncertainty: Text
    pattern: Literal["possible", "recurring", "recent", "aspirational", "task_related"]
    evidence: list[Quote] = Field(min_length=1, max_length=6)
    video_ids: list[Digest] = Field(min_length=1, max_length=1000)
    status: Literal["draft", "confirmed", "rejected", "removed"] = "draft"
    edited_text: str = Field(default="", max_length=250)

    @property
    def key(self):
        return fingerprint(
            [self.kind, self.broad.en.casefold().strip(), self.specific.en.casefold().strip()]
        )


class ProposedFinding(Model):
    kind: Literal["interest", "reflection"]
    group_ids: list[str] = Field(min_length=1, max_length=24)
    text: AdoptableText
    explanation: Text
    uncertainty: Text
    pattern: Literal["possible", "recurring", "recent", "aspirational", "task_related"]


class ReflectionDraft(ProposedFinding):
    kind: Literal["reflection"]


class InterestFinding(ProposedFinding):
    kind: Literal["interest"]


class Synthesis(Model):
    findings: list[InterestFinding] = Field(max_length=12)
    reflection_drafts: list[ReflectionDraft] = Field(default_factory=list, max_length=4)
    questions: list[Text] = Field(max_length=3)


class Batch(Model):
    id: ID = Field(default_factory=lambda: uuid4().hex)
    revision: int = 0
    name: str = Field(min_length=1, max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items: list[Item] = Field(min_length=1, max_length=1000)
    duplicates: int = 0
    invalid: int = 0
    notices: list[str] = Field(default_factory=list, max_length=100)
    state: Literal["ready", "running", "paused", "complete", "failed"] = "ready"
    findings: list[Finding] = Field(default_factory=list, max_length=40)
    questions: list[Text] = Field(default_factory=list, max_length=3)
    omitted_groups: int = 0
    policy: Literal["1"] = "1"

    @property
    def digest(self):
        return fingerprint([self.policy, [i.video.model_dump() for i in self.items]])

    def counts(self):
        result = {
            key: sum(i.status == key for i in self.items)
            for key in ("pending", "full", "partial", "skipped", "failed")
        }
        return {
            "imported": len(self.items),
            **result,
            "duplicates": self.duplicates,
            "invalid": self.invalid,
            "reused": sum(i.reused for i in self.items),
        }


class Preview(Model):
    videos: list[Video] = Field(max_length=1000)
    duplicates: int = 0
    invalid: int = 0
    notices: list[str] = Field(default_factory=list, max_length=100)
