"""Explicit local report selection without overwriting any report or reviewed copy.

The append-only journal commits one small directory atomically. Selected reports
remain generated, unverified reference material, never original owner evidence.
Checksums detect corruption, not a hostile process with the same filesystem access.
"""

from __future__ import annotations

import os
import re
import stat
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from anti_dating_scam.reports.local_artifacts import MAX_ARTIFACT_BYTES, validate_local_artifact
from anti_dating_scam.reports.localized_reports import (
    render_localized_reports,
    validate_localization,
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
    _unsafe,
)
from anti_dating_scam.services.report_revisions import MAX_RENDER_BYTES, ReportRevisionService

MAX_SELECTIONS = 1_000
MAX_EVENT_BYTES = 8_000
MAX_JOURNAL_BYTES = 8_000_000
NO_SELECTION = "0" * 64
_ID = re.compile(r"^[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ERROR = (
    "The report selection cannot be verified. Refresh and deliberately select a valid report. "
    "A damaged selection journal requires separate recovery; it is not replaced automatically. "
    "/ 无法校验报告选择，请刷新并明确选择有效报告。损坏的选择记录需要单独恢复，系统不会自动替换。"
)
_REVIEW_ONLY = (
    "Report references are disabled by your explicit choice. Original files and archives "
    "remain available for literal review. Select a verified conversion or regenerate and "
    "explicitly select a current report before using report references. "
    "/ 你已明确停用报告参考。原文件和存档仍可按原文复核。请先选择已校验的转换报告，"
    "或重新生成并明确选择当前报告，再使用报告参考。"
)


class ActiveReportError(ValueError):
    """Safe bilingual selection error, without report data or filesystem paths."""


class LegacyReviewOnlyError(ActiveReportError):
    """An explicit disabled state, never permission to fall back to legacy bytes."""


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class SelectionState(_Model):
    kind: ReportKind
    selection_version: Digest
    revision_id: RecordID | None
    selected_at: str | None


class SelectionPreview(_Model):
    kind: ReportKind
    revision_id: RecordID | None
    previous_selection_version: Digest
    generated_bundle_digest: Digest
    target_bundle_digest: Digest
    markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)]
    detailed_markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)] | None
    preview_digest: Digest


class ResolvedReport(_Model):
    kind: ReportKind
    revision_id: RecordID | None
    selection_version: Digest
    content_digest: Digest
    canonical: dict
    localized_text: list[dict]
    markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)]
    detailed_markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)] | None


class ConversionSelectionState(SelectionState):
    target_kind: Literal["legacy_conversion"] = "legacy_conversion"
    conversion_id: RecordID


class ReviewOnlySelectionState(SelectionState):
    target_kind: Literal["legacy_review_only"] = "legacy_review_only"


class ConvertedResolvedReport(ResolvedReport):
    target_kind: Literal["legacy_conversion"] = "legacy_conversion"
    conversion_id: RecordID


class ConversionSelectionPreview(_Model):
    kind: ReportKind
    conversion_id: RecordID
    previous_selection_version: Digest
    source_digest: Digest
    integrity_digest: Digest
    target_bundle_digest: Digest
    markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)]
    detailed_markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)] | None
    preview_digest: Digest


class ReviewOnlySelectionPreview(_Model):
    kind: ReportKind
    previous_selection_version: Digest
    markdown: Annotated[str, Field(min_length=1, max_length=MAX_RENDER_BYTES)]
    detailed_markdown: None = None
    preview_digest: Digest


class _Event(_Model):
    schema_version: Literal["0.1"]
    id: RecordID
    sequence: Annotated[int, Field(ge=1, le=MAX_SELECTIONS)]
    kind: ReportKind
    revision_id: RecordID | None
    previous_selection_version: Digest
    generated_bundle_digest: Digest
    target_bundle_digest: Digest
    preview_digest: Digest
    selected_at: Annotated[str, Field(min_length=1, max_length=40)]
    event_digest: Digest

    @field_validator("selected_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        return CorrectionRecord.valid_timestamp(value)


class _NewEvent(_Model):
    schema_version: Literal["0.2"]
    id: RecordID
    sequence: Annotated[int, Field(ge=1, le=MAX_SELECTIONS)]
    kind: ReportKind
    previous_selection_version: Digest
    preview_digest: Digest
    selected_at: Annotated[str, Field(min_length=1, max_length=40)]
    event_digest: Digest

    @field_validator("selected_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        return CorrectionRecord.valid_timestamp(value)


class _ConversionEvent(_NewEvent):
    target_kind: Literal["legacy_conversion"]
    conversion_id: RecordID
    source_digest: Digest
    integrity_digest: Digest
    target_bundle_digest: Digest


class _ReviewOnlyEvent(_NewEvent):
    target_kind: Literal["legacy_review_only"]


def _parse_event(raw):
    payload = _decode(raw)
    if payload.get("schema_version") == "0.1":
        return _Event.model_validate(payload)
    if payload.get("schema_version") == "0.2":
        model = {
            "legacy_conversion": _ConversionEvent,
            "legacy_review_only": _ReviewOnlyEvent,
        }.get(payload.get("target_kind"))
        if model is not None:
            return model.model_validate(payload)
    raise ValueError("unsupported selection event")


def _safe(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except LegacyReviewOnlyError:
            raise
        except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError):
            raise ActiveReportError(_ERROR) from None

    return wrapped


def _revision_id(value):
    if value is not None and (type(value) is not str or not _ID.fullmatch(value)):
        raise ValueError("invalid revision identifier")
    return value


class ActiveReportService:
    """One captured vault. Reads are side-effect free; selection requires exact consent."""

    @_safe
    def __init__(self, vault_dir: Path):
        self._vault = Path(os.path.abspath(os.fspath(vault_dir)))
        self._directory_exists(self._vault)

    @staticmethod
    def _directory_exists(path: Path) -> bool:
        # A pristine missing vault is allowed, but every existing ancestor must be safe.
        for node in (*reversed(path.parents), path):
            try:
                info = node.lstat()
            except FileNotFoundError:
                return False
            if _unsafe(info) or not stat.S_ISDIR(info.st_mode):
                raise ValueError("unsafe directory")
        if path.resolve(strict=True) != path:
            raise ValueError("unsafe directory")
        return True

    def _io(self) -> ReportReviewService:
        return ReportReviewService(self._vault)

    def _root(self, kind: str) -> Path:
        return self._vault / "reports" / "active_selections" / ReportReviewService._kind(kind)

    def _history(self, kind: str):
        root = self._root(kind)
        if not self._directory_exists(root):
            return [], NO_SELECTION
        io = self._io()
        entries = io._entries(root)
        if len(entries) > MAX_SELECTIONS * 2 + 1:
            raise ValueError("selection entry limit")
        events, total = [], 0
        for directory in entries:
            if directory.name == ".writer.lock":
                if io._check(directory, directory=False).st_size > 1:
                    raise ValueError("invalid lock")
                continue
            if io._is_pending_entry(directory):
                continue
            io._check(directory, directory=True)
            if not _ID.fullmatch(directory.name) or len(events) >= MAX_SELECTIONS:
                raise ValueError("invalid selection entry")
            files = io._entries(directory)
            if {path.name for path in files} != {"selection.json"}:
                raise ValueError("invalid selection transaction")
            path = directory / "selection.json"
            total += io._check(path, directory=False).st_size
            if total > MAX_JOURNAL_BYTES:
                raise ValueError("journal byte limit")
            raw = io._read(path, MAX_EVENT_BYTES)
            event = _parse_event(raw)
            if (
                event.id != directory.name
                or event.kind != kind
                or raw != _encode(event.model_dump(mode="json"))
                or event.event_digest
                != _hash(_encode(event.model_dump(mode="json", exclude={"event_digest"})))
            ):
                raise ValueError("invalid selection checksum")
            events.append((event, _hash(raw)))
        events.sort(key=lambda item: item[0].sequence)
        previous = NO_SELECTION
        for index, (event, version) in enumerate(events, 1):
            if event.sequence != index or event.previous_selection_version != previous:
                raise ValueError("broken selection chain")
            previous = version
        return events, previous

    @staticmethod
    def _state(kind, events, version):
        event = events[-1][0] if events else None
        common = {
            "kind": kind, "selection_version": version, "revision_id": None,
            "selected_at": event.selected_at if event else None,
        }
        if isinstance(event, _ConversionEvent):
            return ConversionSelectionState(**common, conversion_id=event.conversion_id)
        if isinstance(event, _ReviewOnlyEvent):
            return ReviewOnlySelectionState(**common)
        return SelectionState(
            kind=kind,
            selection_version=version,
            revision_id=event.revision_id if event else None,
            selected_at=event.selected_at if event else None,
        )

    @_safe
    def get_selection(self, kind: ReportKind) -> SelectionState:
        events, version = self._history(kind)
        return self._state(kind, events, version)

    def _generated(self, kind: str):
        io = self._io()
        root = self._vault / "reports"
        paths = {
            "source_report.json": root / f"{kind}.json",
            "source_localization.json": root / f"{kind}_localization.json",
        }
        if kind == "mate_criteria":
            paths["source_ideal_profiles.json"] = root / "ideal_partner_profiles.json"
        raw = {name: io._read(path, MAX_ARTIFACT_BYTES) for name, path in paths.items()}
        canonical = {
            "report" if kind == "self_portrait" else "criteria": validate_local_artifact(
                _decode(raw["source_report.json"]), kind
            )
        }
        if kind == "mate_criteria":
            canonical["ideal_profiles"] = validate_local_artifact(
                _decode(raw["source_ideal_profiles.json"]), "ideal_profiles"
            )
        companion = _decode(raw["source_localization.json"])
        if (
            set(companion) != {"schema_version", "localized_text"}
            or companion["schema_version"] != "0.1"
        ):
            raise ValueError("invalid companion")
        entries = companion["localized_text"]
        validate_localization(kind, canonical, entries)
        rendered = render_localized_reports(kind, canonical, entries)
        data = {
            "canonical": canonical,
            "localized_text": entries,
            "markdown": rendered["markdown"],
            "detailed_markdown": rendered.get("detailed_markdown"),
        }
        if any(len(value.encode("utf-8")) > MAX_RENDER_BYTES for value in rendered.values()):
            raise ValueError("render size limit")
        # Catch a normal regeneration between reading companion files; no mixed tuple escapes.
        if any(io._read(path, MAX_ARTIFACT_BYTES) != raw[name] for name, path in paths.items()):
            raise ValueError("source changed during read")
        hashes = {name: _hash(value) for name, value in raw.items()}
        return hashes, data

    def _target(self, kind: str, revision_id: str | None):
        kind = ReportReviewService._kind(kind)
        _revision_id(revision_id)
        generated_hashes, data = self._generated(kind)
        generated_digest = _hash(_encode(generated_hashes))
        integrity = None
        if revision_id is not None:
            bundle = ReportRevisionService(self._vault).read_verified_bundle(kind, revision_id)
            if bundle.source_file_digests != generated_hashes:
                raise ValueError("copy belongs to an older generated bundle")
            data = bundle.model_dump(
                include={"canonical", "localized_text", "markdown", "detailed_markdown"},
                mode="json",
            )
            integrity = bundle.integrity_digest
            # Copy verification may scan many immutable snapshots. A regeneration
            # during that scan must not leave a preview using an older source tuple.
            if self._generated(kind)[0] != generated_hashes:
                raise ValueError("source changed while verifying copy")
        target_digest = _hash(
            _encode(
                {
                    "kind": kind,
                    "revision_id": revision_id,
                    "generated_bundle_digest": generated_digest,
                    "copy_integrity_digest": integrity,
                    "bundle": data,
                }
            )
        )
        return generated_digest, target_digest, data

    def _conversion_target(self, kind: str, conversion_id: str):
        # This is deliberately separate from _target: old original/revision
        # selections still require current canonical source files.
        from anti_dating_scam.services.legacy_conversions import LegacyConversionService
        from anti_dating_scam.services.legacy_reports import LegacyReportService

        kind = ReportReviewService._kind(kind)
        if _revision_id(conversion_id) is None:
            raise ValueError("conversion identifier required")
        originals = LegacyReportService(self._vault)
        before = originals.inspect(kind).source_digest
        bundle = LegacyConversionService(self._vault).read_verified_bundle(kind, conversion_id)
        if (
            bundle.kind != kind or bundle.conversion_id != conversion_id
            or bundle.source_digest != before
        ):
            raise ValueError("conversion belongs to an older source bundle")
        data = bundle.model_dump(
            include={"canonical", "localized_text", "markdown", "detailed_markdown"},
            mode="json",
        )
        if originals.inspect(kind).source_digest != before:
            raise ValueError("source changed while verifying conversion")
        target_digest = _hash(_encode({
            "kind": kind,
            "target_kind": "legacy_conversion",
            "conversion_id": conversion_id,
            "source_digest": before,
            "integrity_digest": bundle.integrity_digest,
            "bundle": data,
        }))
        return before, bundle.integrity_digest, target_digest, data

    def _expected_history(self, kind, expected_version):
        if type(expected_version) is not str or not _DIGEST.fullmatch(expected_version):
            raise ValueError("invalid expected version")
        _, version = self._history(kind)
        if version != expected_version:
            raise ValueError("selection changed")
        return version

    @staticmethod
    def _conversion_fields(kind, conversion_id, version, source, integrity, target, data):
        return {
            "kind": kind,
            "conversion_id": conversion_id,
            "previous_selection_version": version,
            "source_digest": source,
            "integrity_digest": integrity,
            "target_bundle_digest": target,
            "markdown": data["markdown"],
            "detailed_markdown": data["detailed_markdown"],
        }

    def _preview_conversion(self, kind, conversion_id, expected_version):
        version = self._expected_history(kind, expected_version)
        source, integrity, target, data = self._conversion_target(kind, conversion_id)
        fields = self._conversion_fields(
            kind, conversion_id, version, source, integrity, target, data,
        )
        if self._history(kind)[1] != version:
            raise ValueError("selection changed during preview")
        return ConversionSelectionPreview(**fields, preview_digest=_hash(_encode(fields)))

    @_safe
    def preview_conversion_selection(
        self, kind: ReportKind, conversion_id: str, *, expected_selection_version: str,
    ) -> ConversionSelectionPreview:
        return self._preview_conversion(kind, conversion_id, expected_selection_version)

    @staticmethod
    def _review_only_fields(kind, version):
        return {
            "kind": kind,
            "previous_selection_version": version,
            "markdown": _REVIEW_ONLY,
            "detailed_markdown": None,
        }

    def _preview_review_only(self, kind, expected_version):
        kind = ReportReviewService._kind(kind)
        version = self._expected_history(kind, expected_version)
        fields = self._review_only_fields(kind, version)
        return ReviewOnlySelectionPreview(**fields, preview_digest=_hash(_encode(fields)))

    @_safe
    def preview_legacy_review_only(
        self, kind: ReportKind, *, expected_selection_version: str,
    ) -> ReviewOnlySelectionPreview:
        # No damaged target or original needs to be read to disable references.
        return self._preview_review_only(kind, expected_selection_version)

    def _preview(self, kind, revision_id, expected_version):
        if type(expected_version) is not str or not _DIGEST.fullmatch(expected_version):
            raise ValueError("invalid expected version")
        _, version = self._history(kind)
        if version != expected_version:
            raise ValueError("selection changed")
        generated_digest, target_digest, data = self._target(kind, revision_id)
        fields = {
            "kind": kind,
            "revision_id": revision_id,
            "previous_selection_version": version,
            "generated_bundle_digest": generated_digest,
            "target_bundle_digest": target_digest,
            "markdown": data["markdown"],
            "detailed_markdown": data["detailed_markdown"],
        }
        if self._history(kind)[1] != version:
            raise ValueError("selection changed during preview")
        return SelectionPreview(**fields, preview_digest=_hash(_encode(fields)))

    @_safe
    def preview_selection(
        self, kind: ReportKind, revision_id: str | None, *, expected_selection_version: str
    ) -> SelectionPreview:
        # Prior target is intentionally not loaded: a damaged copy can be deselected.
        return self._preview(kind, revision_id, expected_selection_version)

    @_safe
    def resolve(self, kind: ReportKind) -> ResolvedReport | None:
        events, version = self._history(kind)
        if not events:
            return None  # The ONLY default/legacy fallback signal.
        event = events[-1][0]
        if isinstance(event, _ReviewOnlyEvent):
            fields = self._review_only_fields(kind, event.previous_selection_version)
            if (
                _hash(_encode(fields)) != event.preview_digest
                or self._history(kind)[1] != version
            ):
                raise ValueError("disabled selection changed")
            raise LegacyReviewOnlyError(_REVIEW_ONLY)
        if isinstance(event, _ConversionEvent):
            source, integrity, target, data = self._conversion_target(kind, event.conversion_id)
            fields = self._conversion_fields(
                kind, event.conversion_id, event.previous_selection_version,
                source, integrity, target, data,
            )
            if (
                source != event.source_digest or integrity != event.integrity_digest
                or target != event.target_bundle_digest
                or _hash(_encode(fields)) != event.preview_digest
                or self._history(kind)[1] != version
            ):
                raise ValueError("selected conversion changed")
            return ConvertedResolvedReport(
                kind=kind, revision_id=None, conversion_id=event.conversion_id,
                selection_version=version, content_digest=target, **data,
            )
        generated_digest, target_digest, data = self._target(kind, event.revision_id)
        preview_fields = {
            "kind": kind,
            "revision_id": event.revision_id,
            "previous_selection_version": event.previous_selection_version,
            "generated_bundle_digest": generated_digest,
            "target_bundle_digest": target_digest,
            "markdown": data["markdown"],
            "detailed_markdown": data["detailed_markdown"],
        }
        if (
            generated_digest != event.generated_bundle_digest
            or target_digest != event.target_bundle_digest
            or _hash(_encode(preview_fields)) != event.preview_digest
            or self._history(kind)[1] != version
        ):
            raise ValueError("selected report changed")
        return ResolvedReport(
            kind=kind,
            revision_id=event.revision_id,
            selection_version=version,
            content_digest=target_digest,
            **data,
        )

    @_safe
    def select(self, preview: SelectionPreview, *, confirmed: bool) -> SelectionState:
        if confirmed is not True or not isinstance(preview, SelectionPreview):
            raise ValueError("explicit confirmation required")
        preview = SelectionPreview.model_validate(preview.model_dump(mode="json"))
        if (
            self._preview(preview.kind, preview.revision_id, preview.previous_selection_version)
            != preview
        ):
            raise ValueError("modified or stale preview")
        io = self._io()
        root = self._root(preview.kind)
        io._mkdir(root.parent)
        io._mkdir(root)
        with io._writer(root):
            events, version = self._history(preview.kind)
            if (
                self._preview(preview.kind, preview.revision_id, preview.previous_selection_version)
                != preview
            ):
                raise ValueError("modified or stale preview")
            # Reserve the last slot to return to current generated report, without deleting history.
            if len(events) >= MAX_SELECTIONS or (
                preview.revision_id is not None and len(events) >= MAX_SELECTIONS - 1
            ):
                raise ValueError("selection history limit")
            identifier = uuid4().hex
            fields = {
                "schema_version": "0.1",
                "id": identifier,
                "sequence": len(events) + 1,
                "kind": preview.kind,
                "revision_id": preview.revision_id,
                "previous_selection_version": version,
                "generated_bundle_digest": preview.generated_bundle_digest,
                "target_bundle_digest": preview.target_bundle_digest,
                "preview_digest": preview.preview_digest,
                "selected_at": datetime.now(UTC).isoformat(),
            }
            event = _Event(**fields, event_digest=_hash(_encode(fields)))
            raw = _encode(event.model_dump(mode="json"))
            prior_bytes = sum(len(_encode(item.model_dump(mode="json"))) for item, _ in events)
            if len(raw) > MAX_EVENT_BYTES or prior_bytes + len(raw) > MAX_JOURNAL_BYTES:
                raise ValueError("event size limit")
            stage, final = root / f".pending-{identifier}", root / identifier
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            stage.mkdir(mode=0o700)
            io._check(stage, directory=True)
            io._write_new(stage / "selection.json", raw)
            if io._read(stage / "selection.json", MAX_EVENT_BYTES) != raw:
                raise ValueError("staged selection changed")
            if (
                self._preview(preview.kind, preview.revision_id, preview.previous_selection_version)
                != preview
            ):
                raise ValueError("source or target changed during selection")
            io._check(root, directory=True)
            io._check(stage, directory=True)
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            os.rename(stage, final)
            return self._state(preview.kind, [(event, _hash(raw))], _hash(raw))

    def _repreview_new(self, preview):
        if isinstance(preview, ConversionSelectionPreview):
            return self._preview_conversion(
                preview.kind, preview.conversion_id, preview.previous_selection_version,
            )
        return self._preview_review_only(preview.kind, preview.previous_selection_version)

    def _select_new(self, preview, confirmed, model):
        if confirmed is not True or not isinstance(preview, model):
            raise ValueError("explicit confirmation required")
        preview = model.model_validate(preview.model_dump(mode="json", warnings=False))
        if self._repreview_new(preview) != preview:
            raise ValueError("modified or stale preview")
        io = self._io()
        root = self._root(preview.kind)
        io._mkdir(root.parent.parent)
        io._mkdir(root.parent)
        io._mkdir(root)
        with io._writer(root):
            events, version = self._history(preview.kind)
            if self._repreview_new(preview) != preview:
                raise ValueError("modified or stale preview")
            conversion = isinstance(preview, ConversionSelectionPreview)
            # Keep the final slot for current originals or explicit reference disabling.
            if len(events) >= MAX_SELECTIONS or (conversion and len(events) >= MAX_SELECTIONS - 1):
                raise ValueError("selection history limit")
            identifier = uuid4().hex
            fields = {
                "schema_version": "0.2", "id": identifier, "sequence": len(events) + 1,
                "kind": preview.kind, "previous_selection_version": version,
                "preview_digest": preview.preview_digest,
                "selected_at": datetime.now(UTC).isoformat(),
                "target_kind": "legacy_conversion" if conversion else "legacy_review_only",
            }
            if conversion:
                fields.update({
                    "conversion_id": preview.conversion_id, "source_digest": preview.source_digest,
                    "integrity_digest": preview.integrity_digest,
                    "target_bundle_digest": preview.target_bundle_digest,
                })
            event_model = _ConversionEvent if conversion else _ReviewOnlyEvent
            event = event_model(**fields, event_digest=_hash(_encode(fields)))
            raw = _encode(event.model_dump(mode="json"))
            prior_bytes = sum(len(_encode(item.model_dump(mode="json"))) for item, _ in events)
            if len(raw) > MAX_EVENT_BYTES or prior_bytes + len(raw) > MAX_JOURNAL_BYTES:
                raise ValueError("event size limit")
            stage, final = root / f".pending-{identifier}", root / identifier
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            stage.mkdir(mode=0o700)
            io._check(stage, directory=True)
            io._write_new(stage / "selection.json", raw)
            if io._read(stage / "selection.json", MAX_EVENT_BYTES) != raw:
                raise ValueError("staged selection changed")
            if self._repreview_new(preview) != preview:
                raise ValueError("source or target changed during selection")
            io._check(root, directory=True)
            io._check(stage, directory=True)
            if final.exists() or final.is_symlink():
                raise ValueError("identifier collision")
            os.rename(stage, final)
            return self._state(preview.kind, [(event, _hash(raw))], _hash(raw))

    @_safe
    def select_conversion(
        self, preview: ConversionSelectionPreview, *, confirmed: bool,
    ) -> ConversionSelectionState:
        return self._select_new(preview, confirmed, ConversionSelectionPreview)

    @_safe
    def select_review_only(
        self, preview: ReviewOnlySelectionPreview, *, confirmed: bool,
    ) -> ReviewOnlySelectionState:
        return self._select_new(preview, confirmed, ReviewOnlySelectionPreview)
