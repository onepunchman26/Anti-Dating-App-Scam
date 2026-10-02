"""Synthetic collection journeys, attribution, batch consent and deletion regressions."""

import json
import os
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest

from anti_dating_scam.ai.privacy import BackendError, outbound_messages
from anti_dating_scam.batch_context.analysis import (
    BatchGrant,
    group_items,
    item_request,
    synthesis_request,
    validate_item,
    validate_synthesis,
)
from anti_dating_scam.batch_context.importers import (
    canonical_url,
    import_files,
    import_notes,
    parse_text,
    preview_rows,
)
from anti_dating_scam.batch_context.models import ItemAnalysis, Synthesis
from anti_dating_scam.batch_context.retrieval import PublicMetadata
from anti_dating_scam.batch_context.service import BatchService
from anti_dating_scam.services.personal_model import relevant_entries
from anti_dating_scam.services.reflection_chat import ReflectionChatService

YOUTUBE = "https://www.youtube.com/watch?v=synthetic01"
TIKTOK = "https://www.tiktok.com/@synthetic/video/1234567890123456789"
BILIBILI = "https://www.bilibili.com/video/BV1234567890"


def pair(text="Photography", zh="摄影"):
    return {"en": text, "zh": zh}


def rows():
    return [
        {
            "url": YOUTUBE,
            "title": "Street composition",
            "transcript": "Framing light on a street.",
            "saved_at": "2026-08-01",
            "collection": "Camera",
        },
        {
            "url": TIKTOK,
            "title": "Camera equipment",
            "summary": "A lens comparison.",
            "annotation": "Saved for a work reference.",
            "collection": "Work",
        },
        {"url": BILIBILI, "title": "Photography editing"},
        {"url": "https://example.invalid/no-content"},
    ]


class SyntheticBackend:
    recipient = "https://synthetic.invalid/responses#test"

    def __init__(self):
        self.calls = []
        self.fail = set()
        self.cancel_after = None
        self.category = None
        self.bad_quote = False
        self.bad_synthesis = False

    def chat(self, request):
        outbound_messages(request, recipient=self.recipient, local=False)
        self.calls.append(request)
        data = json.loads(request.messages[0].content)
        if self.category:
            raise BackendError("synthetic", category=self.category)
        if isinstance(data, list):
            if self.bad_synthesis:
                return "{}"
            output = {
                field: [
                    {
                        "kind": kind,
                        "group_ids": [d["group_id"] for d in data],
                        "text": pair(
                            "I am interested in photography visuals.", "我对摄影视觉感兴趣。"
                        ),
                        "explanation": pair(
                            "Saved materials mention composition.", "收藏材料提到构图。"
                        ),
                        "uncertainty": pair(
                            "Participation and endorsement unknown.", "参与和赞同未知。"
                        ),
                        "pattern": "possible",
                    }
                ]
                for field, kind in (("findings", "interest"), ("reflection_drafts", "reflection"))
            }
            return json.dumps({**output, "questions": []})
        if data["video_id"] in self.fail:
            raise RuntimeError("PRIVATE PROVIDER BODY NEVER DISPLAY")
        material = (
            data["materials"][0]
            if data["materials"]
            else {
                "origin": "title",
                "text": data["title"],
            }
        )
        result = {
            "summary": pair("Supplied material about photography.", "提供的摄影相关材料。"),
            "topics": [{"broad": pair(), "specific": pair("Visual style", "视觉风格")}],
            "creator_claims": [],
            "evidence": [
                {
                    "video_id": data["video_id"],
                    "origin": material["origin"],
                    "quote": "FABRICATED" if self.bad_quote else material["text"][:100],
                }
            ],
            "sensitive": False,
        }
        if self.cancel_after:
            self.cancel_after.set()
        return json.dumps(result)


def create(tmp_path, incoming=None):
    service = BatchService(tmp_path)
    preview = preview_rows(rows() if incoming is None else incoming)
    batch = service.create(
        preview, [v.id for v in preview.videos], name="Synthetic", confirmed=True
    )
    return service, batch


def run(service, batch, backend=None, **kwargs):
    backend = backend or SyntheticBackend()
    grant = BatchGrant.approve(batch, backend, confirmed=True)
    return service.process(batch.id, backend, grant, **kwargs)


def test_mixed_dedup_canonical_identity_and_derivative_summary():
    preview = preview_rows(
        rows()
        + [
            {"url": "https://youtu.be/synthetic01?t=99", "summary": "Framing light on a street."},
            {"url": YOUTUBE + "&list=one", "transcript": "Framing light on a street."},
            {"url": "https://www.youtube.com/playlist?list=one"},
            {"url": "https://vm.tiktok.com/short"},
        ]
    )
    assert len(preview.videos) == 4 and preview.duplicates == 2 and preview.invalid == 2
    assert len(preview.videos[0].materials) == 1
    assert preview.videos[0].materials[0].origin == "transcript"
    assert (
        canonical_url("https://example.invalid/video?id=1")[2]
        != canonical_url("https://example.invalid/video?id=2")[2]
    )


def test_supported_exports_and_no_message_history_import(tmp_path):
    csv = tmp_path / "playlist.csv"
    csv.write_text(
        "Playlist Id,Channel Id,Title\nPL1,SYNTHETIC,Camera\n\n"
        "Video Id,Playlist Video Creation Timestamp\nsynthetic01,2026-08-01T10:00:00Z\n"
    )
    export = tmp_path / "saved.json"
    export.write_text(
        json.dumps(
            {
                "Likes and Favourites": {
                    "Like List": {"ItemFavoriteList": [{"Date": "2026-09-02", "Link": TIKTOK}]},
                    "Favourite Videos": [
                        {"Date": "2026-09-03", "Video landing page link": BILIBILI}
                    ],
                },
                "Direct Messages": {"Message": {"url": "https://example.invalid/PRIVATE"}},
                "Your Activity": {
                    "Watch History": [{"Link": "https://example.invalid/UNSELECTED"}]
                },
            }
        )
    )
    preview = import_files([csv, export])
    assert len(preview.videos) == 3 and all(v.saved_at for v in preview.videos)
    assert "PRIVATE" not in preview.model_dump_json()
    assert "UNSELECTED" not in preview.model_dump_json()
    assert len(parse_text("Date: 2026-09-01\nLink: " + TIKTOK)) == 1


def test_prepared_notes_provenance_hidden_and_duplicate(tmp_path):
    (tmp_path / "camera.md").write_text(
        YOUTUBE + "\n# Summary\nCreator shows light.\n# User annotation\nI like the visual style."
    )
    hidden = tmp_path / ".obsidian"
    hidden.mkdir()
    (hidden / "private.md").write_text(TIKTOK)
    (tmp_path / "derivative.md").write_text(YOUTUBE + "\n# Summary\nCreator shows light.")
    result = import_notes(tmp_path)
    assert len(result.videos) == 1 and result.duplicates == 1
    assert {m.origin for m in result.videos[0].materials} == {"existing_summary", "user_annotation"}
    assert len(result.videos[0].materials) == 2


def test_import_bounds_hardlinks_and_unknown_formats(tmp_path):
    original = tmp_path / "source.txt"
    original.write_text(YOUTUBE)
    hardlink = tmp_path / "linked.txt"
    os.link(original, hardlink)
    preview = import_files([hardlink])
    assert not preview.videos and preview.notices
    with pytest.raises(ValueError):
        parse_text("X" * 2_000_001)
    with pytest.raises(ValueError):
        parse_text('{"Direct Messages": {"Link": "https://example.invalid"}}', ".json")
    with pytest.raises(ValueError):
        canonical_url("https://example.invalid/video?access_token=do-not-store")


def test_batch_limit_and_duplicate_at_limit():
    incoming = [{"url": f"https://example.invalid/{i}"} for i in range(1000)]
    assert len(preview_rows(incoming + [incoming[0]]).videos) == 1000
    with pytest.raises(ValueError, match="batch_limit"):
        preview_rows(incoming + [{"url": "https://example.invalid/1001"}])


def test_pipeline_counts_group_review_existing_memory_and_undo(tmp_path):
    service, batch = create(tmp_path)
    backend = SyntheticBackend()
    result = run(service, batch, backend)
    assert result.counts() == dict(
        imported=4,
        pending=0,
        full=1,
        partial=2,
        skipped=1,
        failed=0,
        duplicates=0,
        invalid=0,
        reused=0,
    )
    assert len(backend.calls) == 4 and len(result.findings) == 2
    assert not service.memory.read().entries
    with pytest.raises(ValueError, match="memory_changed_or_disabled"):
        service.review(
            result.id, result.revision, [result.findings[0].id], action="confirm", confirmed=True
        )
    service.memory.change(0, action="enable", confirmed=True)
    result = service.review(
        result.id,
        result.revision,
        [f.id for f in result.findings],
        action="confirm",
        confirmed=True,
    )
    memory = service.memory.read()
    # Identical adopted wording is one memory even if offered under both headings.
    assert len(memory.entries) == 1 and memory.entries[0].external_evidence
    assert relevant_entries(memory, "photography")
    chat = ReflectionChatService()
    chat.bind_memory(service.memory)
    assert chat._memory.entries == memory.entries
    service.undo(result.id, confirmed=True)
    assert not service.list() and not service.memory.read().entries


def test_individual_failure_does_not_stop_batch_and_retry_reuses_successes(tmp_path):
    service, batch = create(tmp_path)
    backend = SyntheticBackend()
    backend.fail = {batch.items[0].video.id}
    result = run(service, batch, backend)
    assert result.counts()["failed"] == 1 and result.counts()["partial"] == 2
    assert "PRIVATE" not in result.model_dump_json()
    backend.fail.clear()
    count = len(backend.calls)
    result = run(service, result, backend, retry_failed=True)
    assert result.counts()["failed"] == 0 and len(backend.calls) == count + 2


def test_interruption_checkpoint_resume_and_late_reply_discard(tmp_path):
    service, batch = create(tmp_path)
    cancel = Event()
    progress = []

    def pause_after_one(b):
        progress.append(b)
        cancel.set()

    first = run(service, batch, cancel=cancel, progress=pause_after_one)
    assert first.state == "paused" and first.items[0].status == "full"
    assert len(progress) == 1
    resumed_backend = SyntheticBackend()
    resumed = run(service, first, resumed_backend)
    assert resumed.state == "complete" and len(resumed_backend.calls) == 3
    other_service, other = create(
        tmp_path, [{"url": "https://example.invalid/late", "title": "Light"}]
    )
    cancel = Event()
    late = SyntheticBackend()
    late.cancel_after = cancel
    paused = run(other_service, other, late, cancel=cancel)
    assert paused.items[0].status == "pending" and paused.items[0].analysis is None


@pytest.mark.parametrize("category", ["usage", "auth", "model"])
def test_plan_limit_stops_instead_of_retrying_every_item(tmp_path, category):
    service, batch = create(tmp_path)
    backend = SyntheticBackend()
    backend.category = category
    with pytest.raises(ValueError, match="batch_" + category):
        run(service, batch, backend)
    assert len(backend.calls) == 1 and service.read(batch.id).state == "paused"


def test_reimport_reuses_results_without_duplicate_memory_weight(tmp_path):
    service, original = create(tmp_path)
    original = run(service, original)
    service.memory.change(0, action="enable", confirmed=True)
    original = service.review(
        original.id, original.revision, [original.findings[0].id], action="confirm", confirmed=True
    )
    _, repeated = create(tmp_path)
    assert repeated.counts()["reused"] == 3
    backend = SyntheticBackend()
    repeated = run(service, repeated, backend)
    assert len(backend.calls) == 1
    repeated = service.review(
        repeated.id, repeated.revision, [repeated.findings[0].id], action="confirm", confirmed=True
    )
    before = service.memory.read()
    assert len(before.entries) == 1 and len(before.entries[0].batch_ids) == 2
    service.undo(original.id, confirmed=True)
    remaining = service.memory.read()
    assert len(remaining.entries) == 1 and remaining.entries[0].batch_ids == [repeated.id]
    assert all(e.batch_id == repeated.id for e in remaining.entries[0].external_evidence)
    service.undo(repeated.id, confirmed=True)
    assert not service.memory.read().entries and not service.list()


def test_correction_withdraws_previous_claim_until_readopted(tmp_path):
    service, batch = create(tmp_path)
    batch = run(service, batch)
    service.memory.change(0, action="enable", confirmed=True)
    key = batch.findings[0].id
    batch = service.review(batch.id, batch.revision, [key], action="confirm", confirmed=True)
    batch = service.review(
        batch.id,
        batch.revision,
        [key],
        action="revise",
        text="This was saved for work.",
        confirmed=True,
    )
    assert not service.memory.read().entries
    assert batch.findings[0].status == "draft"
    batch = service.review(batch.id, batch.revision, [key], action="confirm", confirmed=True)
    assert service.memory.read().entries[0].text == "This was saved for work."
    batch = service.review(batch.id, batch.revision, [key], action="reject", confirmed=True)
    assert not service.memory.read().entries
    with pytest.raises(ValueError, match="no_longer_active"):
        service.review(batch.id, batch.revision, [key], action="confirm", confirmed=True)


def test_scope_evidence_and_stale_review_fail_closed(tmp_path):
    service, batch = create(tmp_path)
    backend = SyntheticBackend()
    with pytest.raises(ValueError):
        BatchGrant.approve(batch, backend, confirmed=1)
    grant = BatchGrant.approve(batch, backend, confirmed=True)
    backend.recipient = "https://another.invalid"
    with pytest.raises(ValueError, match="scope_changed"):
        service.process(batch.id, backend, grant)
    backend = SyntheticBackend()
    backend.bad_quote = True
    result = run(service, batch, backend)
    assert result.counts()["failed"] == 3 and not result.findings
    result = run(service, result, retry_failed=True)
    with pytest.raises(ValueError, match="batch_changed"):
        service.review(result.id, 0, [result.findings[0].id], action="remove", confirmed=True)
    with pytest.raises(ValueError):
        service.undo(batch.id, confirmed=False)


def test_title_only_cannot_have_creator_claims_and_sensitive_extraction_rejected(tmp_path):
    service, batch = create(tmp_path)
    item = batch.items[2].video
    fake = SyntheticBackend()
    grant = BatchGrant.approve(batch, fake, confirmed=True)
    parsed = json.loads(grant.call(batch, fake, item_request(item)))
    parsed["creator_claims"] = [pair("Creator advocates saving money.", "作者主张省钱。")]
    with pytest.raises(ValueError, match="metadata"):
        validate_item(ItemAnalysis.model_validate(parsed), item)
    parsed["creator_claims"] = []
    parsed["summary"] = pair("User has a disorder.", "用户有诊断。")
    with pytest.raises(ValueError, match="sensitive"):
        validate_item(ItemAnalysis.model_validate(parsed), item)


def test_temporal_and_work_inferences_require_distinct_evidence(tmp_path):
    service, batch = create(tmp_path, [rows()[0], rows()[2]])
    batch = run(service, batch)
    groups, _ = group_items(batch)
    request, used = synthesis_request(groups)
    fake = SyntheticBackend()
    grant = BatchGrant.approve(batch, fake, confirmed=True)
    raw = json.loads(grant.call(batch, fake, request))
    for pattern, message in (
        ("recurring", "recurring"),
        ("aspirational", "annotation"),
        ("task_related", "annotation"),
    ):
        raw["findings"][0]["pattern"] = pattern
        with pytest.raises(ValueError, match=message):
            validate_synthesis(Synthesis.model_validate(raw), used)


def test_metadata_permission_identity_and_partial_failure(tmp_path):
    service, batch = create(tmp_path, [{"url": YOUTUBE}, {"url": TIKTOK}, {"url": BILIBILI}])

    class Fetcher:
        ENDPOINTS = PublicMetadata.ENDPOINTS

        def fetch(self, video):
            if video.source == "tiktok":
                raise OSError("PRIVATE DETAIL")
            return video.model_copy(update={"title": "Public photography title"})

    with pytest.raises(ValueError, match="scope"):
        service.fetch_metadata(batch.id, Fetcher(), approved_digest="changed", confirmed=True)
    batch = service.fetch_metadata(
        batch.id, Fetcher(), approved_digest=batch.digest, confirmed=True
    )
    assert batch.items[0].video.title and batch.items[1].error == "metadata_unavailable"
    assert not batch.items[2].video.title
    assert "PRIVATE" not in batch.model_dump_json()
    with pytest.raises(ValueError, match="unsupported"):
        PublicMetadata().fetch(batch.items[2].video)


def test_synthesis_failure_resume_and_export_does_not_include_raw_material(tmp_path):
    service, batch = create(tmp_path)
    fake = SyntheticBackend()
    fake.bad_synthesis = True
    with pytest.raises(ValueError):
        run(service, batch, fake)
    saved = service.read(batch.id)
    assert saved.state == "failed" and saved.counts()["pending"] == 0
    fake.bad_synthesis = False
    count = len(fake.calls)
    result = run(service, saved, fake)
    assert len(fake.calls) == count + 1 and result.findings
    destination = tmp_path / "result.json"
    service.export(result.id, destination)
    exported = json.loads(destination.read_text(encoding="utf-8"))
    assert "items" not in exported and exported["findings"][1]["status"] == "draft"
    with pytest.raises(FileExistsError):
        service.export(result.id, destination)


def test_identical_content_in_another_batch_needs_its_own_grant(tmp_path):
    service, first = create(tmp_path)
    _, second = create(tmp_path)
    backend = SyntheticBackend()
    assert first.digest == second.digest
    grant = BatchGrant.approve(first, backend, confirmed=True)
    with pytest.raises(ValueError, match="scope_changed"):
        service.process(second.id, backend, grant)
    assert not backend.calls


def test_repeated_support_survives_removing_recent_copies_without_extra_context(tmp_path):
    service, first = create(tmp_path)
    service.memory.change(0, action="enable", confirmed=True)
    batches = [first]
    for index in range(6):
        batch = batches[0] if index == 0 else create(tmp_path)[1]
        result = run(service, batch)
        service.review(
            result.id, result.revision, [result.findings[0].id], action="confirm", confirmed=True
        )
        if index:
            batches.append(batch)
    memory = service.memory.read()
    entry = memory.entries[0]
    assert len(memory.entries) == 1 and len(entry.batch_ids) == 6
    assert len(entry.external_evidence) == 18
    assert len(entry.context_payload()["external_evidence"]) == 3
    for batch in reversed(batches[1:]):
        service.undo(batch.id, confirmed=True)
    remaining = service.memory.read().entries[0]
    assert remaining.batch_ids == [first.id] and len(remaining.external_evidence) == 3


def test_merge_requires_same_kind_and_reapproval_then_undo_cascades(tmp_path):
    service, batch = create(tmp_path)
    batch = run(service, batch)
    interest = batch.findings[0]
    other = interest.model_copy(
        update={
            "id": uuid4().hex,
            "specific": interest.specific.model_copy(update={"en": "Equipment"}),
            "text": interest.text.model_copy(update={"en": "I explore camera equipment."}),
        }
    )
    batch = service.save(batch.model_copy(update={"findings": batch.findings + [other]}))
    with pytest.raises(ValueError, match="same_kind"):
        service.review(
            batch.id,
            batch.revision,
            [f.id for f in batch.findings],
            action="merge",
            text="Combined",
            confirmed=True,
        )
    service.memory.change(0, action="enable", confirmed=True)
    batch = service.review(
        batch.id, batch.revision, [interest.id, other.id], action="confirm", confirmed=True
    )
    assert len(service.memory.read().entries) == 2
    batch = service.review(
        batch.id,
        batch.revision,
        [interest.id, other.id],
        action="merge",
        text="I explore photography for work.",
        confirmed=True,
    )
    assert not service.memory.read().entries
    merged = batch.findings[-1]
    assert merged.status == "draft" and len(merged.evidence) == 3
    batch = service.review(batch.id, batch.revision, [merged.id], action="confirm", confirmed=True)
    memory = service.memory.read()
    child = memory.entries[0].model_copy(
        update={
            "id": uuid4().hex,
            "text": "A dependent tentative idea.",
            "external_key": "",
            "batch_ids": [],
            "external_evidence": [],
            "source": "manual",
            "depends_on": [memory.entries[0].id],
        }
    )
    service.memory._commit(
        memory,
        memory.entries + [child],
        enabled=True,
        action="synthetic_dependency",
        ids=[child.id],
    )
    service.undo(batch.id, confirmed=True)
    assert not service.memory.read().entries


def test_stale_checkpoint_cannot_restore_removed_data(tmp_path):
    service, batch = create(tmp_path)
    latest = service.save(batch)
    with pytest.raises(ValueError, match="batch_changed"):
        service.save(batch)
    service.undo(latest.id, confirmed=True)
    with pytest.raises(FileNotFoundError):
        service.save(latest)
    assert not service.list()


def test_long_supplied_transcript_is_partial_and_synthesis_is_bounded(tmp_path):
    incoming = [dict(rows()[0], transcript="Synthetic composition. " * 190)]
    service, batch = create(tmp_path, incoming)
    result = run(service, batch)
    assert result.counts()["partial"] == 1 and result.counts()["full"] == 0
    example = result.items[0]
    items = []
    for index in range(40):
        topic = example.analysis.topics[0].model_copy(
            update={
                "specific": example.analysis.topics[0].specific.model_copy(
                    update={"en": f"Distinct topic {index}"}
                )
            }
        )
        items.append(
            example.model_copy(
                update={
                    "video": example.video.model_copy(update={"id": f"{index:064x}"}),
                    "analysis": example.analysis.model_copy(update={"topics": [topic]}),
                }
            )
        )
    groups, omitted = group_items(result.model_copy(update={"items": items}))
    request, used = synthesis_request(groups)
    assert len(groups) == 24 and omitted == 16 and used
    assert len(request.messages[0].content) <= 23_000


def test_recorded_real_synthetic_outputs_replay_with_strict_attribution(tmp_path):
    # Offline regression of real outputs; this test makes no model or network calls.
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "batch_smoke", root / "scripts/smoke_video_batch.py"
    )
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    evidence = root / "docs/evidence"
    first = json.loads((evidence / "2026-10-02-video-batch-plan.json").read_text(encoding="utf-8"))
    final = json.loads((evidence / "2026-10-02-video-batch-final.json").read_text(encoding="utf-8"))
    outputs = iter([c["output"] for c in first["calls"][:3]] + [final["calls"][0]["output"]])

    class RecordedBackend(SyntheticBackend):
        def chat(self, request):
            outbound_messages(request, recipient=self.recipient, local=False)
            return json.dumps(next(outputs))

    service, batch = create(tmp_path, smoke.SYNTHETIC)
    result = run(service, batch, RecordedBackend())
    assert len(result.findings) == 4 and result.findings[-1].kind == "reflection"
    assert not service.memory.read().entries
    groups, _ = group_items(result)
    request, used = synthesis_request(groups)
    assert request.response_schema["properties"]["reflection_drafts"]["minItems"] == 1
    raw = final["calls"][0]["output"]
    with pytest.raises(ValueError, match="reflection_draft_required"):
        validate_synthesis(Synthesis.model_validate({**raw, "reflection_drafts": []}), used)
