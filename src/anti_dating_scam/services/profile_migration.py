"""Explicit exact-byte migration from a flat profile to the current profile/ layout.

This changes only placement, never schema, wording, evidence or consent. Original
flat files remain untouched. The shared lock coordinates application writers;
filesystem checks are not a transaction against arbitrary noncooperating processes.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field

from anti_dating_scam.reports.schema_validator import load_schema
from anti_dating_scam.services.report_review import Digest, ReportReviewService, _encode, _hash

MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 4_000_000
_NAMES = ("profile.mpm.md", "profile.json")
_ERROR = (
    "The profile copy could not be safely verified or completed. Refresh and review again. "
    "Original flat files have not been replaced or removed. "
    "/ 无法安全校验或完成档案复制，请刷新后重新复核。原有平铺文件未被替换或删除。"
)


class ProfileMigrationError(ValueError):
    """A privacy-safe bilingual error with no submitted file content."""


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ProfileMigrationFile(_Model):
    filename: Literal["profile.mpm.md", "profile.json"]
    present: bool
    size_bytes: Annotated[int, Field(ge=0, le=MAX_FILE_BYTES)]
    sha256: Digest | None
    text: Annotated[str, Field(max_length=MAX_FILE_BYTES)] | None
    encoding: Literal["utf8", "binary", "missing"]


class ProfileMigrationIssue(_Model):
    code: Annotated[str, Field(min_length=1, max_length=80)]
    message_en: Annotated[str, Field(min_length=1, max_length=1_000)]
    message_zh: Annotated[str, Field(min_length=1, max_length=1_000)]


class ProfileMigrationPreview(_Model):
    vault_digest: Digest
    files: Annotated[list[ProfileMigrationFile], Field(min_length=2, max_length=2)]
    source_digest: Digest
    destination_state: Literal["absent", "empty", "occupied"]
    eligible: bool
    issues: Annotated[list[ProfileMigrationIssue], Field(max_length=20)]
    preview_digest: Digest


class MigrationResult(_Model):
    directory_path: str
    source_digest: Digest
    files: Annotated[
        list[Literal["profile.mpm.md", "profile.json"]], Field(min_length=1, max_length=2),
    ]


def _safe(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError):
            raise ProfileMigrationError(_ERROR) from None

    return wrapped


def _strict_json(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def invalid(_value):
        raise ValueError("nonfinite value")

    value = json.loads(
        raw.decode("utf-8-sig"), object_pairs_hook=unique, parse_constant=invalid,
    )
    if type(value) is not dict:
        raise ValueError("profile must be an object")
    # Also rejects overflowed JSON numbers and unpaired Unicode surrogates.
    _encode(value)
    validator = Draft202012Validator(load_schema("personal_profile.schema.json"))
    if not validator.is_valid(value):
        raise ValueError("profile schema mismatch")
    # jsonschema's optional date-time checker can silently be unavailable. Use
    # a bounded RFC3339 shape and the standard library for actual date validity.
    for field in ("created_at", "updated_at"):
        stamp = value[field]
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:[Zz]|[+-]\d{2}:\d{2})",
            stamp,
        ):
            raise ValueError("invalid timestamp")
        if stamp[-1].upper() != "Z" and (
            int(stamp[-5:-3]) > 23 or int(stamp[-2:]) > 59
        ):
            # fromisoformat normalizes offsets such as +00:60 to +01:00.
            raise ValueError("invalid timezone offset")
        datetime.fromisoformat(stamp.upper().replace("Z", "+00:00"))
    return value


class ProfileMigrationService:
    @_safe
    def __init__(self, vault_dir: Path):
        self._io = ReportReviewService(vault_dir)
        self._vault = self._io._vault
        root = self._io._check(self._vault, directory=True)
        self._identity = (root.st_dev, root.st_ino)
        self._vault_digest = _hash(_encode({
            "path": str(self._vault), "device": root.st_dev, "inode": root.st_ino,
        }))

    def _check_root(self):
        current = self._io._check(self._vault, directory=True)
        if (current.st_dev, current.st_ino) != self._identity:
            raise ValueError("vault changed")

    def _optional(self, filename):
        self._check_root()
        path = self._vault / filename
        try:
            path.lstat()
        except FileNotFoundError:
            self._check_root()
            return None
        return self._io._read(path, MAX_FILE_BYTES)

    def _destination(self):
        self._check_root()
        target = self._vault / "profile"
        try:
            target.lstat()
        except FileNotFoundError:
            self._check_root()
            return "absent"
        self._io._check(target, directory=True)
        with os.scandir(target) as entries:
            occupied = next(entries, None) is not None
        self._io._check(target, directory=True)
        return "occupied" if occupied else "empty"

    def _inspect(self):
        sources = {name: self._optional(name) for name in _NAMES}
        if sum(len(raw) for raw in sources.values() if raw is not None) > MAX_TOTAL_BYTES:
            raise ValueError("source limit")
        files, issues = [], []
        eligible = True

        def issue(code, en, zh):
            issues.append(ProfileMigrationIssue(code=code, message_en=en, message_zh=zh))

        issue(
            "layout_only",
            "Only the folder layout changes. Existing bytes are copied exactly; no new "
            "claims, evidence, translations or schema upgrades are created.",
            "仅改变文件夹布局，按原始字节复制；不生成新的主张、证据、译文或升级后的结构。",
        )
        issue(
            "originals_retained",
            "Original flat files remain. Copies are plaintext and may be synced by a "
            "sync folder. Existing profile/ content is never overwritten or merged.",
            "原有平铺文件保留。副本为明文，同步文件夹可能将其同步；"
            "不会覆盖或合并 profile/ 中的内容。",
        )
        for name, raw in sources.items():
            if raw is None:
                files.append(ProfileMigrationFile(
                    filename=name, present=False, size_bytes=0, sha256=None,
                    text=None, encoding="missing",
                ))
                continue
            try:
                text, encoding = raw.decode("utf-8"), "utf8"
            except UnicodeError:
                text, encoding, eligible = None, "binary", False
                issue(
                    "invalid_utf8",
                    f"{name} is not UTF-8 text. It remains untouched; copying is blocked.",
                    f"{name} 不是 UTF-8 文本。原件保持不变，暂不能复制。",
                )
            files.append(ProfileMigrationFile(
                filename=name, present=True, size_bytes=len(raw), sha256=_hash(raw),
                text=text, encoding=encoding,
            ))
            if name == "profile.json" and encoding == "utf8":
                try:
                    _strict_json(raw)
                except (ValueError, TypeError, RecursionError, UnicodeError):
                    eligible = False
                    issue(
                        "invalid_profile_json",
                        "profile.json does not satisfy the supported personal-profile "
                        "contract. Invalid, duplicate, nonfinite or unsupported fields are "
                        "not repaired or dropped; review the unchanged original.",
                        "profile.json 不符合当前支持的个人档案契约。无效、重复、非有限数值或不支持"
                        "的字段不会被修复或丢弃；请复核保留不变的原件。",
                    )
        if all(raw is None for raw in sources.values()):
            eligible = False
            issue(
                "missing_sources", "No flat profile files were found; nothing can be copied.",
                "未找到平铺档案文件，没有可复制的内容。",
            )
        destination = self._destination()
        if destination == "occupied":
            eligible = False
            issue(
                "destination_occupied",
                "profile/ already contains entries. Automatic overwriting or merging is blocked.",
                "profile/ 已含有内容，已阻止自动覆盖或合并。",
            )
        if any(self._optional(name) != raw for name, raw in sources.items()):
            raise ValueError("source changed during preview")
        if self._destination() != destination:
            raise ValueError("destination changed during preview")
        presence = {
            item.filename: {"present": item.present, "size_bytes": item.size_bytes,
                            "sha256": item.sha256}
            for item in files
        }
        fields = {
            "vault_digest": self._vault_digest,
            "files": [item.model_dump(mode="json") for item in files],
            "source_digest": _hash(_encode(presence)),
            "destination_state": destination,
            "eligible": eligible,
            "issues": [item.model_dump(mode="json") for item in issues],
        }
        return ProfileMigrationPreview(**fields, preview_digest=_hash(_encode(fields))), sources

    @_safe
    def inspect(self) -> ProfileMigrationPreview:
        """Read only the two fixed flat source files and destination presence."""
        return self._inspect()[0]

    def _clean_stage(self, stage, identity):
        """Remove only this invocation's regular fixed members, or leave it alone."""
        try:
            current = self._io._check(stage, directory=True)
            if (current.st_dev, current.st_ino) != identity:
                return
            entries = self._io._entries(stage)
            if not {entry.name for entry in entries} <= set(_NAMES):
                return
            for entry in entries:
                self._io._check(entry, directory=False)
            for entry in entries:
                self._io._check(entry, directory=False)
                entry.unlink()
            self._io._check(stage, directory=True)
            stage.rmdir()  # Only the verified empty directory; never recursive deletion.
        except (OSError, ValueError):
            pass

    def _verify_stage(self, stage, identity, sources):
        current = self._io._check(stage, directory=True)
        if (current.st_dev, current.st_ino) != identity:
            raise ValueError("staged directory changed")
        if {entry.name for entry in self._io._entries(stage)} != {
            name for name, raw in sources.items() if raw is not None
        }:
            raise ValueError("staged members changed")
        for name, raw in sources.items():
            if raw is not None and self._io._read(stage / name, MAX_FILE_BYTES) != raw:
                raise ValueError("staged bytes changed")
        current = self._io._check(stage, directory=True)
        if (current.st_dev, current.st_ino) != identity:
            raise ValueError("staged directory changed during read")

    @_safe
    def migrate(self, preview: ProfileMigrationPreview, *, confirmed: bool) -> MigrationResult:
        """Publish one complete directory after explicit confirmation and revalidation."""
        if confirmed is not True or type(preview) is not ProfileMigrationPreview:
            raise ValueError("explicit confirmation and typed preview required")
        preview = ProfileMigrationPreview.model_validate(preview.model_dump(mode="python"))
        current, sources = self._inspect()
        if not preview.eligible or current != preview:
            raise ValueError("preview changed or ineligible")
        lock_dir = self._vault / ".profile-migration"
        self._io._mkdir(lock_dir)
        with self._io._writer(lock_dir):
            current, sources = self._inspect()
            if current != preview:
                raise ValueError("preview changed")
            stage = self._vault / f".pending-profile-migration-{uuid4().hex}"
            self._check_root()
            stage.mkdir(mode=0o700)
            info = self._io._check(stage, directory=True)
            identity = (info.st_dev, info.st_ino)
            removed_empty = False
            target = self._vault / "profile"
            try:
                for name, raw in sources.items():
                    if raw is not None:
                        self._io._write_new(stage / name, raw)
                self._verify_stage(stage, identity, sources)
                if self._inspect()[0] != preview:
                    raise ValueError("preview changed before publication")
                self._io._check(stage, directory=True)
                self._check_root()
                if preview.destination_state == "empty":
                    if self._destination() != "empty":
                        raise ValueError("destination became occupied")
                    target.rmdir()  # Verified empty only; never remove existing member files.
                    removed_empty = True
                if self._destination() != "absent":
                    raise ValueError("destination appeared")
                self._verify_stage(stage, identity, sources)
                os.rename(stage, target)
            except (OSError, ValueError, TypeError):
                if removed_empty:
                    try:
                        self._check_root()
                        target.mkdir(mode=0o700)  # Fails harmlessly if another actor created it.
                    except (OSError, ValueError):
                        pass
                self._clean_stage(stage, identity)
                raise
        return MigrationResult(
            directory_path=str(target), source_digest=preview.source_digest,
            files=[name for name, raw in sources.items() if raw is not None],
        )
