"""Bounded connected-AI report bundles shared independently of any UI."""

from __future__ import annotations

import json
import re
from typing import Annotated, Literal

from pydantic import Field, ValidationError

from anti_dating_scam.reports.local_artifacts import (
    ArtifactModel,
    ArtifactValidationError,
    Confidence,
    EvidenceList,
    IdealProfiles,
    MateCriteria,
    SelfPortrait,
    Text,
)
from anti_dating_scam.reports.localized_reports import validate_localization


class LocalizedText(ArtifactModel):
    path: Annotated[str, Field(min_length=1, max_length=300)]
    source: Text
    en: Text
    zh: Text


Localizations = Annotated[list[LocalizedText], Field(max_length=300)]


class BundleClaim(ArtifactModel):
    # Put nested evidence last. Some small models otherwise close the claim
    # prematurely after its evidence array and misplace type/confidence fields.
    topic: Literal[
        "values", "wants", "communication", "boundaries", "market_stance", "presentation", "pattern"
    ]
    type: Literal["observation", "inference", "speculation"]
    confidence: Confidence
    claim: Text
    evidence: EvidenceList


class ConcisePortrait(SelfPortrait):
    claims: Annotated[list[BundleClaim], Field(max_length=5)]
    # New connected-AI bundles cannot use free summaries as a second channel
    # for claims that lack evidence or bypass the localization map.
    headline: None = None
    summary: None = None
    generated_at: None = None


class PortraitBundle(ArtifactModel):
    report: ConcisePortrait
    localized_text: Localizations


class ConciseCriteria(MateCriteria):
    stated: Annotated[list[BundleClaim], Field(max_length=3)]
    revealed: Annotated[list[BundleClaim], Field(max_length=3)]


class CriteriaBundle(ArtifactModel):
    criteria: ConciseCriteria
    ideal_profiles: IdealProfiles
    localized_text: Localizations


_BUNDLES = {"self_portrait": PortraitBundle, "mate_criteria": CriteriaBundle}


def bundle_schema(kind: str) -> dict:
    original = _BUNDLES[kind].model_json_schema()
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
            # Ollama's grammar converter cannot represent this nonblank search.
            # Keep minLength in generation and the FULL nonblank constraint in
            # the mandatory Pydantic validation before any files can be written.
            del result["pattern"]
        if result.get("type") == "string" and "maxLength" in result:
            # The installed llama.cpp grammar compiler rejects char{1,8000};
            # older builds also reject the 2000 repetition boundary. Request
            # concise generation below that threshold without truncating any
            # input/output. Persisted artifacts and manual/connected reply
            # parsing retain their original full Pydantic bounds (8000 for Text).
            result["maxLength"] = min(result["maxLength"], 1000)
        return result

    # Inline references for local grammar implementations that support only a
    # subset of JSON Schema. Pydantic still validates the full contract after generation.
    return inline(original)


def bundle_prompt(kind: str) -> str:
    if kind == "self_portrait":
        output_keys = "report, localized_text"
        fields = (
            "every report claim, caveat, open question, coverage covered/not_covered item, "
            "and consistency finding narrative"
        )
        paths = (
            "/report/claims/0/claim, /report/caveats/0, /report/caveats/1, "
            "/report/open_questions/0, /report/data_coverage/not_covered/0"
        )
        shape = (
            "This is a self-portrait bundle. The report object contains only self-portrait "
            "fields from its schema; localized_text is its top-level sibling. "
            "Omit optional headline, summary and generated_at. "
        )
        findings = (
            "A consistency finding requires TWO genuinely conflicting direct quotes; otherwise "
            "consistency_findings is []. Never invent contradiction findings. "
        )
    elif kind == "mate_criteria":
        output_keys = "criteria, ideal_profiles, localized_text"
        fields = (
            "every stated/revealed claim, criteria caveat, open question, ideal_profiles caveat, "
            "candidate description, nonnull choice_reason and uncertainty_notes"
        )
        paths = (
            "/criteria/stated/0/claim, /criteria/revealed/0/claim, /criteria/caveats/0, "
            "/criteria/caveats/1, /criteria/open_questions/0, /ideal_profiles/caveats/0"
        )
        shape = (
            "This is a relationship-criteria bundle. criteria, ideal_profiles and localized_text "
            "are three separate top-level siblings. Never nest ideal_profiles inside criteria. "
        )
        findings = (
            "Include fictional candidates only when an actual exercise is present in the "
            "supplied context. Empty candidates with explicit caveats are correct when no "
            "exercise occurred. Never invent participant choices or biographies. "
        )
    else:
        raise ValueError("Unsupported report bundle kind.")
    return (
        "\nReturn ONE JSON object matching the schema below, with no fences or delimiters. "
        "Do not write Markdown or a separate narrative report. The app renders the canonical "
        "report fields into both languages. "
        + shape
        + "Write each canonical narrative field in concise "
        "English and provide its faithful Simplified Chinese translation in localized_text. "
        "Each localized_text entry has path (JSON pointer), source (EXACT canonical value), "
        "en (EXACT same English value), zh (its complete Simplified Chinese translation). "
        "For a claim path, source and en must both equal the canonical claim sentence, "
        "NOT its evidence quote. For any path, copy that exact field value into source and en; "
        "do not substitute a quotation, paraphrase or neighboring field. "
        + f"Supply exactly one entry for {fields}. "
        + "Each array item needs its own entry at its own index. In particular, map every caveat "
        "separately: caveats/0 refers only to item 0 and caveats/1 only to item 1. "
        "Never join several caveats or fields into one localization entry, skip an item or "
        "reuse a path. No entries for quotes, source identifiers, schema versions, enums or IDs. "
        + f"Relevant path examples (paths only, not report content): {paths}. "
        + "Use the actual list indices. No extra paths or entries. "
        "Translate each exact field without adding interpretations or new facts. "
        "Preserve the source's scope, strength, uncertainty, frequency and intensity in both "
        "languages. A preference or wish is not a requirement or prohibition; do not strengthen "
        "wants into musts or infer a ban from a stated preference. "
        "Use at most 3 supported claims for a short input, never invent material to fill sections. "
        "Keep evidence quotations short and exact. Only use frameworks supported by the data. "
        "Empty claims with explicit caveats are correct when evidence is missing. "
        "Never invent evidence. "
        + findings
        + "Evidence quotes MUST be exact contiguous excerpts from the supplied data; never join "
        "non-adjacent sentences into one quote. Claims about the owner may cite only USER-role "
        "input, never the assistant's questions, examples, or prior generated reports. "
        "Claims.topic permits only values, wants, "
        "communication, boundaries, market_stance, presentation or pattern. Put questions in "
        "open_questions and limitations in caveats, NEVER in claims. "
        "The canonical report contains all supported evidence compactly; no scores or diagnoses. "
        "For each claim, write the fields in this order: topic, type, confidence, claim, evidence. "
        "The evidence array is the LAST field in a claim; close the claim only after that array. "
        "Validation schema (instructions only, NEVER repeat this schema as your answer):\n"
        + json.dumps(bundle_schema(kind), ensure_ascii=False)
        + "\nNow produce a DOCUMENT INSTANCE from the original user data. Your top-level keys "
        + f"must be exactly {output_keys}. Do NOT output schema keywords such as properties, "
        + "additionalProperties, type or required at the top level. Fill actual report values."
    )


def parse_bundle(
    reply: str, kind: str, *, evidence_text: str | None = None, context_text: str | None = None
) -> dict:
    try:
        if len(reply.encode("utf-8")) > 512_000:
            raise ValueError("oversized")
        stripped = reply.strip()
        if stripped.startswith("```json\n") and stripped.endswith("\n```"):
            reply = stripped[len("```json\n") : -len("\n```")]
        data = json.loads(reply)
        checked = _BUNDLES[kind].model_validate(data)
    except (ValidationError, ValueError, TypeError, RecursionError):
        raise ArtifactValidationError(
            "The AI report bundle is incomplete or invalid. No report files were saved; "
            "try a model that supports this report format. / AI 报告不完整或格式无效，"
            "未保存报告文件；请改用能够遵循此报告格式的模型。"
        ) from None
    validated = checked.model_dump(mode="json", exclude_unset=True)
    if evidence_text is not None:
        normalized_source = re.sub(r"\s+", " ", evidence_text).strip()

        def verify_quotes(value, source):
            if isinstance(value, list):
                for item in value:
                    verify_quotes(item, source)
            elif isinstance(value, dict):
                if "quote" in value and "source" in value:
                    quote = re.sub(r"\s+", " ", value["quote"]).strip()
                    if not quote or quote not in source:
                        raise ArtifactValidationError(
                            "The AI cited evidence absent from the supplied data; no files saved. "
                            "/ "
                            "AI 引用了输入材料中不存在的证据，未保存任何文件。"
                        )
                for item in value.values():
                    verify_quotes(item, source)

        for key, value in validated.items():
            if key != "ideal_profiles":
                verify_quotes(value, normalized_source)
        all_context = re.sub(r"\s+", " ", context_text or evidence_text).strip()
        for candidate in validated.get("ideal_profiles", {}).get("candidates", []):
            # A vignette may quote the assistant's fictional description. An
            # asserted owner choice must instead quote the owner's own input.
            source = normalized_source if candidate["choice_reason"] is not None else all_context
            verify_quotes(candidate, source)
    canonical = {key: value for key, value in validated.items() if key != "localized_text"}
    validate_localization(kind, canonical, validated["localized_text"])
    return validated
