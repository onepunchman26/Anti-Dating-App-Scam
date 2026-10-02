"""Bounded memory proposals and deterministic evidence/relevance checks; no storage."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MemoryKind = Literal[
    "preference",
    "self_report",
    "interpretation",
    "event",
    "goal",
    "boundary",
    "pattern",
    "open_question",
]
INFERRED_KINDS = {"interpretation", "pattern", "open_question"}


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Evidence(Model):
    source: str = Field(pattern=r"^S[0-9]{3}$")
    quote: str = Field(min_length=1, max_length=350, pattern=r"\S")


class MemoryCandidate(Model):
    action: Literal["add", "refine", "qualify", "supersede"]
    target_id: str | None = Field(pattern=r"^[a-f0-9]{32}$")
    text: str = Field(min_length=1, max_length=250, pattern=r"\S")
    kind: MemoryKind
    context: str = Field(min_length=1, max_length=250, pattern=r"\S")
    basis: str = Field(min_length=1, max_length=350, pattern=r"\S")
    uncertainty: str = Field(min_length=1, max_length=250, pattern=r"\S")
    alternatives: list[str] = Field(max_length=3)
    evidence: list[Evidence] = Field(min_length=1, max_length=3)
    depends_on: list[str] = Field(max_length=4)
    sensitive: bool

    @model_validator(mode="after")
    def bounded(self):
        if (self.action == "add") != (self.target_id is None):
            raise ValueError("Replacement requires a target; additions cannot name one.")
        if any(not text.strip() or len(text) > 250 for text in self.alternatives):
            raise ValueError("Invalid alternative.")
        if any(not re.fullmatch(r"[a-f0-9]{32}", item) for item in self.depends_on):
            raise ValueError("Invalid dependency.")
        if self.kind in INFERRED_KINDS and not self.alternatives:
            raise ValueError("Hypotheses need an alternative explanation.")
        return self


class MemoryEvaluation(Model):
    outcome: Literal["proposals", "no_update", "disabled", "safety_priority", "unavailable"]
    reason: str = Field(min_length=1, max_length=350, pattern=r"\S")
    candidates: list[MemoryCandidate] = Field(max_length=3)

    @model_validator(mode="after")
    def consistent(self):
        if (self.outcome == "proposals") != bool(self.candidates):
            raise ValueError("Inconsistent evaluation.")
        return self


class EvaluatedMemory(Model):
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    scope: str
    revision: int
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evaluation: MemoryEvaluation

    def operation_id(self, candidate: MemoryCandidate) -> str:
        payload = [self.scope, self.session_id, candidate.model_dump(mode="json")]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate_evaluation(evaluation, *, sources, permitted, existing):
    """Reject fabricated evidence and foreign dependencies; discard exact duplicates."""
    result = MemoryEvaluation.model_validate(evaluation)
    if not permitted:
        return MemoryEvaluation(
            outcome="disabled", reason="Session only / 仅本次会话", candidates=[]
        )
    known = {item.id: item for item in existing if item.review_status != "rejected"}
    candidates = []
    for item in result.candidates:
        if any(e.source not in sources or e.quote not in sources[e.source] for e in item.evidence):
            raise ValueError("Memory evidence is not an exact current user quote.")
        if item.target_id is not None and item.target_id not in known:
            raise ValueError("Unknown or rejected memory target.")
        if any(dep not in known or dep == item.target_id for dep in item.depends_on):
            raise ValueError("Invalid memory dependency.")
        accounts = {e.source for e in item.evidence} | set(item.depends_on)
        if item.kind == "pattern" and len(accounts) < 2:
            raise ValueError("A pattern needs multiple accounts.")
        if item.action == "add" and any(
            old.text.casefold().strip() == item.text.casefold().strip() for old in existing
        ):
            continue
        if item not in candidates:
            if item.kind in INFERRED_KINDS:
                # Conservatively bind inferred statements to all retrieved context;
                # the model cannot omit a dependency to evade later deletion.
                item = item.model_copy(
                    update={
                        "depends_on": sorted(
                            set(item.depends_on) | (set(known) - {item.target_id})
                        ),
                    }
                )
            candidates.append(item)
    return result.model_copy(
        update={
            "candidates": candidates,
            "outcome": "proposals"
            if candidates
            else ("no_update" if result.outcome == "proposals" else result.outcome),
        }
    )


def _terms(text):
    text = text.casefold()
    words = set(re.findall(r"[a-z]{3,}", text)) - {
        "the",
        "and",
        "that",
        "this",
        "with",
        "have",
        "was",
        "for",
        "you",
        "are",
        "but",
    }
    for block in re.findall(r"[\u3400-\u9fff]+", text):
        words.update(block[i : i + 2] for i in range(len(block) - 1))
    return words


def relevant_entries(state, query: str, *, limit: int = 4):
    """Deterministic local retrieval, no external index, embedding or archive read."""
    if not state.enabled:
        return []
    entries = [entry for entry in state.entries if entry.review_status != "rejected"]
    if not query.strip():
        # A small opening orientation; do not preload intimate episodes unprompted.
        return [e for e in entries if e.kind in {"preference", "goal", "boundary"}][-2:]
    terms = _terms(query)
    ranked = [(len(terms & _terms(e.text + " " + e.context)), e) for e in entries]
    ranked = [(score, e) for score, e in ranked if score]
    ranked.sort(key=lambda pair: (pair[0], pair[1].approved_at), reverse=True)
    return [entry for _, entry in ranked[:limit]]
