"""Lossless local legacy-report archives, without conversion or evidence promotion.

Raw bytes are authoritative. Parsed shape and plain-text displays are review aids
only; missing evidence, uncertainty or translations are never manufactured.
"""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from anti_dating_scam.reports.local_artifacts import validate_local_artifact
from anti_dating_scam.reports.localized_reports import validate_localization
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

MAX_FILE_BYTES = 2_000_000
MAX_BUNDLE_BYTES = 10_000_000
MAX_PREVIEW_BYTES = 64_000_000
MAX_ARCHIVE_BYTES = 80_000_000
MAX_ARCHIVES = 100
MAX_HISTORY_BYTES = 256_000_000
MAX_MANIFEST_BYTES = 16_000
MAX_LEDGER_FIELDS = 1_000
_MEMBERS = {
    "self_portrait": (
        "self_portrait.json",
        "self_portrait.md",
        "self_portrait.detailed.md",
        "self_portrait_localization.json",
        "self_portrait.html",
    ),
    "mate_criteria": (
        "mate_criteria.json",
        "mate_criteria.md",
        "mate_criteria_localization.json",
        "ideal_partner_profiles.json",
    ),
}
_ID = re.compile(r"^[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ERROR = (
    "The legacy archive could not be verified or saved safely. Refresh the source files and "
    "review again. Existing originals and archives were not replaced. "
    "/ 无法安全校验或保存旧报告归档，请刷新源文件后重新复核。原文件及已有归档未被替换。"
)
ArchiveFormat = Literal[
    "self_portrait_v03",
    "mate_criteria_legacy_v01",
    "current_structured",
    "markdown_only",
    "unrecognized",
    "missing",
]


class LegacyReportError(ValueError):
    """Privacy-safe bilingual public error."""


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class LegacyFile(_Model):
    label: Annotated[str, Field(min_length=1, max_length=80)]
    present: bool
    size_bytes: Annotated[int, Field(ge=0, le=MAX_FILE_BYTES)]
    sha256: Digest | None
    text: Annotated[str, Field(max_length=MAX_FILE_BYTES)] | None
    encoding: Literal["utf8", "binary", "missing"]


class LegacyIssue(_Model):
    code: Annotated[str, Field(min_length=1, max_length=80)]
    message_en: Annotated[str, Field(min_length=1, max_length=1_000)]
    message_zh: Annotated[str, Field(min_length=1, max_length=1_000)]


class LegacyField(_Model):
    file_label: Annotated[str, Field(min_length=1, max_length=80)]
    pointer: Annotated[str, Field(max_length=MAX_FILE_BYTES)]
    value_type: Literal["object", "array", "string", "number", "boolean", "null", "opaque"]
    status: Literal["preserved_only"] = "preserved_only"


class LegacyInspection(_Model):
    kind: ReportKind
    source_digest: Digest
    format: ArchiveFormat
    files: Annotated[list[LegacyFile], Field(min_length=1, max_length=5)]
    issues: Annotated[list[LegacyIssue], Field(max_length=100)]


class LegacyArchivePreview(LegacyInspection):
    field_ledger: Annotated[list[LegacyField], Field(max_length=MAX_LEDGER_FIELDS + 5)]
    review_text_en: Annotated[str, Field(min_length=1, max_length=20_000)]
    review_text_zh: Annotated[str, Field(min_length=1, max_length=20_000)]
    preview_digest: Digest


class SavedLegacyArchive(_Model):
    id: RecordID
    kind: ReportKind
    created_at: Annotated[str, Field(min_length=1, max_length=40)]
    source_digest: Digest
    archive_digest: Digest
    directory_path: str

    @field_validator("created_at")
    @classmethod
    def valid_timestamp(cls, value):
        return CorrectionRecord.valid_timestamp(value)


class _Manifest(_Model):
    schema_version: Literal["0.1"]
    operation: Literal["legacy_archive"]
    id: RecordID
    kind: ReportKind
    created_at: Annotated[str, Field(min_length=1, max_length=40)]
    source_digest: Digest
    archive_digest: Digest
    preview_digest: Digest
    files: Annotated[dict[str, Digest], Field(min_length=2, max_length=6)]
    manifest_digest: Digest

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
            raise LegacyReportError(_ERROR) from None

    return wrapped


def _json_value(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonstandard constant")

    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique, parse_constant=invalid)


def _value_type(value):
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    return "number"


def _build(kind: str, sources: dict[str, bytes | None]):
    if set(sources) != set(_MEMBERS[kind]):
        raise ValueError("invalid source members")
    files, issues, ledger, parsed = [], [], [], {}

    def issue(code, en, zh):
        issues.append(LegacyIssue(code=code, message_en=en, message_zh=zh))

    issue(
        "preservation_only",
        "Archive and review only: no conversion, verification of claims, "
        "translation, activation, or AI request occurs.",
        "仅归档与复核：不进行格式转换、主张核实、翻译、启用或 AI 请求。",
    )
    issue(
        "plaintext_snapshot",
        "Saving retains plaintext copies of all present fixed report "
        "files, including unsupported fields and any HTML, without changing the originals.",
        "保存会保留当前固定报告文件的明文副本，包括不支持的字段及 HTML；原件保持不变。",
    )
    issue(
        "language_and_provenance",
        "Original content remains in its supplied language. Missing "
        "evidence, confidence and translations stay missing; "
        "citations are not verified identities.",
        "原始内容保留其提供时的语言。缺失的证据、置信度和译文仍为缺失；引文来源不是已核实的身份。",
    )
    total = 0
    for label in _MEMBERS[kind]:
        raw = sources[label]
        if raw is None:
            files.append(
                LegacyFile(
                    label=label,
                    present=False,
                    size_bytes=0,
                    sha256=None,
                    text=None,
                    encoding="missing",
                )
            )
            continue
        total += len(raw)
        if len(raw) > MAX_FILE_BYTES or total > MAX_BUNDLE_BYTES:
            raise ValueError("source byte limit")
        try:
            text = raw.decode("utf-8")  # Keep BOM, whitespace and line endings in this review copy.
            encoding = "utf8"
        except UnicodeError:
            text, encoding = None, "binary"
            issue(
                "invalid_utf8",
                f"{label}: bytes are preserved exactly; a UTF-8 text view is unavailable.",
                f"{label}：原始字节完整保留，无法提供 UTF-8 文本视图。",
            )
        files.append(
            LegacyFile(
                label=label,
                present=True,
                size_bytes=len(raw),
                sha256=_hash(raw),
                text=text,
                encoding=encoding,
            )
        )
        if not label.endswith(".json"):
            ledger.append(LegacyField(file_label=label, pointer="", value_type="opaque"))
            continue
        try:
            value = _json_value(raw)
            # Unpaired surrogates cannot enter a safe Unicode preview/ledger.
            json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (ValueError, TypeError, RecursionError, UnicodeError):
            ledger.append(LegacyField(file_label=label, pointer="", value_type="opaque"))
            issue(
                "invalid_json",
                f"{label}: JSON could not be safely interpreted. Exact bytes are retained.",
                f"{label}：无法安全解析 JSON，原始字节仍完整保留。",
            )
            continue
        parsed[label] = value
        if (
            isinstance(value, dict)
            and len(ledger) + len(value) <= MAX_LEDGER_FIELDS
            and all(
                len(key.replace("~", "~0").replace("/", "~1")) + 1 <= MAX_FILE_BYTES
                for key in value
            )
        ):
            for key, field in value.items():
                pointer = "/" + key.replace("~", "~0").replace("/", "~1")
                ledger.append(
                    LegacyField(file_label=label, pointer=pointer, value_type=_value_type(field))
                )
        else:
            ledger.append(LegacyField(file_label=label, pointer="", value_type=_value_type(value)))
            if isinstance(value, dict):
                issue(
                    "ledger_grouped",
                    f"{label}: the field ledger is grouped at the document root "
                    "because of its size. All fields remain in the full text and exact snapshot.",
                    f"{label}：字段数量较多，清单按整份文档展示。所有字段仍保留在完整文本及精确快照中。",
                )
    primary = parsed.get(f"{kind}.json")
    detected = "unrecognized"
    if not any(item.present for item in files):
        detected = "missing"
        issue(
            "no_files",
            "No fixed report files are present; there is nothing to archive.",
            "固定报告文件均不存在，没有可归档的内容。",
        )
    elif isinstance(primary, dict):
        try:
            validate_local_artifact(primary, kind)
            detected = "current_structured"
        except ValueError:
            if (
                kind == "self_portrait"
                and primary.get("schema_version") == "0.3"
                and any(key in primary for key in ("claims", "top_values", "wants", "connection"))
            ):
                detected = "self_portrait_v03"
            elif (
                kind == "mate_criteria"
                and primary.get("schema_version") == "0.1"
                and any(key in primary for key in ("stated_criteria", "revealed_criteria"))
                and not any(key in primary for key in ("stated", "revealed"))
            ):
                detected = "mate_criteria_legacy_v01"
    elif sources[f"{kind}.json"] is None and any(
        raw is not None and label.endswith(".md") for label, raw in sources.items()
    ):
        detected = "markdown_only"
    if detected == "unrecognized":
        issue(
            "unrecognized_shape",
            "The report shape is unrecognized. It is preserved as supplied, "
            "not interpreted as a current validated report.",
            "无法识别报告结构。内容按原样保留，不会被解释为当前有效报告。",
        )
    if detected == "current_structured":
        issue(
            "current_shape_only",
            "The primary JSON has the current structured shape. This label "
            "alone does not mean that its required companion files form a complete valid bundle.",
            "主 JSON 文件符合当前结构。此标签本身不代表必需的配套文件构成完整有效的报告组合。",
        )
        canonical = {"report" if kind == "self_portrait" else "criteria": primary}
        complete = True
        if kind == "mate_criteria":
            if sources["ideal_partner_profiles.json"] is None:
                complete = False
                issue(
                    "missing_ideal_profiles",
                    "The required fictional-profile companion is missing.",
                    "缺少必需的虚构档案配套文件。",
                )
            else:
                try:
                    canonical["ideal_profiles"] = validate_local_artifact(
                        parsed.get("ideal_partner_profiles.json"), "ideal_profiles"
                    )
                except ValueError:
                    complete = False
                    issue(
                        "invalid_ideal_profiles",
                        "The fictional-profile companion is not valid "
                        "under the current structural contract; original bytes remain preserved.",
                        "虚构档案配套文件不符合当前结构契约；原始字节仍完整保留。",
                    )
        locale_label = f"{kind}_localization.json"
        if sources[locale_label] is None:
            complete = False
            issue(
                "missing_localization",
                "The required bilingual localization companion is missing.",
                "缺少必需的双语映射配套文件。",
            )
        else:
            try:
                locale = parsed.get(locale_label)
                if (
                    not isinstance(locale, dict)
                    or set(locale) != {"schema_version", "localized_text"}
                    or locale["schema_version"] != "0.1"
                ):
                    raise ValueError("invalid locale envelope")
                if complete:
                    validate_localization(kind, canonical, locale["localized_text"])
                else:
                    # A missing/invalid canonical companion precludes full map validation.
                    raise ValueError("incomplete bundle")
            except (ValueError, KeyError, TypeError):
                complete = False
                issue(
                    "invalid_localization",
                    "The bilingual map is invalid, incomplete, or cannot "
                    "be fully checked without valid canonical companions. "
                    "No translations are added.",
                    "双语映射无效、不完整，或缺少有效的结构化配套文件而无法完整校验。系统不会补写译文。",
                )
        if complete:
            issue(
                "complete_current_bundle",
                "All required supplied companions pass structural checks. "
                "This does not establish factual truth or translation fidelity, "
                "and archives stay inactive.",
                "提供的全部必需配套文件通过结构检查。这不证明事实或翻译准确，归档仍不会被启用。",
            )
        else:
            issue(
                "invalid_current_bundle",
                "The supplied files are not a complete validated current "
                "bundle. They remain an archive for review, not a converted or selectable report.",
                "所提供文件不是完整有效的当前报告组合。它们仅作为复核归档保留，不是已转换或可启用的报告。",
            )
    presence = {
        item.label: {"present": item.present, "size_bytes": item.size_bytes, "sha256": item.sha256}
        for item in files
    }
    digest = _hash(_encode(presence))
    inspection = LegacyInspection(
        kind=kind, source_digest=digest, format=detected, files=files, issues=issues
    )
    en = (
        "Legacy report archive preview — preservation only\n\n"
        + "\n".join(item.message_en for item in issues)
        + "\n\nFiles (fixed labels; missing files remain missing):\n"
        + "\n".join(
            f"{item.label}: {str(item.present).lower()}, {item.size_bytes} bytes" for item in files
        )
    )
    zh = (
        "旧报告归档预览——仅保留原始内容\n\n"
        + "\n".join(item.message_zh for item in issues)
        + "\n\n文件（固定名称；缺失的文件仍保持缺失）：\n"
        + "\n".join(
            f"{item.label}：{'存在' if item.present else '缺失'}，{item.size_bytes} 字节"
            for item in files
        )
    )
    fields = {
        **inspection.model_dump(mode="json"),
        "field_ledger": [entry.model_dump(mode="json") for entry in ledger],
        "review_text_en": en,
        "review_text_zh": zh,
    }
    preview = LegacyArchivePreview(**fields, preview_digest=_hash(_encode(fields)))
    payload = {label: raw for label, raw in sources.items() if raw is not None}
    payload["preview.json"] = _encode(preview.model_dump(mode="json"))
    if len(payload["preview.json"]) > MAX_PREVIEW_BYTES:
        raise ValueError("preview byte limit")
    return inspection, preview, payload


class LegacyReportService:
    @_safe
    def __init__(self, vault_dir: Path):
        self._io = ReportReviewService(vault_dir)

    def _root(self, kind):
        return self._io._vault / "reports" / "legacy_archives" / self._io._kind(kind)

    def _optional(self, path):
        # Missing members are data, but unsafe/missing ancestors cannot mask a link.
        for directory in reversed(path.parents):
            if not directory.is_relative_to(self._io._vault):
                continue
            try:
                directory.lstat()
            except FileNotFoundError:
                self._io._check(directory.parent, directory=True)
                return None
            self._io._check(directory, directory=True)
        try:
            path.lstat()
        except FileNotFoundError:
            self._io._check(path.parent, directory=True)
            return None
        return self._io._read(path, MAX_FILE_BYTES)

    def _current(self, kind):
        kind = self._io._kind(kind)
        reports = self._io._vault / "reports"
        sources, total = {}, 0
        for label in _MEMBERS[kind]:
            raw = self._optional(reports / label)
            total += len(raw) if raw is not None else 0
            if total > MAX_BUNDLE_BYTES:
                raise ValueError("source byte limit")
            sources[label] = raw
        if any(self._optional(reports / label) != raw for label, raw in sources.items()):
            raise ValueError("source changed during read")
        return _build(kind, sources)

    @_safe
    def inspect(self, kind: ReportKind) -> LegacyInspection:
        return self._current(kind)[0]

    @_safe
    def preview_archive(self, kind: ReportKind, *, expected_digest: str) -> LegacyArchivePreview:
        if type(expected_digest) is not str or not _DIGEST.fullmatch(expected_digest):
            raise ValueError("invalid digest")
        _, preview, _ = self._current(kind)
        if preview.source_digest != expected_digest or preview.format == "missing":
            raise ValueError("stale or absent source")
        return preview

    def _verified(self, directory, kind, identifier):
        files = self._io._entries(directory)
        sizes = {path.name: self._io._check(path, directory=False).st_size for path in files}
        if sum(sizes.values()) > MAX_ARCHIVE_BYTES:
            raise ValueError("archive size limit")
        manifest = _Manifest.model_validate(
            _decode(self._io._read(directory / "manifest.json", MAX_MANIFEST_BYTES))
        )
        if (
            manifest.id != identifier
            or manifest.kind != kind
            or manifest.manifest_digest
            != _hash(_encode(manifest.model_dump(mode="json", exclude={"manifest_digest"})))
            or set(sizes) != set(manifest.files) | {"manifest.json"}
            or "preview.json" not in manifest.files
            or not set(manifest.files) <= set(_MEMBERS[kind]) | {"preview.json"}
        ):
            raise ValueError("invalid archive manifest")
        payload = {
            name: self._io._read(
                directory / name, MAX_PREVIEW_BYTES if name == "preview.json" else MAX_FILE_BYTES
            )
            for name in manifest.files
        }
        if any(_hash(raw) != manifest.files[name] for name, raw in payload.items()):
            raise ValueError("archive checksum mismatch")
        _, preview, rebuilt = _build(kind, {label: payload.get(label) for label in _MEMBERS[kind]})
        archive_digest = _hash(_encode({name: _hash(raw) for name, raw in rebuilt.items()}))
        if (
            rebuilt != payload
            or preview.format == "missing"
            or manifest.source_digest != preview.source_digest
            or manifest.preview_digest != preview.preview_digest
            or manifest.archive_digest != archive_digest
        ):
            raise ValueError("archive derivation mismatch")
        saved = SavedLegacyArchive(
            id=identifier,
            kind=kind,
            created_at=manifest.created_at,
            source_digest=preview.source_digest,
            archive_digest=archive_digest,
            directory_path=str(directory),
        )
        return saved, preview, payload, sum(sizes.values())

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
        if len(entries) > MAX_ARCHIVES * 2 + 1:
            raise ValueError("archive entry limit")
        saved, total = [], 0
        for folder in entries:
            if folder.name == ".writer.lock":
                if self._io._check(folder, directory=False).st_size > 1:
                    raise ValueError("invalid lock")
                continue
            if self._io._is_pending_entry(folder):
                continue
            self._io._check(folder, directory=True)
            if not _ID.fullmatch(folder.name) or len(saved) >= MAX_ARCHIVES:
                raise ValueError("invalid archive entry")
            size = sum(
                self._io._check(path, directory=False).st_size for path in self._io._entries(folder)
            )
            if total + size > MAX_HISTORY_BYTES:
                raise ValueError("archive history byte limit")
            record, _, _, verified_size = self._verified(folder, kind, folder.name)
            total += verified_size
            saved.append(record)
        return sorted(saved, key=lambda item: (item.created_at, item.id)), total

    @_safe
    def list_archives(self, kind: ReportKind) -> list[SavedLegacyArchive]:
        return self._history(self._io._kind(kind))[0]

    def _read(self, kind, identifier):
        kind = self._io._kind(kind)
        if type(identifier) is not str or not _ID.fullmatch(identifier):
            raise ValueError("invalid archive id")
        return self._verified(self._root(kind) / identifier, kind, identifier)

    @_safe
    def read_archive(self, kind: ReportKind, identifier: str) -> LegacyArchivePreview:
        return self._read(kind, identifier)[1]

    @_safe
    def read_snapshot(self, kind: ReportKind, identifier: str, file_label: str) -> bytes:
        kind = self._io._kind(kind)
        if type(file_label) is not str or file_label not in _MEMBERS[kind]:
            raise ValueError("invalid snapshot label")
        return self._read(kind, identifier)[2][file_label]

    @_safe
    def save_archive(self, preview: LegacyArchivePreview, *, confirmed: bool) -> SavedLegacyArchive:
        if confirmed is not True or not isinstance(preview, LegacyArchivePreview):
            raise ValueError("explicit confirmation required")
        preview = LegacyArchivePreview.model_validate(
            preview.model_dump(mode="json", warnings=False)
        )
        _, current, payload = self._current(preview.kind)
        if current != preview or current.format == "missing":
            raise ValueError("modified or stale preview")
        self._history(preview.kind)
        root = self._root(preview.kind)
        self._io._mkdir(root.parent)
        self._io._mkdir(root)
        with self._io._writer(root):
            records, total = self._history(preview.kind)
            _, current, payload = self._current(preview.kind)
            if current != preview:
                raise ValueError("source changed")
            identifier = uuid4().hex
            digest = _hash(_encode({name: _hash(raw) for name, raw in payload.items()}))
            fields = {
                "schema_version": "0.1",
                "operation": "legacy_archive",
                "id": identifier,
                "kind": preview.kind,
                "created_at": datetime.now(UTC).isoformat(),
                "source_digest": preview.source_digest,
                "archive_digest": digest,
                "preview_digest": preview.preview_digest,
                "files": {name: _hash(raw) for name, raw in payload.items()},
            }
            manifest = _Manifest(**fields, manifest_digest=_hash(_encode(fields)))
            payload["manifest.json"] = _encode(manifest.model_dump(mode="json"))
            size = sum(map(len, payload.values()))
            if (
                len(records) >= MAX_ARCHIVES
                or size > MAX_ARCHIVE_BYTES
                or total + size > MAX_HISTORY_BYTES
            ):
                raise ValueError("archive history limit")
            stage, final = root / f".pending-{identifier}", root / identifier
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            stage.mkdir(mode=0o700)
            self._io._check(stage, directory=True)
            for label, raw in payload.items():
                self._io._write_new(stage / label, raw)
            self._verified(stage, preview.kind, identifier)
            if self._current(preview.kind)[1] != preview:
                raise ValueError("source presence or bytes changed during save")
            self._io._check(root, directory=True)
            self._io._check(stage, directory=True)
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            os.rename(stage, final)
            return SavedLegacyArchive(
                id=identifier,
                kind=preview.kind,
                created_at=manifest.created_at,
                source_digest=preview.source_digest,
                archive_digest=digest,
                directory_path=str(final),
            )
