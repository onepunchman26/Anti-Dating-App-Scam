"""Explicit partial legacy conversion without supplying absent claim metadata.

Only complete bilingual claims are copied. Every original byte remains in a
separately verified archive; unsupported material is never promoted to evidence.
"""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from anti_dating_scam.reports.local_artifacts import Claim, validate_local_artifact
from anti_dating_scam.reports.localized_reports import (
    render_localized_reports,
    validate_localization,
)
from anti_dating_scam.services.legacy_reports import (
    LegacyIssue,
    LegacyReportService,
    _json_value,
)
from anti_dating_scam.services.report_review import (
    CorrectionRecord,
    Digest,
    RecordID,
    ReportKind,
    ReportReviewService,
    _decode,
    _encode,
    _hash,
)
from anti_dating_scam.services.report_revisions import MAX_RENDER_BYTES

MAX_CONVERSIONS = 100
MAX_CONVERSION_BYTES = 16_000_000
MAX_HISTORY_BYTES = 128_000_000
MAX_PREVIEW_BYTES = 8_000_000
MAX_MANIFEST_BYTES = 16_000
MAX_LEDGER_FIELDS = 2_000
_ID = re.compile(r"^[0-9a-f]{32}$")
_HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]")
_ERROR = (
    "The legacy conversion could not be verified or saved. Review the archive, current "
    "source and conversion again. Originals and existing records were not replaced. "
    "/ 无法校验或保存旧报告转换，请重新复核存档、当前来源及转换预览。原文件及已有记录未被替换。"
)
_CAVEAT = (
    "Partial legacy conversion: only entries with supplied bilingual wording, topic, "
    "claim type, confidence and quoted evidence were copied. These are unverified legacy "
    "claims; original evidence was not reread and no AI analysis occurred. Structural "
    "validation does not establish truth, source identity, quotation support or translation "
    "fidelity. Other narratives, coverage assertions, findings, questions, fictional "
    "candidates and choices remain only in the linked exact-byte archive. They were not "
    "silently merged into this report. Review the conversion ledger and original archive "
    "before using this incomplete report.",
    "旧报告的部分转换：仅复制已提供双语表述、主题、主张类型、置信度及证据引文的条目。"
    "这些仍是未经核实的旧版主张；未重读原始证据，也未进行 AI 分析。结构校验不能证明事实、"
    "来源身份、引文支持或翻译准确。其他叙述、覆盖声明、一致性发现、问题、虚构候选人及选择"
    "仅保留在关联的精确字节存档中，没有悄悄合并进本报告。使用这份不完整报告前，请复核"
    "转换清单及原始存档。",
)
_COVERED = (
    "Only structurally complete claims from the archived legacy report were copied.",
    "仅复制旧报告存档中结构完整的主张。",
)
_NOT_COVERED = (
    "Original source material was not reread; source coverage and unsupported legacy claims "
    "remain unverified and are not reconstructed.",
    "未重读原始来源材料；来源覆盖情况及不受支持的旧版主张仍未核实，也未重建。",
)
_PROFILES_CAVEAT = (
    "No fictional candidates or recorded choices were converted. Their original content "
    "remains only in the linked legacy archive.",
    "未转换虚构候选人或已记录的选择；其原始内容仅保留在关联的旧报告存档中。",
)


class LegacyConversionError(ValueError):
    """Sanitized bilingual error without source content or private paths."""


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ConversionField(_Model):
    file_label: Annotated[str, Field(min_length=1, max_length=80)]
    pointer: Annotated[str, Field(max_length=4_000)]
    status: Literal["copied", "partial", "archive_only"]
    reason_en: Annotated[str, Field(min_length=1, max_length=1_000)]
    reason_zh: Annotated[str, Field(min_length=1, max_length=1_000)]


class LegacyConversionPreview(_Model):
    kind: ReportKind
    archive_id: RecordID
    archive_digest: Digest
    source_digest: Digest
    converted_count: Annotated[int, Field(ge=0, le=100)]
    eligible: bool
    field_ledger: Annotated[list[ConversionField], Field(max_length=MAX_LEDGER_FIELDS)]
    issues: Annotated[list[LegacyIssue], Field(max_length=100)]
    canonical: dict
    localized_text: list[dict]
    markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)]
    detailed_markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)] | None
    preview_digest: Digest


class SavedLegacyConversion(_Model):
    id: RecordID
    kind: ReportKind
    created_at: Annotated[str, Field(min_length=1, max_length=40)]
    archive_id: RecordID
    source_digest: Digest
    integrity_digest: Digest
    directory_path: str

    @field_validator("created_at")
    @classmethod
    def valid_timestamp(cls, value):
        return CorrectionRecord.valid_timestamp(value)


class VerifiedConversionBundle(_Model):
    kind: ReportKind
    conversion_id: RecordID
    archive_id: RecordID
    archive_digest: Digest
    source_digest: Digest
    integrity_digest: Digest
    canonical: dict
    localized_text: list[dict]
    markdown: str
    detailed_markdown: str | None


class _Manifest(_Model):
    schema_version: Literal["0.1"]
    operation: Literal["legacy_conversion"]
    id: RecordID
    kind: ReportKind
    created_at: Annotated[str, Field(min_length=1, max_length=40)]
    archive_id: RecordID
    archive_digest: Digest
    source_digest: Digest
    preview_digest: Digest
    files: Annotated[dict[str, Digest], Field(min_length=3, max_length=4)]
    integrity_digest: Digest

    @field_validator("created_at")
    @classmethod
    def valid_timestamp(cls, value):
        return CorrectionRecord.valid_timestamp(value)


def _safe(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError):
            raise LegacyConversionError(_ERROR) from None
    return wrapped


def _bilingual(value):
    if not isinstance(value, dict) or set(value) != {"en", "zh"}:
        raise ValueError("missing bilingual text")
    en, zh = value["en"], value["zh"]
    if (
        type(en) is not str or type(zh) is not str
        or not 1 <= len(en) <= 8_000 or not 1 <= len(zh) <= 8_000
        or not re.search(r"[A-Za-z]", en) or len(_HAN.findall(zh)) < 2 or en == zh
    ):
        raise ValueError("invalid supplied languages")
    return en, zh


def _claim(value, *, criteria=False):
    if not isinstance(value, dict):
        raise ValueError("invalid legacy claim")
    text_key = "criterion" if criteria else "claim"
    pair = _bilingual(value[text_key])
    evidence = value["evidence"]
    if criteria and type(evidence) is str:
        evidence = [{"quote": evidence, "source": value["source"]}]
    # No defaults: topic, evidence, type and confidence must all have been supplied.
    claim = Claim.model_validate({
        "topic": value["topic"], "claim": pair[1], "evidence": evidence,
        "type": value["type"], "confidence": value["confidence"],
    }).model_dump(mode="json")
    return claim, pair


def _build(kind, saved_archive, archive_preview, archive_payload):
    label = f"{kind}.json"
    ledger, issues, translations = [], [], []
    blocked = False
    ledger_grouped = False

    def issue(code, en, zh):
        issues.append(LegacyIssue(code=code, message_en=en, message_zh=zh))

    def field(pointer, status, en, zh, filename=label):
        # Excessively broad legacy objects stay represented by their whole-document ledger.
        nonlocal ledger_grouped
        if len(ledger) < MAX_LEDGER_FIELDS - 1 and len(pointer) <= 4_000:
            ledger.append(ConversionField(
                file_label=filename, pointer=pointer, status=status, reason_en=en, reason_zh=zh,
            ))
        else:
            ledger_grouped = True

    def localize(pointer, pair):
        en, zh = pair
        translations.append({"path": pointer, "source": zh, "en": en, "zh": zh})
        return zh

    try:
        primary = _json_value(archive_payload[label])
        if not isinstance(primary, dict):
            raise ValueError("legacy object required")
    except (ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        primary = {}
        blocked = True
    supported = (
        primary.get("schema_version") == "0.3"
        if kind == "self_portrait"
        else primary.get("schema_version") == "0.1"
        and any(key in primary for key in ("stated_criteria", "revealed_criteria"))
    )
    if not supported:
        blocked = True
        issue("unsupported_shape", "This archived document has no supported legacy shape.",
              "这份存档不属于受支持的旧版结构。")
    field("", "partial", "The complete original is retained in the verified archive; only "
          "explicitly listed supported fields may be copied.",
          "完整原文保留在经过校验的存档中；仅可复制清单中明确列出的受支持字段。")
    handled = {"claims", "caveats"} if kind == "self_portrait" else {
        "stated_criteria", "revealed_criteria", "caveats",
    }
    for key in list(primary)[:1_000]:
        if key not in handled:
            pointer = "/" + key.replace("~", "~0").replace("/", "~1")
            field(pointer, "archive_only", "Not transferred to the current report. Exact "
                  "content remains in the original archive.",
                  "未转入当前报告；精确内容仍保留在原始存档中。")
    for archived_file in archive_preview.files:
        if archived_file.present and archived_file.label != label:
            field("", "archive_only", "This companion is retained exactly in the archive. "
                  "It is not reused as evidence, translation or a converted report.",
                  "此配套文件精确保留在存档中，不复用为证据、译文或转换后的报告。",
                  archived_file.label)

    def group(source_key, target_pointer, limit):
        values = primary.get(source_key, [])
        result = []
        if not supported:
            return result
        if not isinstance(values, list) or len(values) > limit:
            field("/" + source_key, "archive_only", "The group is invalid or exceeds the "
                  "conversion limit; no entry from this group is copied.",
                  "此分组无效或超过转换上限；本分组没有条目被复制。")
            return result
        for index, value in enumerate(values):
            pointer = f"/{source_key}/{index}"
            try:
                claim, pair = _claim(value, criteria=kind == "mate_criteria")
            except (ValueError, KeyError, TypeError, RecursionError, UnicodeError):
                field(pointer, "archive_only", "Missing or invalid bilingual wording, topic, "
                      "claim type, confidence or quoted evidence. Nothing is supplied by default.",
                      "双语表述、主题、主张类型、置信度或证据引文缺失或无效；不使用默认值补写。")
                continue
            localize(f"{target_pointer}/{len(result)}/claim", pair)
            result.append(claim)
            field(pointer, "partial", "Only the supplied wording, topic, type, confidence and "
                  "quoted evidence are copied exactly. Other entry fields remain archive-only; "
                  "support and translation have not been verified.",
                  "仅精确复制提供的表述、主题、类型、置信度及引文；条目中的其他字段仅保留于"
                  "存档，证据支持及翻译未经核实。")
            copied = ("criterion" if kind == "mate_criteria" else "claim",
                      "topic", "type", "confidence", "evidence")
            for key in copied:
                field(pointer + "/" + key, "copied", "Supplied value copied without "
                      "inventing missing metadata; wording retains both supplied languages.",
                      "复制已提供的值，不补造缺失元数据；表述保留提供的两种语言。")
            if kind == "mate_criteria" and type(value["evidence"]) is str:
                field(pointer + "/source", "copied", "Supplied source label copied exactly.",
                      "精确复制提供的来源标签。")
        return result

    if kind == "self_portrait":
        report = {
            "schema_version": "0.2", "report_type": "self_portrait",
            "data_coverage": {
                "sources_read": [],
                "covered": [localize("/report/data_coverage/covered/0", _COVERED)],
                "not_covered": [localize("/report/data_coverage/not_covered/0", _NOT_COVERED)],
            },
            "claims": group("claims", "/report/claims", 100),
            "consistency_findings": [], "open_questions": [], "caveats": [],
        }
        canonical, caveat_prefix = {"report": report}, "/report/caveats"
        count = len(report["claims"])
    else:
        report = {
            "schema_version": "0.1", "report_type": "mate_criteria",
            "stated": group("stated_criteria", "/criteria/stated", 50),
            "revealed": group("revealed_criteria", "/criteria/revealed", 50),
            "open_questions": [], "caveats": [],
        }
        canonical = {"criteria": report, "ideal_profiles": {
            "schema_version": "0.1", "candidates": [],
            "caveats": [localize("/ideal_profiles/caveats/0", _PROFILES_CAVEAT)],
        }}
        caveat_prefix = "/criteria/caveats"
        count = len(report["stated"]) + len(report["revealed"])
    caveats = primary.get("caveats", [])
    if not isinstance(caveats, list) or len(caveats) > 29:
        blocked = True
        issue("caveats_incomplete", "Original caveats cannot all be retained within the "
              "current contract. Conversion cannot be saved.",
              "无法在当前结构上限内保留全部原有警示；不能保存转换。")
        field("/caveats", "archive_only", "Invalid or excessive caveats block conversion.",
              "无效或超量的原有警示会阻止转换。")
    else:
        for index, value in enumerate(caveats):
            try:
                pair = _bilingual(value)
            except (ValueError, TypeError, KeyError):
                blocked = True
                field(f"/caveats/{index}", "archive_only", "An original caveat lacks complete "
                      "supplied bilingual text; conversion is blocked rather than omitting it.",
                      "原有警示缺少完整的双语表述；阻止转换，不将其遗漏。")
                continue
            report["caveats"].append(localize(f"{caveat_prefix}/{len(report['caveats'])}", pair))
            field(f"/caveats/{index}", "copied", "Original bilingual caveat retained exactly.",
                  "精确保留原有双语警示。")
    report["caveats"].append(localize(f"{caveat_prefix}/{len(report['caveats'])}", _CAVEAT))
    if blocked:
        issue("blocked", "Missing supported structure or complete original caveats prevents "
              "saving. The exact archive remains available.",
              "受支持的结构或完整原有警示缺失，不能保存；精确原文存档仍可用。")
    if count == 0:
        issue("no_complete_claims", "No complete bilingual evidence-bearing claim can be "
              "converted. This preview cannot be saved or selected as a report.",
              "没有可转换的完整双语证据主张；此预览不能保存或选择为报告。")
    issue("partial_unverified", _CAVEAT[0], _CAVEAT[1])
    if ledger_grouped or len(primary) > 1_000 or len(ledger) >= MAX_LEDGER_FIELDS - 1:
        issue("ledger_grouped", "The field ledger has entry-count and pointer-length limits. "
              "The root entry covers all fields not listed individually; every original byte "
              "remains in the linked archive.",
              "字段清单有条目数量及指针长度上限；整份文档条目涵盖未单独列出的所有字段，"
              "所有原始字节仍保留在关联存档中。")
    for key, contract in (
        [("report", "self_portrait")] if kind == "self_portrait"
        else [("criteria", "mate_criteria"), ("ideal_profiles", "ideal_profiles")]
    ):
        canonical[key] = validate_local_artifact(canonical[key], contract)
    validate_localization(kind, canonical, translations)
    rendered = render_localized_reports(kind, canonical, translations)
    if any(len(text.encode("utf-8")) > MAX_RENDER_BYTES for text in rendered.values()):
        raise ValueError("render size limit")
    fields = {
        "kind": kind, "archive_id": saved_archive.id,
        "archive_digest": saved_archive.archive_digest,
        "source_digest": saved_archive.source_digest,
        "converted_count": count, "eligible": count > 0 and not blocked,
        "field_ledger": [item.model_dump(mode="json") for item in ledger],
        "issues": [item.model_dump(mode="json") for item in issues],
        "canonical": canonical, "localized_text": translations,
        "markdown": rendered["markdown"], "detailed_markdown": rendered.get("detailed_markdown"),
    }
    preview = LegacyConversionPreview(**fields, preview_digest=_hash(_encode(fields)))
    payload = {
        "preview.json": _encode(preview.model_dump(mode="json")),
        "canonical.json": _encode({"canonical": canonical, "localized_text": translations}),
        "report.md": preview.markdown.encode("utf-8"),
    }
    if preview.detailed_markdown is not None:
        payload["report.detailed.md"] = preview.detailed_markdown.encode("utf-8")
    if len(payload["preview.json"]) > MAX_PREVIEW_BYTES:
        raise ValueError("preview size limit")
    return preview, payload


class LegacyConversionService:
    """Conversions retain an immutable verified archive dependency; no activation here."""

    @_safe
    def __init__(self, vault_dir: Path):
        self._io = ReportReviewService(vault_dir)
        self._archives = LegacyReportService(vault_dir)

    def _root(self, kind):
        return self._io._vault / "reports" / "converted_reports" / self._io._kind(kind)

    def _derived(self, kind, archive_id):
        saved, preview, payload, _ = self._archives._read(kind, archive_id)
        return _build(kind, saved, preview, payload)

    def _current(self, kind, archive_id):
        preview, payload = self._derived(kind, archive_id)
        if self._archives.inspect(kind).source_digest != preview.source_digest:
            raise ValueError("archive no longer matches current source")
        return preview, payload

    @_safe
    def preview_conversion(self, kind: ReportKind, archive_id: str) -> LegacyConversionPreview:
        return self._current(self._io._kind(kind), archive_id)[0]

    def _verified(self, folder, kind, identifier):
        sizes = {path.name: self._io._check(path, directory=False).st_size
                 for path in self._io._entries(folder)}
        if sum(sizes.values()) > MAX_CONVERSION_BYTES:
            raise ValueError("conversion size limit")
        raw_manifest = self._io._read(folder / "manifest.json", MAX_MANIFEST_BYTES)
        manifest = _Manifest.model_validate(_decode(raw_manifest))
        expected_names = {"preview.json", "canonical.json", "report.md"}
        if kind == "self_portrait":
            expected_names.add("report.detailed.md")
        if (
            manifest.id != identifier or manifest.kind != kind
            or set(manifest.files) != expected_names
            or set(sizes) != expected_names | {"manifest.json"}
            or raw_manifest != _encode(manifest.model_dump(mode="json"))
            or manifest.integrity_digest != _hash(_encode(
                manifest.model_dump(mode="json", exclude={"integrity_digest"})
            ))
        ):
            raise ValueError("conversion manifest mismatch")
        payload = {
            name: self._io._read(folder / name, MAX_PREVIEW_BYTES if name == "preview.json"
                                else MAX_RENDER_BYTES)
            for name in expected_names
        }
        if any(_hash(raw) != manifest.files[name] for name, raw in payload.items()):
            raise ValueError("conversion checksum mismatch")
        preview, derived = self._derived(kind, manifest.archive_id)
        if (
            not preview.eligible or derived != payload
            or preview.archive_digest != manifest.archive_digest
            or preview.source_digest != manifest.source_digest
            or preview.preview_digest != manifest.preview_digest
        ):
            raise ValueError("conversion derivation mismatch")
        record = SavedLegacyConversion(
            id=identifier, kind=kind, created_at=manifest.created_at,
            archive_id=manifest.archive_id, source_digest=manifest.source_digest,
            integrity_digest=manifest.integrity_digest, directory_path=str(folder),
        )
        return record, preview, sum(sizes.values())

    def _history(self, kind):
        root = self._root(kind)
        try:
            root.lstat()
        except FileNotFoundError:
            for parent in (root.parent.parent, root.parent):
                try:
                    parent.lstat()
                except FileNotFoundError:
                    self._io._check(parent.parent, directory=True)
                    break
                self._io._check(parent, directory=True)
            return [], 0
        entries = self._io._entries(root)
        if len(entries) > MAX_CONVERSIONS * 2 + 1:
            raise ValueError("conversion entry limit")
        records, total = [], 0
        for directory in entries:
            if directory.name == ".writer.lock":
                if self._io._check(directory, directory=False).st_size > 1:
                    raise ValueError("invalid lock")
                continue
            if self._io._is_pending_entry(directory):
                continue
            self._io._check(directory, directory=True)
            if not _ID.fullmatch(directory.name) or len(records) >= MAX_CONVERSIONS:
                raise ValueError("invalid conversion directory")
            size = sum(self._io._check(path, directory=False).st_size
                       for path in self._io._entries(directory))
            if total + size > MAX_HISTORY_BYTES:
                raise ValueError("conversion history size limit")
            record, _, actual_size = self._verified(directory, kind, directory.name)
            total += actual_size
            records.append(record)
        return sorted(records, key=lambda item: (item.created_at, item.id)), total

    @_safe
    def list_conversions(self, kind: ReportKind) -> list[SavedLegacyConversion]:
        return self._history(self._io._kind(kind))[0]

    def _read(self, kind, identifier):
        kind = self._io._kind(kind)
        if type(identifier) is not str or not _ID.fullmatch(identifier):
            raise ValueError("invalid conversion identifier")
        return self._verified(self._root(kind) / identifier, kind, identifier)

    @_safe
    def read_conversion(self, kind: ReportKind, identifier: str) -> LegacyConversionPreview:
        return self._read(kind, identifier)[1]

    @_safe
    def read_verified_bundle(self, kind: ReportKind, identifier: str) -> VerifiedConversionBundle:
        record, preview, _ = self._read(kind, identifier)
        return VerifiedConversionBundle(
            kind=kind, conversion_id=identifier, archive_id=record.archive_id,
            archive_digest=preview.archive_digest, source_digest=record.source_digest,
            integrity_digest=record.integrity_digest, canonical=preview.canonical,
            localized_text=preview.localized_text, markdown=preview.markdown,
            detailed_markdown=preview.detailed_markdown,
        )

    @_safe
    def save_conversion(self, preview: LegacyConversionPreview, *, confirmed: bool
                        ) -> SavedLegacyConversion:
        if confirmed is not True or not isinstance(preview, LegacyConversionPreview):
            raise ValueError("explicit conversion confirmation required")
        preview = LegacyConversionPreview.model_validate(
            preview.model_dump(mode="json", warnings=False),
        )
        current, payload = self._current(preview.kind, preview.archive_id)
        if not preview.eligible or current != preview:
            raise ValueError("ineligible, altered or stale conversion")
        root = self._root(preview.kind)
        self._io._mkdir(root.parent)
        self._io._mkdir(root)
        with self._io._writer(root):
            records, total = self._history(preview.kind)
            if self._current(preview.kind, preview.archive_id)[0] != preview:
                raise ValueError("source changed before saving")
            identifier = uuid4().hex
            fields = {
                "schema_version": "0.1", "operation": "legacy_conversion", "id": identifier,
                "kind": preview.kind, "created_at": datetime.now(UTC).isoformat(),
                "archive_id": preview.archive_id, "archive_digest": preview.archive_digest,
                "source_digest": preview.source_digest, "preview_digest": preview.preview_digest,
                "files": {name: _hash(raw) for name, raw in payload.items()},
            }
            manifest = _Manifest(**fields, integrity_digest=_hash(_encode(fields)))
            payload["manifest.json"] = _encode(manifest.model_dump(mode="json"))
            size = sum(map(len, payload.values()))
            if (len(records) >= MAX_CONVERSIONS or size > MAX_CONVERSION_BYTES
                    or total + size > MAX_HISTORY_BYTES):
                raise ValueError("conversion storage limit")
            stage, final = root / f".pending-{identifier}", root / identifier
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            stage.mkdir(mode=0o700)
            self._io._check(stage, directory=True)
            for name, raw in payload.items():
                self._io._write_new(stage / name, raw)
            self._verified(stage, preview.kind, identifier)
            if self._current(preview.kind, preview.archive_id)[0] != preview:
                raise ValueError("source changed during saving")
            self._io._check(root, directory=True)
            self._io._check(stage, directory=True)
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            os.rename(stage, final)
            return SavedLegacyConversion(
                id=identifier, kind=preview.kind, created_at=manifest.created_at,
                archive_id=preview.archive_id, source_digest=preview.source_digest,
                integrity_digest=manifest.integrity_digest, directory_path=str(final),
            )
