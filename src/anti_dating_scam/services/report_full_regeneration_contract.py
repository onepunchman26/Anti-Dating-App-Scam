"""Bounded contracts for reports regenerated from explicitly pasted excerpts.

The application assigns source IDs. Exact quotation membership proves only that
a quote occurs in that submitted excerpt, never its truth, origin or authorship.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anti_dating_scam.reports.artifact_bundles import parse_bundle
from anti_dating_scam.services.report_review import (
    CorrectionRecord,
    Digest,
    RecordID,
    ReportKind,
    _encode,
)

MAX_EXCERPT_CHARS = 24_000


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class RegenerationExcerpt(_Model):
    text: Annotated[str, Field(min_length=1, max_length=12_000, pattern=r"\S")]


Excerpts = Annotated[list[RegenerationExcerpt], Field(min_length=1, max_length=5)]
CorrectionIDs = Annotated[list[RecordID], Field(min_length=1, max_length=10)]


def excerpt_sources(excerpts: list[RegenerationExcerpt]) -> list[dict[str, str]]:
    """Validate and assign stable IDs without trimming or modifying submitted text."""
    if type(excerpts) is not list or not 1 <= len(excerpts) <= 5:
        raise ValueError("One to five original excerpts required.")
    checked = [
        RegenerationExcerpt.model_validate(item.model_dump(warnings=False)) for item in excerpts
    ]
    if (
        sum(len(item.text) for item in checked) > MAX_EXCERPT_CHARS
        or sum(len(item.text.encode("utf-8")) for item in checked) > 96_000
    ):
        raise ValueError("Excerpt size limit exceeded.")
    return [{"id": f"S{index:03d}", "text": item.text} for index, item in enumerate(checked, 1)]


class FullRegenerationProposal(_Model):
    correction_ids: CorrectionIDs
    excerpts: Excerpts
    bundle: dict
    context_digest: Digest
    request_digest: Digest
    origin: Literal["ai_regenerated"] = "ai_regenerated"

    @model_validator(mode="after")
    def bounded_inputs(self):
        excerpt_sources(self.excerpts)
        if len(set(self.correction_ids)) != len(self.correction_ids):
            raise ValueError("Duplicate corrections.")
        if len(_encode(self.bundle)) > 512_000:
            raise ValueError("Bundle size limit exceeded.")
        return self


class FullRegenerationContext(_Model):
    kind: ReportKind
    source_digest: Digest
    context_digest: Digest
    corrections: Annotated[list[CorrectionRecord], Field(min_length=1, max_length=10)]
    caveats: list[str]


def validate_regenerated_bundle(
    kind: ReportKind, excerpts: list[RegenerationExcerpt], bundle: dict
) -> dict:
    """Validate complete localization and exact source-specific quote membership."""
    sources = {item["id"]: item["text"] for item in excerpt_sources(excerpts)}
    checked = parse_bundle(_encode(bundle).decode("utf-8"), kind)
    canonical = {key: value for key, value in checked.items() if key != "localized_text"}
    if kind == "mate_criteria" and canonical["ideal_profiles"]["candidates"]:
        raise ValueError("This workflow contains no fictional-candidate exercise.")
    if kind == "self_portrait":
        identifiers = canonical["report"]["data_coverage"]["sources_read"]
        if identifiers != list(sources):
            raise ValueError("Coverage must identify precisely the submitted source IDs.")

    def verify(value):
        if isinstance(value, list):
            for item in value:
                verify(item)
        elif isinstance(value, dict):
            if "quote" in value and "source" in value:
                quote, source = value["quote"], value["source"]
                if source not in sources or not quote.strip() or quote not in sources[source]:
                    raise ValueError("Quoted text must occur exactly within its assigned source.")
            if "confidence" in value:
                value["confidence"] = "low"
            for item in value.values():
                verify(item)

    verify(canonical)
    return {**canonical, "localized_text": checked["localized_text"]}


def validate_full_bundle(
    kind: ReportKind, bundle: dict, excerpts: list[RegenerationExcerpt]
) -> dict:
    """Public bundle-first spelling shared by request and persistence services."""
    return validate_regenerated_bundle(kind, excerpts, bundle)
