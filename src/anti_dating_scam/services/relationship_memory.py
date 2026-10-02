"""Explicit, bounded local annotations. No discovery, imports or automatic writes."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from anti_dating_scam.services.report_review import ReportReviewService, _decode, _encode


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    text: str = Field(min_length=1, max_length=250, pattern=r"\S")
    kind: Literal["preference", "self_report", "interpretation"]
    source: str = Field(pattern=r"^(manual|session:[a-f0-9]{32})$")
    approved_at: datetime
    supersedes: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    confidence: Literal["unverified"] = "unverified"


class MemoryState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1"] = "1"
    revision: int = Field(default=0, ge=0)
    enabled: bool = False
    entries: list[MemoryEntry] = Field(default_factory=list, max_length=20)


class RelationshipMemory:
    """Ordinary local files, not vault encryption; each change needs user approval."""

    def __init__(self, vault: Path):
        self.vault = Path(os.path.abspath(vault))
        self.directory = self.vault / ".relationship-memory"

    @property
    def store(self):
        return ReportReviewService(self.vault)

    def read(self) -> MemoryState:
        try:
            self.vault.lstat()
        except FileNotFoundError:
            return MemoryState()
        try:
            self.store._check(self.directory, directory=True)
        except FileNotFoundError:
            return MemoryState()
        path = self.directory / "state.json"
        try:
            return MemoryState.model_validate(_decode(self.store._read(path, 100_000)))
        except FileNotFoundError:
            return MemoryState()

    def change(
        self,
        revision: int,
        *,
        confirmed: bool,
        action: str,
        text: str = "",
        kind: str = "preference",
        source: str = "manual",
        entry_id: str | None = None,
    ) -> MemoryState:
        if confirmed is not True:
            raise ValueError("Explicit approval is required.")
        try:
            self.vault.lstat()
        except FileNotFoundError:
            parent = ReportReviewService(self.vault.parent)
            parent._mkdir(self.vault)
        self.store._mkdir(self.directory)
        with self.store._writer(self.directory):
            state = self.read()
            if state.revision != revision:
                raise ValueError("Memory changed; review it again.")
            entries = list(state.entries)
            enabled = state.enabled
            if action == "add" and entry_id is not None:
                raise ValueError("New notes cannot replace existing notes.")
            if action in {"add", "correct"}:
                if action == "correct" and entry_id not in {item.id for item in entries}:
                    raise ValueError("Select an existing memory.")
                entry = MemoryEntry(
                    id=uuid4().hex,
                    text=text,
                    kind=kind,
                    source=source,
                    approved_at=datetime.now(UTC),
                    supersedes=entry_id if action == "correct" else None,
                )
                entries = [item for item in entries if item.id != entry_id] + [entry]
            elif action == "delete":
                if entry_id not in {item.id for item in entries}:
                    raise ValueError("Select an existing memory.")
                entries = [item for item in entries if item.id != entry_id]
            elif action == "enable":
                enabled = True
            elif action in {"pause", "revoke"}:
                enabled = False
            elif action == "clear":
                entries, enabled = [], False
            else:
                raise ValueError("Unknown memory action.")
            updated = MemoryState(revision=revision + 1, enabled=enabled, entries=entries)
            path = self.directory / "state.json"
            if path.exists() or path.is_symlink():
                self.store._check(path, directory=False)
            temporary = self.directory / (uuid4().hex + ".tmp")
            try:
                self.store._write_new(temporary, _encode(updated.model_dump(mode="json")))
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
            return updated

    def export(self, destination: Path, *, confirmed: bool) -> None:
        if confirmed is not True:
            raise ValueError("Review the unencrypted export before saving.")
        state = self.read()
        # Never overwrite existing files, including another app's data.
        with Path(destination).open("xb") as target:
            target.write(_encode(state.model_dump(mode="json")))
