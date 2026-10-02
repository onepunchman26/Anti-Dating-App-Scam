"""Local, append-only user annotations bound to exact canonical report bytes.

No provider calls, evidence promotion, export, or edits to canonical reports occur.
Checksums detect corruption, not a malicious process with the same filesystem access.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from anti_dating_scam.reports.local_artifacts import (
    MAX_ARTIFACT_BYTES,
    Claim,
    Text,
    validate_local_artifact,
)

ReportKind = Literal["self_portrait", "mate_criteria"]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
RecordID = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
TargetPath = Annotated[str, Field(pattern=r"^/(claims|stated|revealed)/(0|[1-9][0-9]{0,2})$")]
MAX_RECORD_BYTES = 120_000  # Published character bounds also fit JSON escape expansion.
MAX_RECORDS = 1_000
MAX_HISTORY_BYTES = 32_000_000
_KINDS = {"self_portrait", "mate_criteria"}
_ID = re.compile(r"^[0-9a-f]{32}$")
_PENDING = re.compile(r"^\.pending-[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_POINTER = re.compile(r"^/(claims|stated|revealed)/(0|[1-9][0-9]{0,2})$")
_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


class ReportReviewError(ValueError):
    """Safe public error; never embeds paths, report content or rejected input."""


class _ResolvedPathChanged(ReportReviewError):
    """Carry private identity evidence for the narrowly permitted staging rename."""

    def __init__(self, resolved: Path, before: os.stat_result):
        super().__init__("Unsafe report path. / 报告路径不安全。")
        self.resolved = resolved
        self.before = before


class ReviewClaim(Claim):
    path: TargetPath


class _ReviewModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ReviewDocument(_ReviewModel):
    kind: ReportKind
    report_digest: Digest
    claims: Annotated[list[ReviewClaim], Field(max_length=100)]
    caveats: Annotated[list[Text], Field(min_length=1, max_length=30)]


class CorrectionRecord(_ReviewModel):
    id: RecordID
    kind: ReportKind
    report_digest: Digest
    target_path: TargetPath
    original_claim: Text
    correction_text: Text
    reason: Annotated[str, Field(min_length=1, max_length=2_000, pattern=r"\S")]
    created_at: Annotated[str, Field(min_length=1, max_length=40)]

    @field_validator("created_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
            raise ValueError("UTC timestamp required")
        return value


class _Envelope(_ReviewModel):
    schema_version: Literal["0.1"]
    record: CorrectionRecord
    record_digest: Digest


def _safe_errors(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ReportReviewError as exc:
            raise ReportReviewError(str(exc)) from None
        except (OSError, ValueError, TypeError, RecursionError, UnicodeError):
            raise ReportReviewError(
                "Report review could not be completed safely. Check the report and review history. "
                "/ 无法安全完成报告复核，请检查报告及复核记录。"
            ) from None

    return wrapped


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _encode(value: dict) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _decode(raw: bytes) -> dict:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("nonstandard JSON constant")

    result = json.loads(
        raw.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=invalid_constant
    )
    if not isinstance(result, dict):
        raise ValueError("object required")
    return result


def _unsafe(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
    )


class ReportReviewService:
    """Capture one vault identity; reads never follow source-label paths or create files."""

    @_safe_errors
    def __init__(self, vault_dir: Path):
        self._vault = Path(os.path.abspath(os.fspath(vault_dir)))
        self._check(self._vault, directory=True)

    def _check(self, path: Path, *, directory: bool) -> os.stat_result:
        if not path.is_relative_to(self._vault):
            raise ReportReviewError("Unsafe report path. / 报告路径不安全。")
        # Check every existing ancestor, including a symlink/junction vault root.
        for ancestor in reversed(path.parents):
            info = ancestor.lstat()
            if _unsafe(info) or not stat.S_ISDIR(info.st_mode):
                raise ReportReviewError("Unsafe report path. / 报告路径不安全。")
        info = path.lstat()
        expected = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
        if _unsafe(info) or not expected or (not directory and info.st_nlink != 1):
            raise ReportReviewError("Unsafe report path. / 报告路径不安全。")
        resolved = path.resolve(strict=True)
        if resolved != path:
            raise _ResolvedPathChanged(resolved, info)
        return info

    @staticmethod
    def _kind(kind: str) -> str:
        if type(kind) is not str or kind not in _KINDS:
            raise ReportReviewError("Unsupported report kind. / 不支持此报告类型。")
        return kind

    def _source(self, kind: str) -> Path:
        return self._vault / "reports" / f"{self._kind(kind)}.json"

    def _history(self, kind: str) -> Path:
        return self._vault / "reports" / "review_history" / self._kind(kind)

    def _read(self, path: Path, limit: int) -> bytes:
        before = self._check(path, directory=False)
        if before.st_size > limit:
            raise ReportReviewError(
                "Report review data exceeds its limit. / 复核数据超过大小限制。"
            )
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ValueError("file changed while opening")
            raw = bytearray()
            while len(raw) <= limit:
                part = os.read(descriptor, min(65_536, limit + 1 - len(raw)))
                if not part:
                    break
                raw.extend(part)
            after = os.fstat(descriptor)
            current = self._check(path, directory=False)
            if (
                len(raw) > limit
                or after.st_size != opened.st_size
                or after.st_mtime_ns != opened.st_mtime_ns
                or (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino)
            ):
                raise ValueError("file changed while reading")
            return bytes(raw)
        finally:
            os.close(descriptor)

    @staticmethod
    def _document(kind: str, raw: bytes) -> ReviewDocument:
        canonical = validate_local_artifact(_decode(raw), kind)
        groups = ("claims",) if kind == "self_portrait" else ("stated", "revealed")
        claims = [
            ReviewClaim(path=f"/{group}/{index}", **claim)
            for group in groups
            for index, claim in enumerate(canonical[group])
        ]
        return ReviewDocument(
            kind=kind, report_digest=_hash(raw), claims=claims, caveats=canonical["caveats"]
        )

    @_safe_errors
    def inspect(self, kind: ReportKind) -> ReviewDocument:
        return self._document(self._kind(kind), self._read(self._source(kind), MAX_ARTIFACT_BYTES))

    @staticmethod
    def _target(document: ReviewDocument, target_path: str) -> ReviewClaim:
        if type(target_path) is not str or not _POINTER.fullmatch(target_path):
            raise ReportReviewError("Invalid claim selection. / 主张选择无效。")
        for claim in document.claims:
            if claim.path == target_path:
                return claim
        raise ReportReviewError("The selected claim is unavailable. / 所选主张不存在。")

    def _entries(self, directory: Path) -> list[Path]:
        self._check(directory, directory=True)
        result = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if len(result) >= MAX_RECORDS * 2 + 1:
                    raise ValueError("too many history entries")
                result.append(Path(entry.path))
        return result

    def _is_pending_entry(self, path: Path) -> bool:
        """Ignore only safe uncommitted directories, including an in-flight commit.

        A directory listing can capture a staging name just before the writer
        atomically renames it. Revalidate the parent if that name vanished; a
        missing/unsafe parent, existing link or malformed pending file still fails.
        Committed entries and writer locks never use this exception.
        """
        if not _PENDING.fullmatch(path.name):
            return False
        try:
            self._check(path, directory=True)
        except _ResolvedPathChanged as changed:
            # Windows can open the staging directory and resolve its handle only
            # after the writer commits it. Accept exactly that same directory at
            # its corresponding committed sibling, never another resolved target.
            committed = path.with_name(path.name.removeprefix(".pending-"))
            if changed.resolved != committed:
                raise
            self._check(path.parent, directory=True)
            after = self._check(committed, directory=True)
            if (after.st_dev, after.st_ino) != (
                changed.before.st_dev, changed.before.st_ino
            ):
                raise
            try:
                path.lstat()
            except FileNotFoundError:
                pass
            else:
                # A surviving/recreated name (including a link) is not a rename.
                raise changed
        except FileNotFoundError:
            self._check(path.parent, directory=True)
        return True

    def _load_history(self, kind: str) -> tuple[list[CorrectionRecord], int]:
        history = self._history(kind)
        # lstat distinguishes a missing directory from a dangling symlink.
        try:
            history.lstat()
        except FileNotFoundError:
            for parent in (self._vault / "reports", history.parent):
                try:
                    parent.lstat()
                except FileNotFoundError:
                    break
                self._check(parent, directory=True)
            return [], 0
        records, total = [], 0
        for folder in self._entries(history):
            if folder.name == ".writer.lock":
                # Windows range locks also affect reads through another descriptor.
                if self._check(folder, directory=False).st_size > 1:
                    raise ValueError("invalid lock")
                continue
            if self._is_pending_entry(folder):
                # Interrupted uncommitted transactions are never visible annotations.
                continue
            self._check(folder, directory=True)
            if not _ID.fullmatch(folder.name) or len(records) >= MAX_RECORDS:
                raise ValueError("invalid history entry")
            files = self._entries(folder)
            if {file.name for file in files} != {"source.json", "correction.json"}:
                raise ValueError("incomplete history transaction")
            incoming_size = sum(self._check(file, directory=False).st_size for file in files)
            if total + incoming_size > MAX_HISTORY_BYTES:
                raise ValueError("history size exceeded")
            raw = self._read(folder / "source.json", MAX_ARTIFACT_BYTES)
            envelope_raw = self._read(folder / "correction.json", MAX_RECORD_BYTES)
            total += len(raw) + len(envelope_raw)
            if total > MAX_HISTORY_BYTES:
                raise ValueError("history size exceeded")
            envelope = _Envelope.model_validate(_decode(envelope_raw))
            record = envelope.record
            if (
                record.id != folder.name
                or record.kind != kind
                or envelope.record_digest != _hash(_encode(record.model_dump(mode="json")))
                or record.report_digest != _hash(raw)
            ):
                raise ValueError("history integrity mismatch")
            document = self._document(kind, raw)
            if self._target(document, record.target_path).claim != record.original_claim:
                raise ValueError("history target mismatch")
            records.append(record)
        return sorted(records, key=lambda record: (record.created_at, record.id)), total

    @_safe_errors
    def list_corrections(
        self, kind: ReportKind, report_digest: str | None = None
    ) -> list[CorrectionRecord]:
        self._kind(kind)
        if report_digest is not None and (
            type(report_digest) is not str or not _DIGEST.fullmatch(report_digest)
        ):
            raise ValueError("invalid digest")
        records, _ = self._load_history(kind)
        return [
            record
            for record in records
            if report_digest is None or record.report_digest == report_digest
        ]

    def _mkdir(self, path: Path) -> None:
        self._check(path.parent, directory=True)
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
        self._check(path, directory=True)

    @contextmanager
    def _writer(self, history: Path):
        key = str(history)
        with _LOCKS_GUARD:
            lock = _LOCKS.setdefault(key, threading.RLock())
        with lock:
            lock_path = history / ".writer.lock"
            flags = os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(lock_path, flags | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    os.write(descriptor, b"0")
                except OSError:
                    os.close(descriptor)
                    raise
            except FileExistsError:
                info = self._check(lock_path, directory=False)
                if info.st_size > 1:
                    raise ValueError("invalid lock") from None
                descriptor = os.open(lock_path, flags)
            acquired = False
            try:
                info = self._check(lock_path, directory=False)
                actual = os.fstat(descriptor)
                if (info.st_dev, info.st_ino) != (actual.st_dev, actual.st_ino):
                    raise ValueError("lock changed")
                deadline = time.monotonic() + 2
                while True:
                    try:
                        if os.name == "nt":
                            import msvcrt

                            os.lseek(descriptor, 0, os.SEEK_SET)
                            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                        else:
                            import fcntl

                            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        acquired = True
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise ReportReviewError(
                                "Another review is being saved. Try again. / "
                                "另一条复核正在保存，请重试。"
                            ) from None
                        time.sleep(0.01)
                yield
            finally:
                if acquired:
                    if os.name == "nt":
                        import msvcrt

                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def _write_new(self, path: Path, raw: bytes) -> None:
        self._check(path.parent, directory=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        with os.fdopen(os.open(path, flags, 0o600), "wb") as target:
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
        self._check(path, directory=False)

    @_safe_errors
    def record_correction(
        self,
        kind: ReportKind,
        *,
        expected_digest: str,
        target_path: str,
        correction_text: str,
        reason: str,
        confirmed: bool,
    ) -> CorrectionRecord:
        if confirmed is not True:
            raise ReportReviewError("Explicit confirmation is required. / 必须明确确认后才能保存。")
        kind = self._kind(kind)
        if type(expected_digest) is not str or not _DIGEST.fullmatch(expected_digest):
            raise ValueError("invalid digest")
        source_path = self._source(kind)
        raw = self._read(source_path, MAX_ARTIFACT_BYTES)
        document = self._document(kind, raw)
        if document.report_digest != expected_digest:
            raise ReportReviewError(
                "The report changed. Refresh and review again. / 报告已变化，请刷新后重新复核。"
            )
        claim = self._target(document, target_path)
        record = CorrectionRecord(
            id=uuid4().hex,
            kind=kind,
            report_digest=expected_digest,
            target_path=target_path,
            original_claim=claim.claim,
            correction_text=correction_text,
            reason=reason,
            created_at=datetime.now(UTC).isoformat(),
        )
        record_data = record.model_dump(mode="json")
        envelope = _encode(
            {
                "schema_version": "0.1",
                "record": record_data,
                "record_digest": _hash(_encode(record_data)),
            }
        )
        if len(envelope) > MAX_RECORD_BYTES:
            raise ValueError("record too large")
        self._load_history(kind)  # Reject corrupt history before creating any directories.
        history = self._history(kind)
        self._mkdir(history.parent)
        self._mkdir(history)
        with self._writer(history):
            records, total = self._load_history(kind)
            if len(records) >= MAX_RECORDS or total + len(raw) + len(envelope) > MAX_HISTORY_BYTES:
                raise ValueError("history limit reached")
            stage = history / f".pending-{record.id}"
            final = history / record.id
            # Exclusive creation; collisions never overwrite even an empty directory.
            if final.exists() or final.is_symlink():
                raise ValueError("record identifier collision")
            stage.mkdir(mode=0o700)
            self._check(stage, directory=True)
            self._write_new(stage / "source.json", raw)
            self._write_new(stage / "correction.json", envelope)
            if (
                self._read(stage / "source.json", MAX_ARTIFACT_BYTES) != raw
                or self._read(stage / "correction.json", MAX_RECORD_BYTES) != envelope
            ):
                raise ValueError("staged history changed")
            if self._read(source_path, MAX_ARTIFACT_BYTES) != raw:
                raise ReportReviewError(
                    "The report changed. Refresh and review again. / 报告已变化，请刷新后重新复核。"
                )
            self._check(history, directory=True)
            self._check(stage, directory=True)
            if final.exists() or final.is_symlink():
                raise ValueError("record identifier collision")
            # Both immutable files become visible as one committed directory.
            os.rename(stage, final)
        return record
