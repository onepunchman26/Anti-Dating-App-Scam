"""Single-reply bilingual wire format for full report regeneration only.

The model supplies both languages beside each narrative field. Projection only
copies those strings into the existing canonical/localization contract; it never
translates, repairs missing content, or verifies the truth of a claim or quote.
Historical report contracts and other generation workflows remain unchanged.
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import Field, ValidationError

from anti_dating_scam.reports.artifact_bundles import parse_bundle
from anti_dating_scam.reports.local_artifacts import (
    MAX_ARTIFACT_BYTES,
    ArtifactModel,
    ArtifactValidationError,
    BilingualText,
    Confidence,
    Evidence,
    EvidenceList,
    ShortText,
)

_Pairs = Annotated[list[BilingualText], Field(max_length=50)]
_Caveats = Annotated[list[BilingualText], Field(min_length=1, max_length=30)]
_FINDING_FIELDS = (
    "stated",
    "contradicting",
    "framing",
    "clarifying_question",
    "alt_benign_explanation",
)
_ERROR = (
    "The bilingual AI report is incomplete or invalid. No report files were saved. "
    "/ AI 双语报告不完整或格式无效，未保存报告文件。"
)


class _PairedClaim(ArtifactModel):
    topic: Literal[
        "values", "wants", "communication", "boundaries", "market_stance", "presentation", "pattern"
    ]
    type: Literal["observation", "inference", "speculation"]
    confidence: Confidence
    claim: BilingualText
    evidence: EvidenceList


class _PairedCoverage(ArtifactModel):
    sources_read: Annotated[list[ShortText], Field(max_length=100)]
    covered: _Pairs
    not_covered: _Pairs


class _PairedFinding(ArtifactModel):
    kind: Literal[
        "stated_vs_revealed",
        "front_vs_back",
        "internal_logic",
        "double_standard",
        "temporal_drift",
        "embellishment",
    ]
    stated: BilingualText
    contradicting: BilingualText
    quotes: Annotated[list[Evidence], Field(min_length=2, max_length=20)]
    confidence: Confidence
    framing: BilingualText
    clarifying_question: BilingualText
    alt_benign_explanation: BilingualText


class _PairedPortrait(ArtifactModel):
    schema_version: Literal["0.2"]
    report_type: Literal["self_portrait"] = "self_portrait"
    data_coverage: _PairedCoverage
    claims: Annotated[list[_PairedClaim], Field(max_length=5)]
    consistency_findings: Annotated[list[_PairedFinding], Field(max_length=40)]
    open_questions: _Pairs
    caveats: _Caveats


class _PairedCriteria(ArtifactModel):
    schema_version: Literal["0.1"]
    report_type: Literal["mate_criteria"] = "mate_criteria"
    stated: Annotated[list[_PairedClaim], Field(max_length=3)]
    revealed: Annotated[list[_PairedClaim], Field(max_length=3)]
    open_questions: _Pairs
    caveats: _Caveats


class _PairedProfiles(ArtifactModel):
    schema_version: Literal["0.1"]
    # This workflow has no fictional-candidate exercise. Requiring [] avoids
    # both invented people and an unnecessary candidate schema for the model.
    candidates: Annotated[list[None], Field(max_length=0)]
    caveats: _Caveats


class _PortraitWire(ArtifactModel):
    report: _PairedPortrait


class _CriteriaWire(ArtifactModel):
    criteria: _PairedCriteria
    ideal_profiles: _PairedProfiles


_WIRES = {"self_portrait": _PortraitWire, "mate_criteria": _CriteriaWire}


def _wire_model(kind: str) -> type[ArtifactModel]:
    try:
        return _WIRES[kind]
    except (KeyError, TypeError):
        raise ArtifactValidationError("Unsupported paired report bundle kind.") from None


def paired_bundle_schema(kind: str) -> dict:
    """Return a grammar-friendly generation schema, never an artifact migration."""
    original = _wire_model(kind).model_json_schema()
    definitions = original.get("$defs", {})

    def inline(value):
        if isinstance(value, list):
            return [inline(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            return inline(definitions[value["$ref"].rsplit("/", 1)[-1]])
        result = {key: inline(item) for key, item in value.items() if key != "$defs"}
        if result.get("pattern") == r"\S":
            del result["pattern"]
        if result.get("type") == "string" and "maxLength" in result:
            # Existing local grammar compilers reject large repetitions. Only
            # generation asks for <=1000 characters; full Pydantic validation
            # retains Text's 8000 limit and nonblank check. Never truncate text.
            result["maxLength"] = min(result["maxLength"], 1000)
        return result

    return inline(original)


def paired_bundle_prompt(kind: str, *, generation_schema: dict | None = None) -> str:
    _wire_model(kind)
    if kind == "self_portrait":
        keys = "report"
        scope = (
            "The only top-level field is report. Pair every claim, each covered/not_covered "
            "coverage item, every finding narrative, each open question and each caveat. "
            "A consistency finding requires TWO genuinely conflicting direct quotes; "
            "otherwise consistency_findings is []. Never invent a contradiction. "
        )
    else:
        keys = "criteria, ideal_profiles"
        scope = (
            "The top-level fields are criteria and ideal_profiles, as separate siblings. "
            "Pair each stated/revealed claim, each open question, each criteria caveat and "
            "each ideal_profiles caveat. ideal_profiles.candidates MUST be []; no candidate "
            "exercise is performed in this workflow. Never invent people or owner choices. "
        )
    return (
        "\nReturn ONE JSON document matching the schema below, without fences or Markdown. "
        + scope
        + "Every narrative field is an object with exactly two string fields: en (concise "
        "English) and zh (its complete faithful Simplified Chinese translation). Both are "
        "required, nonblank strings, never arrays. Each array item has its own pair; never "
        "merge separate caveats or questions. Quotes and source IDs remain plain unchanged "
        "strings, and enums/schema versions remain their schema values. Do not translate "
        "evidence quotes or source IDs. Do not output localized_text, localization paths, "
        "headline, summary or generated_at. The app derives its existing localization "
        "mapping directly from the supplied pairs; it does not supply missing translations. "
        "Translate each exact narrative without adding interpretations or new facts. "
        "Preserve scope, strength, uncertainty, frequency and intensity in both languages. "
        "A preference or wish is not a requirement or prohibition; do not strengthen wants "
        "into musts, infer a ban, or rule out other explanations without evidence. "
        "Use at most 3 supported claims for short input. Empty claim lists with explicit "
        "caveats are correct when evidence is missing. Never invent evidence or fill sections "
        "with unsupported material. Questions belong in open_questions and limitations in "
        "caveats, never claims. No scores, rankings, diagnoses or deterministic person labels. "
        "Evidence quotes must be exact contiguous excerpts of the supplied original USER "
        "data, with its assigned source ID; never join non-adjacent passages. Prior generated "
        "reports, corrections, assistant questions and examples are context, not new evidence. "
        "Keep every claim's fields in order: topic, type, confidence, claim, evidence. "
        "The evidence array is last. Structural validation cannot establish factual truth "
        "or translation fidelity; keep interpretations appropriately uncertain. "
        "Validation schema (instructions only; do not repeat it as the answer):\n"
        + json.dumps(
            paired_bundle_schema(kind) if generation_schema is None else generation_schema,
            ensure_ascii=False,
        )
        + f"\nProduce a document instance with exactly these top-level fields: {keys}. "
        "Do not output schema keywords as document fields."
    )


def project_paired_bundle(kind: str, data: Any) -> dict:
    """Validate one reply and copy explicitly typed pairs into canonical paths.

    No file/provider access or quote authenticity check occurs here. The full
    regeneration service must still bind every quote to its submitted excerpt.
    """
    model = _wire_model(kind)
    try:
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False)
        if len(encoded.encode("utf-8")) > MAX_ARTIFACT_BYTES:
            raise ValueError("oversized")
        checked = model.model_validate(data)
    except (ValidationError, ValueError, TypeError, RecursionError, UnicodeError):
        raise ArtifactValidationError(_ERROR) from None

    localizations: list[dict[str, str]] = []

    def narrative(pair: BilingualText, path: str) -> str:
        localizations.append({"path": path, "source": pair.en, "en": pair.en, "zh": pair.zh})
        return pair.en

    def narratives(pairs: list[BilingualText], path: str) -> list[str]:
        return [narrative(pair, f"{path}/{index}") for index, pair in enumerate(pairs)]

    def claims(items: list[_PairedClaim], path: str) -> list[dict]:
        return [
            {
                "topic": claim.topic,
                "type": claim.type,
                "confidence": claim.confidence,
                "claim": narrative(claim.claim, f"{path}/{index}/claim"),
                "evidence": [item.model_dump(mode="json") for item in claim.evidence],
            }
            for index, claim in enumerate(items)
        ]

    if isinstance(checked, _PortraitWire):
        report = checked.report
        canonical_report = report.model_dump(
            mode="json",
            exclude_unset=True,
            exclude={
                "data_coverage",
                "claims",
                "consistency_findings",
                "open_questions",
                "caveats",
            },
        )
        coverage = report.data_coverage
        canonical_report["data_coverage"] = {
            "sources_read": list(coverage.sources_read),
            "covered": narratives(coverage.covered, "/report/data_coverage/covered"),
            "not_covered": narratives(coverage.not_covered, "/report/data_coverage/not_covered"),
        }
        canonical_report["claims"] = claims(report.claims, "/report/claims")
        findings = []
        for index, finding in enumerate(report.consistency_findings):
            item = finding.model_dump(mode="json", exclude=set(_FINDING_FIELDS))
            for field in _FINDING_FIELDS:
                item[field] = narrative(
                    getattr(finding, field), f"/report/consistency_findings/{index}/{field}"
                )
            findings.append(item)
        canonical_report["consistency_findings"] = findings
        canonical_report["open_questions"] = narratives(
            report.open_questions, "/report/open_questions"
        )
        canonical_report["caveats"] = narratives(report.caveats, "/report/caveats")
        canonical = {"report": canonical_report}
    else:
        criteria = checked.criteria
        canonical_criteria = criteria.model_dump(
            mode="json",
            exclude_unset=True,
            exclude={"stated", "revealed", "open_questions", "caveats"},
        )
        canonical_criteria["stated"] = claims(criteria.stated, "/criteria/stated")
        canonical_criteria["revealed"] = claims(criteria.revealed, "/criteria/revealed")
        canonical_criteria["open_questions"] = narratives(
            criteria.open_questions, "/criteria/open_questions"
        )
        canonical_criteria["caveats"] = narratives(criteria.caveats, "/criteria/caveats")
        canonical = {
            "criteria": canonical_criteria,
            "ideal_profiles": {
                "schema_version": checked.ideal_profiles.schema_version,
                "candidates": [],
                "caveats": narratives(checked.ideal_profiles.caveats, "/ideal_profiles/caveats"),
            },
        }
    # Historical canonical models and exact localization coverage/language
    # validation remain final authority, including byte and localization limits.
    return parse_bundle(
        json.dumps(
            {**canonical, "localized_text": localizations},
            ensure_ascii=False,
            allow_nan=False,
        ),
        kind,
    )
