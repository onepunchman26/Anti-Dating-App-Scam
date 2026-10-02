"""Checkpointed batch processing, grouped review, and reversible existing-memory adoption."""

from __future__ import annotations

import os
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from anti_dating_scam.batch_context.analysis import (
    group_items,
    item_request,
    safe_narrative,
    synthesis_request,
    validate_item,
    validate_synthesis,
)
from anti_dating_scam.batch_context.models import (
    Batch,
    Item,
    ItemAnalysis,
    Synthesis,
)
from anti_dating_scam.services.relationship_memory import (
    ExternalEvidence,
    MemoryEntry,
    RelationshipMemory,
)
from anti_dating_scam.services.report_review import ReportReviewService, _decode, _encode


class BatchService:
    def __init__(self, vault):
        self.vault = Path(os.path.abspath(vault))
        self.directory = self.vault / ".video-context"
        self.guard = ReportReviewService(self.vault)
        self.memory = RelationshipMemory(self.vault)

    def _path(self, batch_id):
        if not re.fullmatch(r"[a-f0-9]{32}", batch_id):
            raise ValueError("invalid_batch_id")
        return self.directory / (batch_id + ".json")

    def _init(self):
        self.guard._mkdir(self.directory)

    def read(self, batch_id):
        return Batch.model_validate(_decode(self.guard._read(self._path(batch_id), 40_000_000)))

    def list(self):
        try:
            self.guard._check(self.directory, directory=True)
        except FileNotFoundError:
            return []
        paths = sorted(self.directory.glob("*.json"))
        if len(paths) > 100:
            raise ValueError("batch_storage_limit")
        return [self.read(path.stem) for path in paths]

    def _write(self, batch):
        data = _encode(Batch.model_validate(batch.model_dump()).model_dump(mode="json"))
        if len(data) > 40_000_000:
            raise ValueError("batch_too_large")
        path = self._path(batch.id)
        if path.exists() or path.is_symlink():
            self.guard._check(path, directory=False)
        temporary = self.directory / (uuid4().hex + ".tmp")
        try:
            self.guard._write_new(temporary, data)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return batch

    def save(self, batch):
        with self.guard._writer(self.directory):
            current = self.read(batch.id)
            if batch.revision != current.revision:
                raise ValueError("batch_changed")
            return self._write(batch.model_copy(update={"revision": batch.revision + 1}))

    def create(self, preview, selected_ids, *, name, confirmed):
        if confirmed is not True:
            raise ValueError("import_consent_required")
        known = {v.id for v in preview.videos}
        if not selected_ids or not set(selected_ids) <= known:
            raise ValueError("select_batch_items")
        self._init()
        with self.guard._writer(self.directory):
            existing = self.list()
            if len(existing) >= 100:
                raise ValueError("batch_storage_limit")
            # Reuse only valid prior results; no second opaque cache retains deleted imports.
            cache = {
                i.video.digest: i
                for b in existing
                for i in b.items
                if i.status in {"full", "partial"} and i.analysis
            }
            items = []
            for video in preview.videos:
                if video.id not in selected_ids:
                    continue
                previous = cache.get(video.digest)
                if previous:
                    validate_item(previous.analysis, video)
                items.append(
                    Item(
                        video=video,
                        analysis=previous.analysis if previous else None,
                        status=previous.status if previous else "pending",
                        reused=previous is not None,
                    )
                )
            return self._write(
                Batch(
                    name=name,
                    items=items,
                    duplicates=preview.duplicates,
                    invalid=preview.invalid,
                    notices=preview.notices,
                )
            )

    def fetch_metadata(
        self, batch_id, fetcher, *, approved_digest, confirmed, cancel=None, progress=lambda _: None
    ):
        batch = self.read(batch_id)
        if confirmed is not True or approved_digest != batch.digest:
            raise ValueError("metadata_scope_changed")
        if batch.findings:
            raise ValueError("already_reviewable")
        cancel = cancel or threading.Event()
        for index, item in enumerate(batch.items):
            if cancel.is_set():
                break
            if item.video.title or item.video.source not in fetcher.ENDPOINTS:
                continue
            try:
                video = fetcher.fetch(item.video)
                if video.id != item.video.id or video.url != item.video.url:
                    raise ValueError("metadata_identity_changed")
                changed = Item(video=video)
            except Exception:
                changed = item.model_copy(update={"error": "metadata_unavailable"})
            if cancel.is_set():
                break
            items = list(batch.items)
            items[index] = changed
            batch = self.save(batch.model_copy(update={"items": items}))
            progress(batch)
        return batch

    def process(
        self, batch_id, backend, grant, *, cancel=None, retry_failed=False, progress=lambda _: None
    ):
        batch = self.read(batch_id)
        grant.check(batch, backend)
        if batch.findings:
            if not retry_failed or not any(i.status == "failed" for i in batch.items):
                raise ValueError("already_reviewable")
            self.memory.remove_batch(batch.id, confirmed=True)
            batch = self.save(batch.model_copy(update={"findings": [], "questions": []}))
        cancel = cancel or threading.Event()
        batch = self.save(batch.model_copy(update={"state": "running"}))
        try:
            for index, item in enumerate(batch.items):
                if cancel.is_set():
                    break
                if item.status != "pending" and not (retry_failed and item.status == "failed"):
                    continue
                if not item.video.materials and not item.video.title:
                    updated = item.model_copy(update={"status": "skipped", "error": "no_content"})
                else:
                    try:
                        raw = grant.call(batch, backend, item_request(item.video))
                        result = validate_item(ItemAnalysis.model_validate_json(raw), item.video)
                        complete = item.video.coverage == "full" and all(
                            len(m.text) <= 2000 and not m.truncated for m in item.video.materials
                        )
                        updated = item.model_copy(
                            update={
                                "analysis": result,
                                "status": "full" if complete else "partial",
                                "error": "",
                            }
                        )
                    except Exception as exc:
                        category = getattr(exc, "category", "")
                        if category in {"usage", "auth", "model", "cancelled"}:
                            batch = self.save(batch.model_copy(update={"state": "paused"}))
                            raise ValueError("batch_" + category) from None
                        updated = item.model_copy(
                            update={"status": "failed", "error": "analysis_failed"}
                        )
                if cancel.is_set():
                    break  # Late output has no persistence or model effect.
                items = list(batch.items)
                items[index] = updated
                batch = self.save(batch.model_copy(update={"items": items}))
                progress(batch)
            if cancel.is_set():
                return self.save(batch.model_copy(update={"state": "paused"}))
            groups, omitted = group_items(batch)
            findings, questions = [], []
            if groups:
                request, used = synthesis_request(groups)
                raw = grant.call(batch, backend, request)
                result = Synthesis.model_validate_json(raw)
                findings = validate_synthesis(result, used)
                questions = result.questions
                represented = {
                    g for f in result.findings + result.reflection_drafts for g in f.group_ids
                }
                omitted += len(groups) - len(represented)
            if cancel.is_set():
                return self.save(batch.model_copy(update={"state": "paused"}))
            return self.save(
                batch.model_copy(
                    update={
                        "findings": findings,
                        "questions": questions,
                        "omitted_groups": omitted,
                        "state": "complete",
                    }
                )
            )
        except Exception:
            # No automatic AI retry. A restart keeps all completed per-item work.
            latest = self.read(batch_id)
            if latest.state == "running":
                self.save(latest.model_copy(update={"state": "failed"}))
            raise

    def review(
        self, batch_id, revision, finding_ids, *, action, text="", language="en", confirmed=False
    ):
        if confirmed is not True or language not in {"en", "zh"}:
            raise ValueError("review_required")
        with self.guard._writer(self.directory):
            batch = self.read(batch_id)
            if batch.revision != revision:
                raise ValueError("batch_changed")
            chosen = [f for f in batch.findings if f.id in finding_ids]
            if not chosen or len(chosen) != len(set(finding_ids)):
                raise ValueError("select_findings")
            findings = list(batch.findings)
            if action == "confirm":
                proposals = []
                for finding in chosen:
                    if finding.status in {"removed", "rejected"}:
                        raise ValueError("finding_no_longer_active")
                    content = finding.edited_text or getattr(finding.text, language)
                    safe_narrative(content)
                    proposals.append(
                        MemoryEntry(
                            id=uuid4().hex,
                            text=content,
                            kind="preference" if finding.kind == "interest" else "self_report",
                            source="batch:" + batch.id,
                            approved_at=datetime.now(UTC),
                            reviewed_at=datetime.now(UTC),
                            batch_ids=[batch.id],
                            external_key=finding.key,
                            external_evidence=[
                                ExternalEvidence(batch_id=batch.id, **q.model_dump())
                                for q in finding.evidence
                            ],
                            context="Explicitly adopted saved-video finding / "
                            "明确采纳的收藏视频结论",
                            basis="User confirmed a draft; creators' words are not user beliefs. / "
                            "用户确认草稿；创作者的话不等于用户信念。",
                            uncertainty=getattr(finding.uncertainty, language)[:250],
                        )
                    )
                self.memory.approve_batch(self.memory.read().revision, proposals, confirmed=True)
                findings = [
                    f.model_copy(update={"status": "confirmed"}) if f in chosen else f
                    for f in findings
                ]
            elif action in {"revise", "reject", "remove", "merge"}:
                if action in {"revise", "merge"} and not (text.strip() and len(text) <= 250):
                    raise ValueError("edit_length_1_250")
                if action == "revise" and len(chosen) != 1:
                    raise ValueError("revise_one_group")
                if action == "merge" and (len(chosen) < 2 or len({f.kind for f in chosen}) != 1):
                    raise ValueError("merge_same_kind")
                self.memory.remove_batch(batch.id, keys={f.key for f in chosen}, confirmed=True)
                if action == "merge":
                    merged = chosen[0].model_copy(
                        update={
                            "id": uuid4().hex,
                            "edited_text": text,
                            "status": "draft",
                            "video_ids": list(
                                dict.fromkeys(v for f in chosen for v in f.video_ids)
                            ),
                            "evidence": list(
                                {
                                    (q.video_id, q.origin, q.quote): q
                                    for f in chosen
                                    for q in f.evidence
                                }.values()
                            )[:6],
                        }
                    )
                    findings = [f for f in findings if f not in chosen] + [merged]
                else:
                    findings = [
                        f.model_copy(
                            update={
                                "edited_text": text if action == "revise" else f.edited_text,
                                "status": {
                                    "revise": "draft",
                                    "reject": "rejected",
                                    "remove": "removed",
                                }[action],
                            }
                        )
                        if f in chosen
                        else f
                        for f in findings
                    ]
            else:
                raise ValueError("unknown_review_action")
            return self._write(
                batch.model_copy(update={"findings": findings, "revision": batch.revision + 1})
            )

    def undo(self, batch_id, *, confirmed):
        if confirmed is not True:
            raise ValueError("undo_consent_required")
        with self.guard._writer(self.directory):
            self.read(batch_id)
            # Memory first: interrupted deletion can never leave active orphan assertions.
            self.memory.remove_batch(batch_id, confirmed=True)
            self.guard._check(self._path(batch_id), directory=False)
            self._path(batch_id).unlink()

    def export(self, batch_id, destination):
        batch = self.read(batch_id)
        # Export the reviewable result, not the full source excerpts. Never overwrite.
        data = {
            "name": batch.name,
            "counts": batch.counts(),
            "created_at": batch.created_at.isoformat(),
            "findings": [f.model_dump(mode="json") for f in batch.findings],
            "questions": [q.model_dump() for q in batch.questions],
        }
        with Path(destination).open("xb") as target:
            target.write(_encode(data))
