"""Immutable reviewed copies with explicitly attributed, unverified interpretations.

Checksums detect accidental corruption, not an attacker able to rewrite the vault.
The source snapshots, annotations and derived files commit as one directory.
"""

from __future__ import annotations

import copy
import os
import re
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from anti_dating_scam.reports.local_artifacts import MAX_ARTIFACT_BYTES, validate_local_artifact
from anti_dating_scam.reports.localized_reports import (
    render_localized_reports,
    required_localization_sources,
    validate_localization,
)
from anti_dating_scam.services.report_full_regeneration_contract import (
    FullRegenerationContext,
    FullRegenerationProposal,
    validate_full_bundle,
)
from anti_dating_scam.services.report_review import (
    MAX_RECORD_BYTES,
    CorrectionRecord,
    Digest,
    RecordID,
    ReportKind,
    ReportReviewService,
    ReviewClaim,
    _decode,
    _encode,
    _Envelope,
    _hash,
)

MAX_REVISIONS = 100
MAX_REVISION_BYTES = 40_000_000
MAX_HISTORY_BYTES = 128_000_000
MAX_RENDER_BYTES = 4_000_000
MAX_MANIFEST_BYTES = 256_000
_ID = re.compile(r"^[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ERROR = (
    "The reviewed copy could not be verified or saved safely. Refresh and review again. "
    "/ 无法安全验证或保存复核副本，请刷新后重新复核。"
)
_COMMON_EN = (
    "Reviewed withdrawal copy: selected claims were withdrawn; multiple selected notes about "
    "one claim withdraw that claim only once. No replacement facts were added, and correction "
    "text remains a separate user annotation. Other content has not been reanalyzed and may "
    "still need correction. Coverage describes the original input, not proof of retained claims."
)
_COMMON_ZH = (
    "经复核的撤回副本：已撤回所选主张；同一主张即使有多条被选中的更正记录，也只撤回一次。"
    "没有加入替代事实，更正文字仍为单独保存的用户批注。其他内容未经重新分析，仍可能需要更正。"
    "材料覆盖范围描述的是原始输入，并不证明保留的主张成立。"
)
_WITHDRAWAL = {
    "self_portrait": (
        _COMMON_EN + " All consistency findings and optional headline/summary fields were removed "
        "because they may depend on withdrawn claims.",
        _COMMON_ZH + "所有一致性发现及可选标题、摘要均已移除，因为它们可能依赖被撤回的主张。",
    ),
    "mate_criteria": (
        _COMMON_EN + " All fictional profiles and recorded choices were removed because they "
        "may depend on withdrawn claims.",
        _COMMON_ZH + "所有虚构档案及其中记录的选择均已移除，因为它们可能依赖被撤回的主张。",
    ),
}
_PROFILES_CAVEAT = (
    "This reviewed copy retains no fictional profiles or recorded choices; "
    "no new analysis occurred.",
    "此复核副本未保留任何虚构档案或其中记录的选择，也未进行新的分析。",
)
_HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]")
_PROPOSAL_EN = "User-proposed interpretation (unverified): "
_PROPOSAL_ZH = "用户提出的解释（未经核实）："
_REPLACEMENT_CAVEAT = (
    "User-proposed interpretation copy: one original claim was replaced with separately "
    "submitted English and Chinese wording. The replacement is explicitly unverified "
    "speculation with low confidence. Its topic and original cited quotations/source labels "
    "are unchanged; retaining citations does not establish support for the new interpretation, "
    "source identity, factual truth, or translation fidelity. Correction notes were not "
    "automatically turned into facts. Dependent findings, optional summaries and fictional "
    "profiles/choices were removed where applicable. No AI analysis occurred; other content "
    "was not reanalyzed and may still require correction. Coverage and any generated timestamp "
    "describe the original input/analysis, not verification of this proposal.",
    "用户解释复核副本：一条原始主张已替换为用户单独提交的中英文表述。替代内容明确标为未经核实、"
    "低置信度的猜测，其主题、原有证据引文及来源标签保持不变。保留引文并不能证明新解释获得支持、"
    "来源身份可靠、事实属实或翻译准确。更正注释没有被自动变成事实。适用的关联发现、可选摘要及"
    "虚构档案和选择已移除。此次没有进行 AI 分析；其他内容未经重新分析，仍可能需要更正。"
    "材料覆盖范围及原有生成时间描述的是原始输入和分析，并不代表此提议经过验证。",
)
_AI_PROPOSAL_EN = "AI-assisted interpretation (quote-limited, unverified): "
_AI_PROPOSAL_ZH = "AI 辅助解释（仅依据已有引文，未经核实）："
_AI_REPLACEMENT_CAVEAT = (
    "AI-assisted interpretation copy: one disputed claim was reconsidered using only its "
    "saved quotations and correction context; the wording may subsequently have been edited "
    "by the user. The replacement remains unverified speculation with low confidence. "
    "Its topic and original quotations/source labels are unchanged. Original evidence files "
    "were not opened; source labels were not followed as paths. Retaining quotations does "
    "not establish support for this interpretation, source identity, truth or translation "
    "fidelity. Corrections are annotations, not replacement evidence. Dependent findings, "
    "summaries and fictional profiles/choices were removed where applicable. Other content "
    "was not reanalyzed. Coverage and original timestamps describe the original report. "
    "Request/context hashes bind recorded inputs; they do not prove a model call or provenance.",
    "AI 辅助解释副本：仅依据一条争议主张已有的引文和更正背景重新考虑其措辞，"
    "用户可能随后编辑了文字。"
    "替代内容仍是未经核实、低置信度的猜测，主题及原有引文和来源标签保持不变。未打开原始证据文件，"
    "未把来源标签当成路径读取。保留引文不能证明新解释获得支持、来源身份可靠、事实属实或翻译准确。"
    "更正只是批注，不是替代证据。适用的关联发现、摘要及虚构档案和选择已移除，其他内容未经重新分析。"
    "覆盖范围及原有时间描述原报告。请求与背景哈希用于绑定记录的输入，不能证明模型调用或内容来源。",
)
_AI_PROFILES_CAVEAT = (
    "This AI-assisted copy retains no fictional profiles or recorded choices; "
    "those profiles and choices were not reanalyzed.",
    "此 AI 辅助副本未保留虚构档案或其中记录的选择，也未对这些档案和选择重新分析。",
)


class ReportRevisionError(ValueError):
    """Sanitized bilingual error, never a rejected value or private path."""


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class RevisionPreview(_Model):
    kind: ReportKind
    source_digest: Digest
    correction_ids: Annotated[list[RecordID], Field(min_length=1, max_length=1_000)]
    removed_claims: Annotated[list[ReviewClaim], Field(min_length=1, max_length=100)]
    markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)]
    detailed_markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)] | None
    preview_digest: Digest


class ReplacementProposal(_Model):
    correction_id: RecordID
    text_en: Annotated[str, Field(min_length=1, max_length=4_000, pattern=r"\S")]
    text_zh: Annotated[str, Field(min_length=1, max_length=4_000, pattern=r"\S")]

    @model_validator(mode="after")
    def language_presence(self):
        # Check user input before adding labels; fixed prefixes must not satisfy this check.
        if (
            not re.search(r"[A-Za-z]", self.text_en)
            or len(_HAN.findall(self.text_zh)) < 2
            or self.text_en == self.text_zh
        ):
            raise ValueError("Both language versions must be supplied and reviewed.")
        return self


class ReplacementPreview(RevisionPreview):
    operation: Literal["replace_claim"]
    proposal: ReplacementProposal
    replacement_claim: ReviewClaim


class AIReplacementProposal(ReplacementProposal):
    origin: Literal["ai_assisted"] = "ai_assisted"
    context_digest: Digest
    request_digest: Digest


class AIReplacementPreview(ReplacementPreview):
    operation: Literal["ai_replace_claim"]
    proposal: AIReplacementProposal


class AIReplacementContext(_Model):
    kind: ReportKind
    source_digest: Digest
    context_digest: Digest
    correction: CorrectionRecord
    original_claim: ReviewClaim


class FullRegenerationPreview(RevisionPreview):
    removed_claims: Annotated[list[ReviewClaim], Field(max_length=100)]
    operation: Literal["regenerate_report"]
    proposal: FullRegenerationProposal


class SavedRevision(_Model):
    id: RecordID
    kind: ReportKind
    source_digest: Digest
    revision_digest: Digest
    created_at: Annotated[str, Field(min_length=1, max_length=40)]
    markdown_path: str
    directory_path: str

    @field_validator("created_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        return CorrectionRecord.valid_timestamp(value)


class VerifiedRevisionBundle(_Model):
    """In-memory verified report data; annotation/snapshot contents stay private."""

    kind: ReportKind
    revision_id: RecordID
    integrity_digest: Digest
    source_file_digests: dict[str, Digest]
    canonical: dict
    localized_text: list[dict]
    markdown: str
    detailed_markdown: str | None


class _Manifest(_Model):
    schema_version: Literal["0.1"]
    id: RecordID
    kind: ReportKind
    source_digest: Digest
    preview_digest: Digest
    revision_digest: Digest
    created_at: Annotated[str, Field(min_length=1, max_length=40)]
    files: Annotated[dict[str, Digest], Field(min_length=1, max_length=1_010)]
    manifest_digest: Digest

    @field_validator("created_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        return CorrectionRecord.valid_timestamp(value)


class _ReplacementManifest(_Manifest):
    schema_version: Literal["0.2"]
    operation: Literal["replace_claim"]


class _AIReplacementManifest(_Manifest):
    schema_version: Literal["0.3"]
    operation: Literal["ai_replace_claim"]


class _FullRegenerationManifest(_Manifest):
    schema_version: Literal["0.4"]
    operation: Literal["regenerate_report"]


def _safe(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError):
            raise ReportRevisionError(_ERROR) from None

    return wrapped


def _selection(ids: list[str]) -> list[str]:
    if (
        type(ids) is not list
        or not 1 <= len(ids) <= 1_000
        or any(type(item) is not str or not _ID.fullmatch(item) for item in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError("invalid selection")
    return sorted(ids)


def _companion(raw: bytes) -> dict:
    value = _decode(raw)
    if set(value) != {"schema_version", "localized_text"} or value["schema_version"] != "0.1":
        raise ValueError("invalid companion")
    return value


def _source_names(kind: str) -> set[str]:
    return {"source_report.json", "source_localization.json"} | (
        {"source_ideal_profiles.json"} if kind == "mate_criteria" else set()
    )


def _output_names(kind: str) -> set[str]:
    return {"report.json", "localization.json", "report.md"} | (
        {"report.detailed.md"} if kind == "self_portrait" else {"ideal_profiles.json"}
    )


def _limit(name: str) -> int:
    if name == "manifest.json":
        return MAX_MANIFEST_BYTES
    if name.startswith("correction-"):
        return MAX_RECORD_BYTES
    if name.endswith(".md") or name == "preview.json":
        return MAX_RENDER_BYTES
    return MAX_ARTIFACT_BYTES


def _checked_inputs(kind: str, sources: dict[str, bytes], notes: dict[str, bytes]):
    if set(sources) != _source_names(kind):
        raise ValueError("invalid source set")
    ids = _selection(list(notes))
    original = validate_local_artifact(_decode(sources["source_report.json"]), kind)
    document = ReportReviewService._document(kind, sources["source_report.json"])
    canonical = {"report" if kind == "self_portrait" else "criteria": original}
    if kind == "mate_criteria":
        canonical["ideal_profiles"] = validate_local_artifact(
            _decode(sources["source_ideal_profiles.json"]), "ideal_profiles"
        )
    translations = _companion(sources["source_localization.json"])["localized_text"]
    validate_localization(kind, canonical, translations)
    selected_paths = set()
    for identifier in ids:
        envelope = _Envelope.model_validate(_decode(notes[identifier]))
        record = envelope.record
        if (
            record.id != identifier
            or record.kind != kind
            or record.report_digest != document.report_digest
            or envelope.record_digest != _hash(_encode(record.model_dump(mode="json")))
            or ReportReviewService._target(document, record.target_path).claim
            != record.original_claim
        ):
            raise ValueError("invalid selected annotation")
        selected_paths.add(record.target_path)
    return document, canonical, translations, ids, selected_paths


def _build(kind: str, sources: dict[str, bytes], notes: dict[str, bytes]):
    """Version 0.1 withdrawal derivation; keep its serialized outputs unchanged."""
    document, canonical, translations, ids, selected_paths = _checked_inputs(kind, sources, notes)
    old_entries = {entry["path"]: entry for entry in translations}
    removed = [claim for claim in document.claims if claim.path in selected_paths]
    revised = copy.deepcopy(canonical)
    root = "report" if kind == "self_portrait" else "criteria"
    report = revised[root]
    moved: dict[str, str] = {}
    for group in ("claims",) if kind == "self_portrait" else ("stated", "revealed"):
        kept = []
        for old_index, claim in enumerate(report[group]):
            if f"/{group}/{old_index}" not in selected_paths:
                moved[f"/{root}/{group}/{len(kept)}/claim"] = f"/{root}/{group}/{old_index}/claim"
                kept.append(claim)
        report[group] = kept
    if kind == "self_portrait":
        report["consistency_findings"] = []
        report.pop("headline", None)
        report.pop("summary", None)
    else:
        revised["ideal_profiles"]["candidates"] = []
    additions = {}

    def caveat(target: dict, prefix: str, bilingual: tuple[str, str]):
        path = f"{prefix}/caveats/{len(target['caveats'])}"
        target["caveats"].append(bilingual[0])
        additions[path] = {
            "path": path,
            "source": bilingual[0],
            "en": bilingual[0],
            "zh": bilingual[1],
        }

    caveat(report, f"/{root}", _WITHDRAWAL[kind])
    if kind == "mate_criteria":
        caveat(revised["ideal_profiles"], "/ideal_profiles", _PROFILES_CAVEAT)
    # Schema validation here also rejects a full caveat list; no original warning is dropped.
    required = required_localization_sources(kind, revised)
    entries = []
    for path, source in required.items():
        entry = dict(additions[path] if path in additions else old_entries[moved.get(path, path)])
        entry["path"] = path
        if entry["source"] != source:
            raise ValueError("reindex source mismatch")
        entries.append(entry)
    validate_localization(kind, revised, entries)
    rendered = render_localized_reports(kind, revised, entries)
    outputs = {
        "report.json": _encode(revised[root]),
        "localization.json": _encode({"schema_version": "0.1", "localized_text": entries}),
        "report.md": rendered["markdown"].encode("utf-8"),
    }
    if kind == "self_portrait":
        outputs["report.detailed.md"] = rendered["detailed_markdown"].encode("utf-8")
    else:
        outputs["ideal_profiles.json"] = _encode(revised["ideal_profiles"])
    output_hashes = {name: _hash(raw) for name, raw in outputs.items()}
    revision_digest = _hash(_encode(output_hashes))
    fields = {
        "kind": kind,
        "source_digest": document.report_digest,
        "correction_ids": ids,
        "removed_claims": [claim.model_dump(mode="json") for claim in removed],
        "markdown": rendered["markdown"],
        "detailed_markdown": rendered.get("detailed_markdown"),
    }
    digest = _hash(
        _encode(
            {
                "preview": fields,
                "sources": {name: _hash(raw) for name, raw in sources.items()},
                "notes": {identifier: _hash(raw) for identifier, raw in notes.items()},
                "outputs": output_hashes,
            }
        )
    )
    preview = RevisionPreview(**fields, preview_digest=digest)
    payload = {
        **sources,
        **{f"correction-{identifier}.json": raw for identifier, raw in notes.items()},
        **outputs,
        "preview.json": _encode(preview.model_dump(mode="json")),
    }
    if (
        any(len(raw) > _limit(name) for name, raw in payload.items())
        or sum(len(raw) for raw in payload.values()) > MAX_REVISION_BYTES
    ):
        raise ValueError("copy size exceeded")
    return preview, payload, revision_digest


def _ai_context(kind, sources, notes):
    document, _, _, ids, paths = _checked_inputs(kind, sources, notes)
    if len(ids) != 1 or len(paths) != 1:
        raise ValueError("one current correction required")
    return AIReplacementContext(
        kind=kind,
        source_digest=document.report_digest,
        context_digest=_hash(_encode({
            "kind": kind,
            "sources": {name: _hash(raw) for name, raw in sources.items()},
            "notes": {identifier: _hash(raw) for identifier, raw in notes.items()},
        })),
        correction=_Envelope.model_validate(_decode(notes[ids[0]])).record,
        original_claim=ReportReviewService._target(document, next(iter(paths))),
    )


def _build_replacement(kind, sources, notes, proposal: ReplacementProposal):
    is_ai = isinstance(proposal, AIReplacementProposal)
    proposal_type = AIReplacementProposal if is_ai else ReplacementProposal
    proposal = proposal_type.model_validate(proposal.model_dump(mode="json", warnings=False))
    if is_ai and proposal.context_digest != _ai_context(kind, sources, notes).context_digest:
        raise ValueError("stale AI context")
    document, canonical, translations, ids, paths = _checked_inputs(kind, sources, notes)
    if ids != [proposal.correction_id] or len(paths) != 1:
        raise ValueError("one current correction required")
    path = next(iter(paths))
    before = ReportReviewService._target(document, path)
    revised = copy.deepcopy(canonical)
    root = "report" if kind == "self_portrait" else "criteria"
    report = revised[root]
    _, group, index = path.split("/")
    replacement = copy.deepcopy(report[group][int(index)])
    # Chinese is the canonical source for this one edited narrative. The original
    # language-preservation contract therefore keeps its exact zh text and EN map.
    prefix_en, prefix_zh = (
        (_AI_PROPOSAL_EN, _AI_PROPOSAL_ZH) if is_ai else (_PROPOSAL_EN, _PROPOSAL_ZH)
    )
    replacement.update(claim=prefix_zh + proposal.text_zh, type="speculation", confidence="low")
    report[group][int(index)] = replacement
    after = ReviewClaim(path=path, **replacement)
    if kind == "self_portrait":
        report["consistency_findings"] = []
        report.pop("headline", None)
        report.pop("summary", None)
    else:
        revised["ideal_profiles"]["candidates"] = []
    entries_by_path = {entry["path"]: dict(entry) for entry in translations}
    replacement_path = f"/{root}{path}/claim"
    entries_by_path[replacement_path] = {
        "path": replacement_path,
        "source": after.claim,
        "en": prefix_en + proposal.text_en,
        "zh": after.claim,
    }

    def add_caveat(target, prefix, bilingual):
        pointer = f"{prefix}/caveats/{len(target['caveats'])}"
        target["caveats"].append(bilingual[0])
        entries_by_path[pointer] = {
            "path": pointer,
            "source": bilingual[0],
            "en": bilingual[0],
            "zh": bilingual[1],
        }

    add_caveat(report, f"/{root}", _AI_REPLACEMENT_CAVEAT if is_ai else _REPLACEMENT_CAVEAT)
    if kind == "mate_criteria":
        add_caveat(
            revised["ideal_profiles"], "/ideal_profiles",
            _AI_PROFILES_CAVEAT if is_ai else _PROFILES_CAVEAT,
        )
    # A full warning list rejects cleanly rather than dropping existing caveats.
    required = required_localization_sources(kind, revised)
    entries = [entries_by_path[pointer] for pointer in required]
    validate_localization(kind, revised, entries)
    rendered = render_localized_reports(kind, revised, entries)
    outputs = {
        "report.json": _encode(revised[root]),
        "localization.json": _encode({"schema_version": "0.1", "localized_text": entries}),
        "report.md": rendered["markdown"].encode("utf-8"),
    }
    if kind == "self_portrait":
        outputs["report.detailed.md"] = rendered["detailed_markdown"].encode("utf-8")
    else:
        outputs["ideal_profiles.json"] = _encode(revised["ideal_profiles"])
    output_hashes = {name: _hash(raw) for name, raw in outputs.items()}
    proposal_raw = _encode(proposal.model_dump(mode="json"))
    fields = {
        "kind": kind,
        "source_digest": document.report_digest,
        "correction_ids": ids,
        "removed_claims": [before.model_dump(mode="json")],
        "markdown": rendered["markdown"],
        "detailed_markdown": rendered.get("detailed_markdown"),
        "operation": "ai_replace_claim" if is_ai else "replace_claim",
        "proposal": proposal.model_dump(mode="json"),
        "replacement_claim": after.model_dump(mode="json"),
    }
    digest = _hash(
        _encode(
            {
                "preview": fields,
                "proposal_digest": _hash(proposal_raw),
                "sources": {name: _hash(raw) for name, raw in sources.items()},
                "notes": {identifier: _hash(raw) for identifier, raw in notes.items()},
                "outputs": output_hashes,
            }
        )
    )
    preview_type = AIReplacementPreview if is_ai else ReplacementPreview
    preview = preview_type(**fields, preview_digest=digest)
    payload = {
        **sources,
        **{f"correction-{identifier}.json": raw for identifier, raw in notes.items()},
        **outputs,
        "proposal.json": proposal_raw,
        "preview.json": _encode(preview.model_dump(mode="json")),
    }
    if (
        any(len(raw) > _limit(name) for name, raw in payload.items())
        or sum(map(len, payload.values())) > MAX_REVISION_BYTES
    ):
        raise ValueError("copy size exceeded")
    return preview, payload, _hash(_encode(output_hashes))


_REGENERATION_CAVEAT = (
    "AI-regenerated report (unverified): the entire report was reconsidered using only the "
    "explicitly submitted original excerpts identified by S001 and subsequent source IDs. "
    "Every quotation was checked for exact occurrence within its identified excerpt; this "
    "does not authenticate the source, establish truth, verify the interpretation or ensure "
    "translation fidelity. All findings retain low confidence. Corrections and prior AI "
    "claims are context, never new evidence. Earlier warnings are retained historical "
    "context and may describe the previous report. No source files were opened or followed. "
    "No fictional-candidate exercise or recorded choices were regenerated. Input/request "
    "hashes bind recorded data and do not prove model execution or authorship.",
    "AI 重新生成的报告（未经核实）：仅根据明确提交的原始摘录，重新考虑了整份报告；"
    "来源编号从 S001 开始。每条引文均已检查是否逐字出现在对应摘录中；这不能认证来源、"
    "证明事实、验证解释或保证翻译准确。所有发现均保留低置信度。更正和先前 AI 主张只是背景，"
    "不是新证据。保留的早期警示属于历史背景，可能描述上一份报告。未打开或追踪原始文件。"
    "未重新生成虚构候选人练习或选择记录。输入及请求哈希用于绑定记录的数据，不能证明模型执行或作者身份。",
)


def _full_context(kind, sources, notes):
    document, canonical, _, ids, _ = _checked_inputs(kind, sources, notes)
    root = "report" if kind == "self_portrait" else "criteria"
    caveats = list(canonical[root]["caveats"])
    if kind == "mate_criteria":
        caveats.extend(canonical["ideal_profiles"]["caveats"])
    return FullRegenerationContext(
        kind=kind,
        source_digest=document.report_digest,
        context_digest=_hash(_encode({
            "kind": kind,
            "sources": {name: _hash(raw) for name, raw in sources.items()},
            "notes": {identifier: _hash(raw) for identifier, raw in notes.items()},
        })),
        corrections=[_Envelope.model_validate(_decode(notes[item])).record for item in ids],
        caveats=caveats,
    )


def _build_full_regeneration(kind, sources, notes, proposal):
    proposal = FullRegenerationProposal.model_validate(
        proposal.model_dump(mode="json", warnings=False)
    )
    context = _full_context(kind, sources, notes)
    document, old, old_entries, ids, _ = _checked_inputs(kind, sources, notes)
    if (
        proposal.context_digest != context.context_digest
        or sorted(proposal.correction_ids) != ids
    ):
        raise ValueError("Regeneration context changed.")
    bundle = validate_full_bundle(kind, proposal.bundle, proposal.excerpts)
    revised = {key: value for key, value in bundle.items() if key != "localized_text"}
    entries = {entry["path"]: dict(entry) for entry in bundle["localized_text"]}
    old_translations = {entry["path"]: entry for entry in old_entries}
    root = "report" if kind == "self_portrait" else "criteria"
    # The host-owned notice and every old warning survive in both languages. A
    # schema limit rejects the copy rather than silently dropping any warning.
    for member in (root,) if kind == "self_portrait" else (root, "ideal_profiles"):
        target = revised[member]
        additions = [
            (warning, old_translations[f"/{member}/caveats/{index}"])
            for index, warning in enumerate(old[member]["caveats"])
        ]
        additions.append((_REGENERATION_CAVEAT[0], {
            "source": _REGENERATION_CAVEAT[0], "en": _REGENERATION_CAVEAT[0],
            "zh": _REGENERATION_CAVEAT[1],
        }))
        for warning, translation in additions:
            pointer = f"/{member}/caveats/{len(target['caveats'])}"
            target["caveats"].append(warning)
            entries[pointer] = {**translation, "path": pointer}
    required = required_localization_sources(kind, revised)
    localized = [entries[pointer] for pointer in required]
    validate_localization(kind, revised, localized)
    rendered = render_localized_reports(kind, revised, localized)
    outputs = {
        "report.json": _encode(revised[root]),
        "localization.json": _encode({"schema_version": "0.1", "localized_text": localized}),
        "report.md": rendered["markdown"].encode("utf-8"),
    }
    if kind == "self_portrait":
        outputs["report.detailed.md"] = rendered["detailed_markdown"].encode("utf-8")
    else:
        outputs["ideal_profiles.json"] = _encode(revised["ideal_profiles"])
    output_hashes = {name: _hash(raw) for name, raw in outputs.items()}
    proposal_raw = _encode(proposal.model_dump(mode="json"))
    fields = {
        "kind": kind, "source_digest": document.report_digest,
        "correction_ids": ids,
        "removed_claims": [claim.model_dump(mode="json") for claim in document.claims],
        "markdown": rendered["markdown"],
        "detailed_markdown": rendered.get("detailed_markdown"),
        "operation": "regenerate_report", "proposal": proposal.model_dump(mode="json"),
    }
    digest = _hash(_encode({
        "preview": fields, "proposal_digest": _hash(proposal_raw),
        "sources": {name: _hash(raw) for name, raw in sources.items()},
        "notes": {identifier: _hash(raw) for identifier, raw in notes.items()},
        "outputs": output_hashes,
    }))
    preview = FullRegenerationPreview(**fields, preview_digest=digest)
    payload = {
        **sources,
        **{f"correction-{identifier}.json": raw for identifier, raw in notes.items()},
        **outputs, "regeneration.json": proposal_raw,
        "preview.json": _encode(preview.model_dump(mode="json")),
    }
    if (
        any(len(raw) > _limit(name) for name, raw in payload.items())
        or sum(map(len, payload.values())) > MAX_REVISION_BYTES
    ):
        raise ValueError("copy size exceeded")
    return preview, payload, _hash(_encode(output_hashes))


class ReportRevisionService:
    """Build a separate immutable reviewed copy without rewriting its source."""

    @_safe
    def __init__(self, vault_dir: Path):
        self._review = ReportReviewService(vault_dir)

    def _root(self, kind: str) -> Path:
        return self._review._vault / "reports" / "reviewed_copies" / self._review._kind(kind)

    def _current_inputs(self, kind: str, ids: list[str], expected_digest: str):
        kind = self._review._kind(kind)
        ids = _selection(ids)
        if type(expected_digest) is not str or not _DIGEST.fullmatch(expected_digest):
            raise ValueError("invalid digest")
        reports = self._review._vault / "reports"
        paths = {
            "source_report.json": reports / f"{kind}.json",
            "source_localization.json": reports / f"{kind}_localization.json",
        }
        if kind == "mate_criteria":
            paths["source_ideal_profiles.json"] = reports / "ideal_partner_profiles.json"
        sources = {
            name: self._review._read(path, MAX_ARTIFACT_BYTES) for name, path in paths.items()
        }
        if _hash(sources["source_report.json"]) != expected_digest:
            raise ValueError("stale report")
        available = {
            record.id: record for record in self._review.list_corrections(kind, expected_digest)
        }
        if not set(ids) <= set(available):
            raise ValueError("unavailable selected note")
        notes = {
            identifier: self._review._read(
                self._review._history(kind) / identifier / "correction.json", MAX_RECORD_BYTES
            )
            for identifier in ids
        }
        return sources, notes

    def _current(
        self,
        kind: str,
        ids: list[str],
        expected_digest: str,
        *,
        proposal: ReplacementProposal | FullRegenerationProposal | None = None,
    ):
        sources, notes = self._current_inputs(kind, ids, expected_digest)
        if isinstance(proposal, FullRegenerationProposal):
            return _build_full_regeneration(kind, sources, notes, proposal)
        return (
            _build_replacement(kind, sources, notes, proposal)
            if proposal is not None
            else _build(kind, sources, notes)
        )

    @_safe
    def preview_withdrawals(
        self, kind: ReportKind, correction_ids: list[str], *, expected_digest: str
    ) -> RevisionPreview:
        return self._current(kind, correction_ids, expected_digest)[0]

    @_safe
    def preview_replacement(
        self, kind: ReportKind, proposal: ReplacementProposal, *, expected_digest: str
    ) -> ReplacementPreview:
        if not isinstance(proposal, ReplacementProposal):
            raise ValueError("typed proposal required")
        proposal = ReplacementProposal.model_validate(
            proposal.model_dump(mode="json", warnings=False)
        )
        return self._current(kind, [proposal.correction_id], expected_digest, proposal=proposal)[0]

    @_safe
    def context_for_ai_replacement(
        self, kind: ReportKind, correction_id: str, *, expected_digest: str
    ) -> AIReplacementContext:
        """Return only one reviewed claim and annotation, never follow evidence source labels."""
        sources, notes = self._current_inputs(kind, [correction_id], expected_digest)
        return _ai_context(kind, sources, notes)

    @_safe
    def context_for_full_regeneration(
        self, kind: ReportKind, correction_ids: list[str], *, expected_digest: str
    ) -> FullRegenerationContext:
        if type(correction_ids) is not list or not 1 <= len(correction_ids) <= 10:
            raise ValueError("One to ten selected corrections required.")
        sources, notes = self._current_inputs(kind, correction_ids, expected_digest)
        return _full_context(kind, sources, notes)

    @_safe
    def preview_full_regeneration(
        self, kind: ReportKind, proposal: FullRegenerationProposal, *, expected_digest: str
    ) -> FullRegenerationPreview:
        if not isinstance(proposal, FullRegenerationProposal):
            raise ValueError("Typed full regeneration proposal required.")
        proposal = FullRegenerationProposal.model_validate(
            proposal.model_dump(mode="json", warnings=False)
        )
        return self._current(
            kind, proposal.correction_ids, expected_digest, proposal=proposal
        )[0]

    @_safe
    def preview_ai_replacement(
        self, kind: ReportKind, proposal: AIReplacementProposal, *, expected_digest: str
    ) -> AIReplacementPreview:
        if not isinstance(proposal, AIReplacementProposal):
            raise ValueError("typed AI-assisted proposal required")
        proposal = AIReplacementProposal.model_validate(
            proposal.model_dump(mode="json", warnings=False)
        )
        return self._current(kind, [proposal.correction_id], expected_digest, proposal=proposal)[0]

    def _verified(self, folder: Path, kind: str, identifier: str, *, include_payload=False):
        files = self._review._entries(folder)
        sizes = {file.name: self._review._check(file, directory=False).st_size for file in files}
        if sum(sizes.values()) > MAX_REVISION_BYTES:
            raise ValueError("copy size exceeded")
        manifest_raw = self._review._read(folder / "manifest.json", MAX_MANIFEST_BYTES)
        manifest_data = _decode(manifest_raw)
        version = manifest_data.get("schema_version")
        is_full = version == "0.4"
        is_ai = version == "0.3"
        is_replacement = version in {"0.2", "0.3"}
        manifest_type = (
            _FullRegenerationManifest if is_full else _AIReplacementManifest if is_ai
            else _ReplacementManifest if is_replacement else _Manifest
        )
        manifest = manifest_type.model_validate(manifest_data)
        body = manifest.model_dump(mode="json", exclude={"manifest_digest"})
        if (
            manifest.id != identifier
            or manifest.kind != kind
            or manifest.manifest_digest != _hash(_encode(body))
            or set(sizes) != set(manifest.files) | {"manifest.json"}
        ):
            raise ValueError("manifest mismatch")
        # Only fixed names or exact UUID note names may reach a file read.
        expected = _source_names(kind) | _output_names(kind) | {"preview.json"}
        if is_replacement:
            expected.add("proposal.json")
        if is_full:
            expected.add("regeneration.json")
        note_names = set(manifest.files) - expected
        note_ids = []
        for name in note_names:
            match = re.fullmatch(r"correction-([0-9a-f]{32})\.json", name)
            if not match:
                raise ValueError("invalid snapshot name")
            note_ids.append(match[1])
        if not expected <= set(manifest.files):
            raise ValueError("missing copy file")
        _selection(note_ids)
        payload = {name: self._review._read(folder / name, _limit(name)) for name in manifest.files}
        if any(_hash(raw) != manifest.files[name] for name, raw in payload.items()):
            raise ValueError("copy checksum mismatch")
        sources = {name: payload[name] for name in _source_names(kind)}
        notes = {identifier: payload[f"correction-{identifier}.json"] for identifier in note_ids}
        if is_full:
            proposal = FullRegenerationProposal.model_validate(
                _decode(payload["regeneration.json"])
            )
            preview, rebuilt, revision_digest = _build_full_regeneration(
                kind, sources, notes, proposal
            )
        elif is_replacement:
            proposal_type = AIReplacementProposal if is_ai else ReplacementProposal
            proposal = proposal_type.model_validate(_decode(payload["proposal.json"]))
            preview, rebuilt, revision_digest = _build_replacement(kind, sources, notes, proposal)
        else:
            preview, rebuilt, revision_digest = _build(kind, sources, notes)
        if (
            rebuilt != payload
            or manifest.source_digest != preview.source_digest
            or manifest.preview_digest != preview.preview_digest
            or manifest.revision_digest != revision_digest
        ):
            raise ValueError("copy derivation mismatch")
        saved = SavedRevision(
            id=identifier,
            kind=kind,
            source_digest=preview.source_digest,
            revision_digest=revision_digest,
            created_at=manifest.created_at,
            markdown_path=str(folder / "report.md"),
            directory_path=str(folder),
        )
        result = (saved, preview, sum(sizes.values()))
        return (*result, payload, manifest_raw) if include_payload else result

    def _history(self, kind: str):
        root = self._root(kind)
        try:
            root.lstat()
        except FileNotFoundError:
            for parent in (root.parent.parent, root.parent):
                try:
                    parent.lstat()
                except FileNotFoundError:
                    break
                self._review._check(parent, directory=True)
            return [], 0
        entries = self._review._entries(root)
        if len(entries) > MAX_REVISIONS * 2 + 1:
            raise ValueError("too many copy entries")
        saved, total = [], 0
        for folder in entries:
            if folder.name == ".writer.lock":
                if self._review._check(folder, directory=False).st_size > 1:
                    raise ValueError("invalid lock")
                continue
            if self._review._is_pending_entry(folder):
                continue
            self._review._check(folder, directory=True)
            if not _ID.fullmatch(folder.name) or len(saved) >= MAX_REVISIONS:
                raise ValueError("invalid copy entry")
            # Aggregate metadata bounds are checked before reading that copy's contents.
            size = sum(
                self._review._check(file, directory=False).st_size
                for file in self._review._entries(folder)
            )
            if total + size > MAX_HISTORY_BYTES:
                raise ValueError("copy history exceeded")
            item, _, verified_size = self._verified(folder, kind, folder.name)
            total += verified_size
            saved.append(item)
        return sorted(saved, key=lambda item: (item.created_at, item.id)), total

    @_safe
    def list_revisions(self, kind: ReportKind) -> list[SavedRevision]:
        return self._history(self._review._kind(kind))[0]

    @_safe
    def read_revision(self, kind: ReportKind, revision_id: str) -> RevisionPreview:
        kind = self._review._kind(kind)
        if type(revision_id) is not str or not _ID.fullmatch(revision_id):
            raise ValueError("invalid revision id")
        return self._verified(self._root(kind) / revision_id, kind, revision_id)[1]

    @_safe
    def read_verified_bundle(self, kind: ReportKind, revision_id: str) -> VerifiedRevisionBundle:
        """Return only the verified derived report and hashes of exact source snapshots.

        Verification and extraction use the same bounded in-memory bytes; consumers
        never receive arbitrary read paths, correction text, or original snapshots.
        """
        kind = self._review._kind(kind)
        if type(revision_id) is not str or not _ID.fullmatch(revision_id):
            raise ValueError("invalid revision id")
        _, preview, _, payload, manifest_raw = self._verified(
            self._root(kind) / revision_id, kind, revision_id, include_payload=True
        )
        canonical = {
            "report" if kind == "self_portrait" else "criteria": _decode(payload["report.json"])
        }
        if kind == "mate_criteria":
            canonical["ideal_profiles"] = _decode(payload["ideal_profiles.json"])
        return VerifiedRevisionBundle(
            kind=kind,
            revision_id=revision_id,
            integrity_digest=_hash(
                _encode(
                    {
                        **{name: _hash(raw) for name, raw in payload.items()},
                        "manifest.json": _hash(manifest_raw),
                    }
                )
            ),
            source_file_digests={name: _hash(payload[name]) for name in _source_names(kind)},
            canonical=canonical,
            localized_text=_companion(payload["localization.json"])["localized_text"],
            markdown=preview.markdown,
            detailed_markdown=preview.detailed_markdown,
        )

    @_safe
    def save_withdrawals(self, preview: RevisionPreview, *, confirmed: bool) -> SavedRevision:
        if confirmed is not True or not isinstance(preview, RevisionPreview):
            raise ValueError("explicit confirmation and preview required")
        # Revalidate even model_copy/model_construct callers, then compare the full preview.
        preview = RevisionPreview.model_validate(preview.model_dump(mode="json", warnings=False))
        return self._save_preview(preview)

    @_safe
    def save_replacement(self, preview: ReplacementPreview, *, confirmed: bool) -> SavedRevision:
        if confirmed is not True or not isinstance(preview, ReplacementPreview):
            raise ValueError("explicit confirmation and replacement preview required")
        preview = ReplacementPreview.model_validate(preview.model_dump(mode="json", warnings=False))
        return self._save_preview(preview, proposal=preview.proposal)

    @_safe
    def save_ai_replacement(
        self, preview: AIReplacementPreview, *, confirmed: bool
    ) -> SavedRevision:
        if confirmed is not True or not isinstance(preview, AIReplacementPreview):
            raise ValueError("explicit confirmation and AI-assisted preview required")
        preview = AIReplacementPreview.model_validate(
            preview.model_dump(mode="json", warnings=False)
        )
        return self._save_preview(preview, proposal=preview.proposal)

    @_safe
    def save_full_regeneration(
        self, preview: FullRegenerationPreview, *, confirmed: bool
    ) -> SavedRevision:
        if confirmed is not True or not isinstance(preview, FullRegenerationPreview):
            raise ValueError("Explicit confirmation and full regeneration preview required.")
        preview = FullRegenerationPreview.model_validate(
            preview.model_dump(mode="json", warnings=False)
        )
        return self._save_preview(preview, proposal=preview.proposal)

    def _save_preview(self, preview, *, proposal=None):
        current, payload, revision_digest = self._current(
            preview.kind, preview.correction_ids, preview.source_digest, proposal=proposal
        )
        if current != preview:
            raise ValueError("stale or modified preview")
        self._history(preview.kind)
        root = self._root(preview.kind)
        self._review._mkdir(root.parent)
        self._review._mkdir(root)
        with self._review._writer(root):
            records, total = self._history(preview.kind)
            current, payload, revision_digest = self._current(
                preview.kind, preview.correction_ids, preview.source_digest, proposal=proposal
            )
            if current != preview:
                raise ValueError("stale or modified preview")
            identifier = uuid4().hex
            manifest_body = {
                "schema_version": "0.1",
                "id": identifier,
                "kind": preview.kind,
                "source_digest": preview.source_digest,
                "preview_digest": preview.preview_digest,
                "revision_digest": revision_digest,
                "created_at": datetime.now(UTC).isoformat(),
                "files": {name: _hash(raw) for name, raw in payload.items()},
            }
            is_ai = isinstance(proposal, AIReplacementProposal)
            is_full = isinstance(proposal, FullRegenerationProposal)
            if is_full:
                manifest_body.update(schema_version="0.4", operation="regenerate_report")
            elif proposal is not None:
                manifest_body.update(
                    schema_version="0.3" if is_ai else "0.2",
                    operation="ai_replace_claim" if is_ai else "replace_claim",
                )
            manifest_type = (
                _FullRegenerationManifest if is_full else _AIReplacementManifest if is_ai
                else _ReplacementManifest if proposal is not None else _Manifest
            )
            manifest = manifest_type(**manifest_body, manifest_digest=_hash(_encode(manifest_body)))
            payload["manifest.json"] = _encode(manifest.model_dump(mode="json"))
            size = sum(len(raw) for raw in payload.values())
            if (
                len(records) >= MAX_REVISIONS
                or size > MAX_REVISION_BYTES
                or total + size > MAX_HISTORY_BYTES
            ):
                raise ValueError("copy history limit reached")
            stage, final = root / f".pending-{identifier}", root / identifier
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            stage.mkdir(mode=0o700)
            self._review._check(stage, directory=True)
            for name, raw in payload.items():
                self._review._write_new(stage / name, raw)
            self._verified(stage, preview.kind, identifier)
            if (
                self._current(
                    preview.kind, preview.correction_ids, preview.source_digest, proposal=proposal
                )[0]
                != preview
            ):
                raise ValueError("source changed during save")
            self._review._check(root, directory=True)
            self._review._check(stage, directory=True)
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            os.rename(stage, final)
            return SavedRevision(
                id=identifier,
                kind=preview.kind,
                source_digest=preview.source_digest,
                revision_digest=revision_digest,
                created_at=manifest.created_at,
                markdown_path=str(final / "report.md"),
                directory_path=str(final),
            )
