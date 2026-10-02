"""Explicit, encrypted exchange of a selected reflection summary only.

No email, discovery, transcript export, account access or automatic import occurs.
Encryption protects a file with a password; it does not authenticate its author,
verify relationship claims, anonymize narrative text or authorize forwarding.
"""

from __future__ import annotations

import os
import re
import struct
from functools import wraps
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from anti_dating_scam.services.reflection_chat import read_saved_reflection
from anti_dating_scam.services.report_review import (
    Digest,
    RecordID,
    ReportReviewService,
    _decode,
    _encode,
    _hash,
)

MAX_PROFILE_TEXT_CHARS = 8_000
MAX_PACKET_BYTES = 96_000
MAX_FILE_BYTES = MAX_PACKET_BYTES + 128
_MAGIC = b"SLWMATCH"
_VERSION = 1
_N, _R, _P = 32_768, 8, 1
_HEADER = struct.Struct(">8sBIBB16s12s")
_ERROR = (
    "The relationship file could not be prepared, saved or opened safely. "
    "Check the selected file and password. Existing files were not replaced. "
    "/ 无法安全准备、保存或打开相处资料包，请检查所选文件和密码。未替换已有文件。"
)


class RelationshipExchangeError(ValueError):
    """Sanitized bilingual failure, without packet contents, password or path."""


def _safe(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:
            raise RelationshipExchangeError(_ERROR) from None

    return wrapped


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class SharedText(_Model):
    en: Annotated[str, Field(min_length=1, max_length=1_200, pattern=r"\S")]
    zh: Annotated[str, Field(min_length=1, max_length=1_200, pattern=r"\S")]

    @model_validator(mode="after")
    def two_languages(self):
        if (
            not re.search(r"[A-Za-z]", self.en)
            or len(re.findall(r"[\u3400-\u9fff]", self.zh)) < 2
            or self.en == self.zh
        ):
            raise ValueError("Both language versions are required.")
        return self


class SharedReflectionItem(_Model):
    topic: Literal["values", "wants", "communication", "boundaries"]
    text: SharedText
    confidence: Literal["low"]


class SharedRelationshipProfile(_Model):
    schema_version: Literal["1.0"]
    profile_id: RecordID
    origin: Literal["ai_reflection_self_report"]
    provisional: Literal[True]
    authorship: Literal["unverified"]
    share_permission: Literal["recipient_private_comparison_only"]
    items: Annotated[list[SharedReflectionItem], Field(max_length=5)]
    open_questions: Annotated[list[SharedText], Field(max_length=10)]
    unknowns: Annotated[list[SharedText], Field(min_length=1, max_length=10)]
    caveats: Annotated[list[SharedText], Field(min_length=1, max_length=10)]

    @field_validator("provisional", mode="before")
    @classmethod
    def explicitly_provisional(cls, value):
        if value is not True:
            raise ValueError("An explicitly provisional summary is required.")
        return value

    @model_validator(mode="after")
    def bounded_summary(self):
        pairs = (
            [item.text for item in self.items] + self.open_questions + self.unknowns + self.caveats
        )
        if sum(len(pair.en) + len(pair.zh) for pair in pairs) > MAX_PROFILE_TEXT_CHARS:
            raise ValueError("Selected summary is too large; no text is truncated.")
        if len(_encode(self.model_dump(mode="json"))) > MAX_PACKET_BYTES:
            raise ValueError("Packet size limit exceeded.")
        return self


class PreparedRelationshipExport(_Model):
    session_id: RecordID
    source_digest: Digest
    packet: SharedRelationshipProfile

    @property
    def packet_digest(self) -> str:
        return _hash(_encode(self.packet.model_dump(mode="json")))

    @property
    def preview_en(self) -> str:
        return preview_relationship_profile(self.packet, "en")

    @property
    def preview_zh(self) -> str:
        return preview_relationship_profile(self.packet, "zh")


class ExportedRelationshipFile(_Model):
    path: Path
    packet_digest: Digest
    file_digest: Digest


def _checked_profile(packet: SharedRelationshipProfile) -> SharedRelationshipProfile:
    return SharedRelationshipProfile.model_validate(packet.model_dump(warnings=False))


@_safe
def profile_digest(packet: SharedRelationshipProfile) -> str:
    return _hash(_encode(_checked_profile(packet).model_dump(mode="json")))


@_safe
def preview_relationship_profile(
    packet: SharedRelationshipProfile, language: Literal["en", "zh"] = "en"
) -> str:
    checked = _checked_profile(packet)
    if language not in {"en", "zh"}:
        raise ValueError("Unsupported language.")
    english = language == "en"
    lines = [
        "Shared relationship reflection — provisional" if english else "共享相处画像——暂定理解",
        (
            "This is an AI interpretation of self-report. Identity and claims are unverified. "
            "It is shared for private discussion with the chosen recipient only. "
            "Do not forward without the sender's permission."
            if english
            else "这是 AI 对自述的解读，身份及结论未经核实。仅供所选接收者私下讨论；"
            "转发前须另获发送者许可。"
        ),
        (
            "Only the text below and an opaque profile ID are included. Chat transcripts, "
            "original quotations, account credentials and saved history are excluded. "
            "The narrative may still contain personal information: review every line."
            if english
            else "资料包只包含下列文字及随机资料编号，不包含聊天原始记录、原文引证、"
            "账号凭据或历史文件。"
            "叙述仍可能含个人信息，请逐行审阅。"
        ),
        "",
    ]
    topics = {
        "values": ("Values", "价值观"),
        "wants": ("Needs and preferences", "需要与偏好"),
        "communication": ("Communication", "沟通方式"),
        "boundaries": ("Boundaries", "个人边界"),
    }
    for item in checked.items:
        label = topics[item.topic][0 if english else 1]
        lines.append(f"{label}: {getattr(item.text, language)}")
    if not checked.items:
        lines.append(
            "No supported portrait statements yet." if english else "尚无可支持的画像陈述。"
        )
    for label, pairs in (
        (("Open questions", "待讨论问题"), checked.open_questions),
        (("Unknowns", "未知信息"), checked.unknowns),
        (("Limitations", "局限"), checked.caveats),
    ):
        lines.extend(["", label[0 if english else 1]])
        lines.extend(f"• {getattr(pair, language)}" for pair in pairs)
    return "\n".join(lines)


def _profile_from_bundle(bundle: dict, profile_id: str) -> SharedRelationshipProfile:
    report = bundle["report"]
    localized = {entry["path"]: entry for entry in bundle["localized_text"]}

    def text(path):
        entry = localized[path]
        return SharedText(en=entry["en"], zh=entry["zh"])

    return SharedRelationshipProfile(
        schema_version="1.0",
        profile_id=profile_id,
        origin="ai_reflection_self_report",
        provisional=True,
        authorship="unverified",
        share_permission="recipient_private_comparison_only",
        items=[
            SharedReflectionItem(
                topic=claim["topic"],
                confidence="low",
                text=text(f"/report/claims/{index}/claim"),
            )
            for index, claim in enumerate(report["claims"])
        ],
        open_questions=[
            text(f"/report/open_questions/{index}")
            for index in range(len(report["open_questions"]))
        ],
        unknowns=[
            text(f"/report/data_coverage/not_covered/{index}")
            for index in range(len(report["data_coverage"]["not_covered"]))
        ],
        caveats=[text(f"/report/caveats/{index}") for index in range(len(report["caveats"]))],
    )


def _password_key(password: str, salt: bytes) -> bytes:
    if (
        type(password) is not str
        or not 12 <= len(password) <= 256
        or not password.strip()
        or len(password.encode("utf-8")) > 1_024
    ):
        raise ValueError("Use a password/passphrase of 12–256 characters.")
    return Scrypt(salt=salt, length=32, n=_N, r=_R, p=_P).derive(password.encode("utf-8"))


def _path_store(path: Path) -> tuple[ReportReviewService, Path]:
    original = Path(path)
    # Windows abspath can silently strip trailing dots/spaces. Reject aliases
    # before normalization, including alternate streams in parent components.
    if any(
        ":" in part or part.rstrip(". ") != part or part in {".", ".."}
        for part in original.parts
        if part != original.anchor
    ) or original.anchor.startswith("\\\\?"):
        raise ValueError("Unsupported portable file path alias.")
    candidate = Path(os.path.abspath(os.fspath(path)))
    if (
        not candidate.name
        or ":" in candidate.name
        or candidate.name.rstrip(". ") != candidate.name
        or candidate.is_reserved()
    ):
        raise ValueError("Unsupported portable file path.")
    store = ReportReviewService(candidate.parent)
    return store, candidate


def _write_new_atomic(store: ReportReviewService, destination: Path, raw: bytes) -> None:
    temporary = destination.parent / f".pending-relationship-{uuid4().hex}"
    store._write_new(temporary, raw)
    before = store._check(temporary, directory=False)
    try:
        if store._read(temporary, MAX_FILE_BYTES) != raw:
            raise ValueError("Staged encrypted file changed.")
        store._check(destination.parent, directory=True)
        # An exclusive hard-link publication is atomic and never replaces a
        # pre-existing filename on either Windows or POSIX. Only ciphertext is
        # staged. Removing our staging link restores the final file's nlink=1.
        os.link(temporary, destination, follow_symlinks=False)
    finally:
        current = temporary.lstat()
        if (current.st_dev, current.st_ino) == (before.st_dev, before.st_ino):
            temporary.unlink()
    store._check(destination, directory=False)


class RelationshipExchangeService:
    @_safe
    def __init__(self, vault_dir: Path):
        # Capture only an explicit vault directory, without reading any report.
        self._vault = ReportReviewService(vault_dir)._vault

    @_safe
    def prepare_export(self, session_id: str) -> PreparedRelationshipExport:
        bundle = read_saved_reflection(self._vault, session_id)
        return PreparedRelationshipExport(
            session_id=session_id,
            source_digest=_hash(_encode(bundle)),
            packet=_profile_from_bundle(bundle, uuid4().hex),
        )

    @_safe
    def export_file(
        self,
        prepared: PreparedRelationshipExport,
        destination: Path,
        password: str,
        *,
        confirmed: bool,
    ) -> ExportedRelationshipFile:
        if confirmed is not True:
            raise ValueError("Review the exact shared text and explicitly confirm export.")
        checked = PreparedRelationshipExport.model_validate(prepared.model_dump(warnings=False))
        bundle = read_saved_reflection(self._vault, checked.session_id)
        expected = _profile_from_bundle(bundle, checked.packet.profile_id)
        if checked.source_digest != _hash(_encode(bundle)) or checked.packet != expected:
            raise ValueError("The selected reflection or prepared summary changed.")
        salt, nonce = os.urandom(16), os.urandom(12)
        header = _HEADER.pack(_MAGIC, _VERSION, _N, _R, _P, salt, nonce)
        raw_packet = _encode(checked.packet.model_dump(mode="json"))
        key = _password_key(password, salt)
        encrypted = header + AESGCM(key).encrypt(nonce, raw_packet, header)
        store, path = _path_store(destination)
        _write_new_atomic(store, path, encrypted)
        return ExportedRelationshipFile(
            path=path,
            packet_digest=checked.packet_digest,
            file_digest=_hash(encrypted),
        )


@_safe
def import_relationship_file(
    path: Path, password: str, *, confirmed: bool
) -> SharedRelationshipProfile:
    """Decrypt a selected attachment in memory; never extract/write imported files."""
    if confirmed is not True:
        raise ValueError("Explicitly confirm opening this selected relationship file.")
    store, selected = _path_store(path)
    raw = store._read(selected, MAX_FILE_BYTES)
    if not _HEADER.size + 16 < len(raw) <= MAX_FILE_BYTES:
        raise ValueError("Invalid encrypted file length.")
    magic, version, n, r, p, salt, nonce = _HEADER.unpack(raw[: _HEADER.size])
    # KDF parameters are fixed, authenticated and checked BEFORE allocation. A
    # malicious file cannot request weaker encryption or an enormous KDF cost.
    if (magic, version, n, r, p) != (_MAGIC, _VERSION, _N, _R, _P):
        raise ValueError("Unsupported encrypted format or KDF parameters.")
    header = raw[: _HEADER.size]
    key = _password_key(password, salt)
    plaintext = AESGCM(key).decrypt(nonce, raw[_HEADER.size :], header)
    if len(plaintext) > MAX_PACKET_BYTES:
        raise ValueError("Decrypted packet size limit exceeded.")
    return SharedRelationshipProfile.model_validate(_decode(plaintext))
