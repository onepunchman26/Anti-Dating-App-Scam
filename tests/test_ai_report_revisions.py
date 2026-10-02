"""Quote-limited AI-assisted copies preserve attribution and exact review context."""

import json
import os
from pathlib import Path

import pytest
from test_report_replacements import _fixture

from anti_dating_scam.services.report_review import _encode, _hash
from anti_dating_scam.services.report_revisions import (
    AIReplacementContext,
    AIReplacementPreview,
    AIReplacementProposal,
    ReportRevisionError,
    ReportRevisionService,
)


def _setup(tmp_path, kind="self_portrait", **kwargs):
    service, reviews, source, proposal, canonical = _fixture(tmp_path, kind, **kwargs)
    digest = reviews.inspect(kind).report_digest
    context = service.context_for_ai_replacement(
        kind, proposal.correction_id, expected_digest=digest,
    )
    assisted = AIReplacementProposal(
        **proposal.model_dump(), context_digest=context.context_digest, request_digest="a" * 64,
    )
    return service, reviews, source, assisted, canonical, context


def _preview(service, proposal, context):
    return service.preview_ai_replacement(
        context.kind, proposal, expected_digest=context.source_digest,
    )


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_context_contains_only_selected_claim_annotation_and_exact_input_binding(tmp_path, kind):
    service, reviews, source, proposal, canonical, context = _setup(tmp_path, kind)
    assert isinstance(context, AIReplacementContext)
    assert set(context.model_dump()) == {
        "kind", "source_digest", "context_digest", "correction", "original_claim",
    }
    assert context.original_claim.path == context.correction.target_path
    assert context.original_claim.claim == context.correction.original_claim
    assert context.correction.id == proposal.correction_id
    assert context.original_claim.evidence[0].source == "../unread-label"
    assert context.source_digest == _hash(source.read_bytes())
    sources = {
        "source_report.json": source,
        "source_localization.json": source.with_name(f"{kind}_localization.json"),
    }
    if kind == "mate_criteria":
        sources["source_ideal_profiles.json"] = source.with_name("ideal_partner_profiles.json")
    note = reviews._history(kind) / proposal.correction_id / "correction.json"
    assert context.context_digest == _hash(_encode({
        "kind": kind,
        "sources": {name: _hash(path.read_bytes()) for name, path in sources.items()},
        "notes": {proposal.correction_id: _hash(note.read_bytes())},
    }))
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_bilingual_attribution_uncertainty_originals_and_history_survive_user_edits(tmp_path, kind):
    service, reviews, source, proposal, canonical, context = _setup(tmp_path, kind)
    originals = {p: p.read_bytes() for p in source.parent.rglob("*") if p.is_file()}
    proposal = proposal.model_copy(update={
        "text_en": "Edited: this one example might reflect the context.",
        "text_zh": "编辑后的措辞：这个例子可能体现了当时的情境。",
    })
    preview = _preview(service, proposal, context)
    assert isinstance(preview, AIReplacementPreview)
    assert preview.operation == "ai_replace_claim"
    assert preview.proposal.origin == "ai_assisted"
    assert "AI-assisted interpretation" in preview.markdown.replace("\\", "")
    assert "AI 辅助解释" in preview.markdown
    assert "仅依据已有引文，未经核实" in preview.markdown
    assert "User-proposed interpretation" not in preview.markdown
    assert "ANNOTATION_NOT_AUTOMATIC_FACT" not in preview.markdown
    assert preview.replacement_claim.type == "speculation"
    assert preview.replacement_claim.confidence == "low"
    for name in ("evidence", "topic", "path"):
        assert getattr(preview.replacement_claim, name) == getattr(context.original_claim, name)
    saved = service.save_ai_replacement(preview, confirmed=True)
    folder = Path(saved.directory_path)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    assert manifest["schema_version"] == "0.3"
    assert manifest["operation"] == "ai_replace_claim"
    assert (folder / "proposal.json").read_bytes() == _encode(proposal.model_dump(mode="json"))
    assert (folder / "source_report.json").read_bytes() == originals[source]
    assert all(p.read_bytes() == raw for p, raw in originals.items())
    restarted = ReportRevisionService(source.parent.parent)
    assert restarted.read_revision(kind, saved.id) == preview
    bundle = restarted.read_verified_bundle(kind, saved.id)
    root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "revealed")
    assert bundle.canonical[root][group][0] == canonical[root][group][0]
    assert bundle.canonical[root]["caveats"][:-1] == canonical[root]["caveats"]
    assert "do not prove a model call" in bundle.canonical[root]["caveats"][-1]
    if kind == "self_portrait":
        assert bundle.canonical[root]["consistency_findings"] == []
        assert "headline" not in bundle.canonical[root] and "summary" not in bundle.canonical[root]
    else:
        assert bundle.canonical["ideal_profiles"]["candidates"] == []
        assert "No AI analysis occurred" not in bundle.markdown
    assert not (source.parent / "active_selections").exists()
    # Saved history uses retained snapshots even when the current writer changes.
    source.write_bytes(b"new invalid current report")
    assert restarted.read_revision(kind, saved.id) == preview


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true"])
def test_ai_save_requires_strict_separate_confirmation(tmp_path, confirmed):
    service, _, source, proposal, _, context = _setup(tmp_path)
    with pytest.raises(ReportRevisionError):
        service.save_ai_replacement(_preview(service, proposal, context), confirmed=confirmed)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("member", ["source", "locale", "ideal", "note"])
@pytest.mark.parametrize("stage", ["preview", "save"])
def test_context_rejects_every_exact_source_or_note_byte_change(tmp_path, member, stage):
    service, reviews, source, proposal, _, context = _setup(tmp_path, "mate_criteria")
    preview = _preview(service, proposal, context)
    target = {
        "source": source,
        "locale": source.with_name("mate_criteria_localization.json"),
        "ideal": source.with_name("ideal_partner_profiles.json"),
        "note": reviews._history(context.kind) / proposal.correction_id / "correction.json",
    }[member]
    target.write_bytes(target.read_bytes() + b" \r\n")
    with pytest.raises(ReportRevisionError):
        if stage == "preview":
            _preview(service, proposal, context)
        else:
            service.save_ai_replacement(preview, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("changes", [
    {"context_digest": "b" * 64}, {"context_digest": "bad"},
    {"request_digest": "bad"}, {"origin": "user"}, {"correction_id": "0" * 32},
    {"text_en": ""}, {"text_zh": "English only"}, {"text_zh": "中文" * 2001},
])
def test_unvalidated_proposals_are_revalidated_without_echoing_private_input(tmp_path, changes):
    service, _, source, proposal, _, context = _setup(tmp_path)
    with pytest.raises(ReportRevisionError) as caught:
        _preview(service, proposal.model_copy(update=changes), context)
    assert "ANNOTATION" not in str(caught.value) and "Synthetic" not in str(caught.value)
    assert not (source.parent / "reviewed_copies").exists()


def test_ai_proposals_cannot_pass_as_user_only_proposals_or_withdrawal(tmp_path):
    service, _, source, proposal, _, context = _setup(tmp_path)
    preview = _preview(service, proposal, context)
    with pytest.raises(ReportRevisionError):
        service.preview_replacement(context.kind, proposal, expected_digest=context.source_digest)
    with pytest.raises(ReportRevisionError):
        service.save_replacement(preview, confirmed=True)
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(preview, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("field", ["markdown", "proposal", "replacement_claim"])
def test_modified_preview_is_rejected(tmp_path, field):
    service, _, source, proposal, _, context = _setup(tmp_path)
    preview = _preview(service, proposal, context)
    altered = {
        "markdown": preview.markdown + "NOT_REVIEWED",
        "proposal": proposal.model_copy(update={"request_digest": "b" * 64}),
        "replacement_claim": preview.replacement_claim.model_copy(update={"confidence": "high"}),
    }[field]
    with pytest.raises(ReportRevisionError):
        service.save_ai_replacement(preview.model_copy(update={field: altered}), confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("member", [
    "proposal.json", "preview.json", "report.json", "report.md", "source_localization.json",
])
def test_tampered_saved_members_fail_closed(tmp_path, member):
    service, _, source, proposal, _, context = _setup(tmp_path)
    saved = service.save_ai_replacement(_preview(service, proposal, context), confirmed=True)
    path = Path(saved.directory_path) / member
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ReportRevisionError):
        service.read_revision(context.kind, saved.id)


@pytest.mark.parametrize("limit", ["report", "profiles"])
def test_original_warnings_are_never_dropped_to_fit_ai_notice(tmp_path, limit):
    counts = {"caveat_count": 30} if limit == "report" else {"profile_caveat_count": 30}
    service, _, source, proposal, _, context = _setup(tmp_path, "mate_criteria", **counts)
    with pytest.raises(ReportRevisionError):
        _preview(service, proposal, context)
    assert not (source.parent / "reviewed_copies").exists()


def test_write_failure_keeps_originals_and_commits_no_copy(tmp_path, monkeypatch):
    service, _, source, proposal, _, context = _setup(tmp_path)
    preview = _preview(service, proposal, context)
    original = source.read_bytes()

    def fail_rename(*args, **kwargs):
        raise OSError("synthetic rename failure")

    monkeypatch.setattr(os, "rename", fail_rename)
    with pytest.raises(ReportRevisionError):
        service.save_ai_replacement(preview, confirmed=True)
    assert source.read_bytes() == original
    assert service.list_revisions(context.kind) == []


def test_evidence_source_labels_are_never_followed(tmp_path, monkeypatch):
    service, reviews, source, proposal, _, context = _setup(tmp_path)
    visited = []
    read = service._review._read

    def tracking_read(path, limit):
        visited.append(path)
        assert path.name != "unread-label"
        return read(path, limit)

    monkeypatch.setattr(service._review, "_read", tracking_read)
    current = service.context_for_ai_replacement(
        context.kind, proposal.correction_id, expected_digest=context.source_digest,
    )
    preview = _preview(service, proposal, current)
    service.save_ai_replacement(preview, confirmed=True)
    assert visited
    assert all(path.is_relative_to(source.parent) for path in visited)
