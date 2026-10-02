"""Explicit, bounded local annotations. No discovery, imports or automatic writes."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anti_dating_scam.services.personal_model import (
    INFERRED_KINDS,
    EvaluatedMemory,
    Evidence,
    MemoryKind,
)
from anti_dating_scam.services.report_review import ReportReviewService, _decode, _encode


class ExternalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    batch_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    video_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    origin: str = Field(
        pattern=r"^(title|transcript|description|existing_summary|user_annotation)$"
    )
    quote: str = Field(min_length=1, max_length=200)


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    text: str = Field(min_length=1, max_length=250, pattern=r"\S")
    kind: MemoryKind
    source: str = Field(pattern=r"^(manual|(?:session|batch):[a-f0-9]{32})$")
    approved_at: datetime
    supersedes: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    confidence: Literal["unverified", "tentative"] = "unverified"
    origin: Literal["user_report", "ai_inference"] = "user_report"
    context: str = Field(default="", max_length=250)
    basis: str = Field(default="", max_length=350)
    uncertainty: str = Field(default="", max_length=250)
    alternatives: list[str] = Field(default_factory=list, max_length=3)
    evidence: list[Evidence] = Field(default_factory=list, max_length=3)
    depends_on: list[str] = Field(default_factory=list, max_length=4)
    review_status: Literal["confirmed", "questioned", "rejected", "corrected"] = "confirmed"
    sensitive: bool = False
    reviewed_at: datetime | None = None
    batch_ids: list[str] = Field(default_factory=list, max_length=100)
    external_key: str = Field(default="", max_length=64)
    external_evidence: list[ExternalEvidence] = Field(default_factory=list, max_length=600)

    def context_payload(self):
        """Import copies are bookkeeping, never extra corroboration in future AI context."""
        data = self.model_dump(mode="json")
        data.pop("batch_ids")
        refs = [r.model_dump(exclude={"batch_id"}) for r in self.external_evidence]
        data["external_evidence"] = list({tuple(r.values()): r for r in refs}.values())[:6]
        return data

    @model_validator(mode="before")
    @classmethod
    def migrate_origin(cls, data):
        if isinstance(data, dict) and "origin" not in data:
            data = dict(data)
            data["origin"] = "ai_inference" if data.get("kind") in INFERRED_KINDS else "user_report"
        return data


class MemoryChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    revision: int
    action: str
    entry_ids: list[str]
    at: datetime


class MemoryState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1", "2"] = "2"
    revision: int = Field(default=0, ge=0)
    enabled: bool = False
    entries: list[MemoryEntry] = Field(default_factory=list, max_length=20)
    changes: list[MemoryChange] = Field(default_factory=list, max_length=100)
    applied: list[str] = Field(default_factory=list, max_length=200)


class RelationshipMemory:
    """Ordinary local files, not vault encryption; each change needs user approval."""

    def __init__(self, vault: Path):
        self.vault = Path(os.path.abspath(vault))
        self.directory = self.vault / ".relationship-memory"

    @property
    def store(self):
        return ReportReviewService(self.vault)

    @property
    def scope(self) -> str:
        return hashlib.sha256(os.path.normcase(str(self.vault.resolve())).encode()).hexdigest()

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
            return MemoryState.model_validate(_decode(self.store._read(path, 16_000_000)))
        except FileNotFoundError:
            return MemoryState()

    @staticmethod
    def _remove_dependents(entries, removed):
        removed = set(removed)
        while True:
            more = {e.id for e in entries if set(e.depends_on) & removed}
            if more <= removed:
                return [e for e in entries if e.id not in removed]
            removed |= more

    def _commit(self, state, entries, *, enabled, action, ids, operation_id=None):
        updated = MemoryState(
            revision=state.revision + 1,
            enabled=enabled,
            entries=entries,
            changes=(
                state.changes
                + [
                    MemoryChange(
                        revision=state.revision + 1,
                        action=action,
                        entry_ids=ids,
                        at=datetime.now(UTC),
                    )
                ]
            )[-100:],
            applied=(state.applied + ([operation_id] if operation_id else []))[-200:],
        )
        path = self.directory / "state.json"
        if path.exists() or path.is_symlink():
            self.store._check(path, directory=False)
        temporary = self.directory / (uuid4().hex + ".tmp")
        encoded = _encode(updated.model_dump(mode="json"))
        if len(encoded) > 16_000_000:
            raise ValueError("memory_storage_limit")
        try:
            self.store._write_new(temporary, encoded)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return updated

    def approve(self, evaluated: EvaluatedMemory, index: int, *, confirmed: bool, reject=False):
        """One explicit approval is atomic; stale batches must be re-evaluated."""
        evaluated = EvaluatedMemory.model_validate(evaluated.model_dump())
        if confirmed is not True or evaluated.scope != self.scope:
            raise ValueError("Approval or selected user scope does not match.")
        if not 0 <= index < len(evaluated.evaluation.candidates):
            raise ValueError("Select a candidate.")
        candidate = evaluated.evaluation.candidates[index]
        operation = evaluated.operation_id(candidate)
        self.store._check(self.directory, directory=True)
        with self.store._writer(self.directory):
            state = self.read()
            if operation in state.applied:
                return state  # A retry must not resurrect a subsequently deleted record.
            if state.revision != evaluated.revision or not state.enabled:
                raise ValueError("Memory changed or is disabled; evaluate again.")
            if reject:
                return self._commit(
                    state,
                    state.entries,
                    enabled=True,
                    action="reject_candidate",
                    ids=[],
                    operation_id=operation,
                )
            if candidate.action == "add" and any(
                old.text.casefold().strip() == candidate.text.casefold().strip()
                for old in state.entries
            ):
                return self._commit(
                    state,
                    state.entries,
                    enabled=True,
                    action="unchanged",
                    ids=[],
                    operation_id=operation,
                )
            known = {e.id for e in state.entries if e.review_status != "rejected"}
            if (candidate.target_id and candidate.target_id not in known) or any(
                dep not in known for dep in candidate.depends_on
            ):
                raise ValueError("The referenced memory no longer exists.")
            entry = MemoryEntry(
                id=uuid4().hex,
                text=candidate.text,
                kind=candidate.kind,
                source="session:" + evaluated.session_id,
                approved_at=datetime.now(UTC),
                supersedes=candidate.target_id,
                origin=("ai_inference" if candidate.kind in INFERRED_KINDS else "user_report"),
                confidence="tentative" if candidate.kind in INFERRED_KINDS else "unverified",
                context=candidate.context,
                basis=candidate.basis,
                uncertainty=candidate.uncertainty,
                alternatives=candidate.alternatives,
                evidence=candidate.evidence,
                depends_on=candidate.depends_on,
                sensitive=candidate.sensitive,
                review_status="corrected" if candidate.target_id else "confirmed",
            )
            entries = self._remove_dependents(
                state.entries,
                [candidate.target_id] if candidate.target_id else [],
            )
            if not set(entry.depends_on) <= {e.id for e in entries}:
                raise ValueError("Correction invalidated a required dependency.")
            return self._commit(
                state,
                entries + [entry],
                enabled=True,
                action=candidate.action,
                ids=[entry.id] + ([candidate.target_id] if candidate.target_id else []),
                operation_id=operation,
            )

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
                    origin="ai_inference" if kind in INFERRED_KINDS else "user_report",
                    confidence="tentative" if kind in INFERRED_KINDS else "unverified",
                    review_status="corrected" if action == "correct" else "confirmed",
                )
                entries = self._remove_dependents(entries, [entry_id] if entry_id else []) + [entry]
            elif action == "delete":
                if entry_id not in {item.id for item in entries}:
                    raise ValueError("Select an existing memory.")
                entries = self._remove_dependents(entries, [entry_id])
            elif action in {"reject", "question"}:
                if entry_id not in {item.id for item in entries}:
                    raise ValueError("Select an existing memory.")
                selected = next(e for e in entries if e.id == entry_id)
                entries = self._remove_dependents(entries, [entry_id]) + [
                    selected.model_copy(
                        update={
                            "review_status": "rejected" if action == "reject" else "questioned",
                            "reviewed_at": datetime.now(UTC),
                        }
                    )
                ]
            elif action == "enable":
                enabled = True
            elif action in {"pause", "revoke"}:
                enabled = False
            elif action == "clear":
                entries, enabled = [], False
            else:
                raise ValueError("Unknown memory action.")
            return self._commit(
                state,
                entries,
                enabled=enabled,
                action=action,
                ids=[entry_id] if entry_id else [],
            )

    def export(self, destination: Path, *, confirmed: bool) -> None:
        if confirmed is not True:
            raise ValueError("Review the unencrypted export before saving.")
        state = self.read()
        # Never overwrite existing files, including another app's data.
        with Path(destination).open("xb") as target:
            target.write(_encode(state.model_dump(mode="json")))

    def approve_batch(self, revision, proposals, *, confirmed):
        """Explicit grouped adoption into the existing model, atomic and duplicate-aware."""
        if confirmed is not True:
            raise ValueError("batch_consent_required")
        proposals = [MemoryEntry.model_validate(p.model_dump()) for p in proposals]
        self.store._mkdir(self.directory)
        with self.store._writer(self.directory):
            state = self.read()
            if state.revision != revision or not state.enabled:
                raise ValueError("memory_changed_or_disabled")
            entries, changed = list(state.entries), []
            for proposal in proposals:
                if not proposal.external_key or not proposal.batch_ids:
                    raise ValueError("batch_sources_required")
                previous = next(
                    (e for e in entries if e.external_key == proposal.external_key), None
                )
                if (
                    previous
                    and previous.text == proposal.text
                    and previous.review_status
                    in {
                        "confirmed",
                        "corrected",
                    }
                ):
                    sources = list(dict.fromkeys(previous.batch_ids + proposal.batch_ids))
                    refs = {
                        tuple(r.model_dump().values()): r
                        for r in previous.external_evidence + proposal.external_evidence
                    }
                    entries = [
                        e.model_copy(
                            update={
                                "batch_ids": sources,
                                "external_evidence": list(refs.values()),
                            }
                        )
                        if e.id == previous.id
                        else e
                        for e in entries
                    ]
                    continue
                if not previous and any(
                    e.text.casefold() == proposal.text.casefold() for e in entries
                ):
                    continue
                if previous:
                    entries = self._remove_dependents(entries, [previous.id])
                    proposal = proposal.model_copy(
                        update={"supersedes": previous.id, "review_status": "corrected"}
                    )
                entries.append(proposal)
                changed.append(proposal.id)
            if len(entries) > 20:
                raise ValueError("memory_full_20")
            return self._commit(state, entries, enabled=True, action="approve_batch", ids=changed)

    def remove_batch(self, batch_id, *, keys=None, confirmed):
        """Recalculate remaining explicit approvals; cascade when the last support is removed."""
        if confirmed is not True:
            raise ValueError("batch_consent_required")
        state = self.read()
        if not any(batch_id in e.batch_ids for e in state.entries):
            return state
        with self.store._writer(self.directory):
            state = self.read()
            entries, removed = [], []
            for entry in state.entries:
                if batch_id not in entry.batch_ids or (
                    keys is not None and entry.external_key not in keys
                ):
                    entries.append(entry)
                    continue
                remaining = [key for key in entry.batch_ids if key != batch_id]
                refs = [r for r in entry.external_evidence if r.batch_id != batch_id]
                if not remaining or not refs:
                    # No surviving exact evidence: remove rather than preserve a stale assertion.
                    removed.append(entry.id)
                else:
                    entries.append(
                        entry.model_copy(
                            update={
                                "batch_ids": remaining,
                                "external_evidence": refs,
                                "source": "batch:" + remaining[0],
                                "reviewed_at": datetime.now(UTC),
                            }
                        )
                    )
            entries = self._remove_dependents(entries, removed)
            return self._commit(
                state, entries, enabled=state.enabled, action="remove_batch", ids=removed
            )
