"""Full regenerated reports remain attributed references, never implicit evidence."""

import json
from pathlib import Path

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.self_portrait_html import render_self_portrait_html
from test_full_report_regeneration import _paired
from test_report_replacement_consumers import (
    ANNOTATION,
    REASON,
    _assert_originals,
    _client,
    _literal,
    _seed,
    _select,
)

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam.services.evidence_paths import list_evidence_files
from anti_dating_scam.services.report_full_regeneration import FullReportRegenerationService
from anti_dating_scam.services.report_full_regeneration_contract import RegenerationExcerpt
from anti_dating_scam.services.report_revisions import ReportRevisionError

QUOTE = "I paused before replying because I was tired."
UNQUOTED = "UNQUOTED_EXCERPT_CONTENT_NOT_FOR_REPORT_REFERENCES"
CLAIM = "The supplied episode describes a pause while tired."


def full_bundle(kind):
    claim = {
        "topic": "communication",
        "type": "observation",
        "confidence": "high",
        "claim": CLAIM,
        "evidence": [{"quote": QUOTE, "source": "S001"}],
    }
    common = {
        "report_type": kind,
        "open_questions": [],
        "caveats": ["One supplied episode cannot establish a stable pattern."],
    }
    if kind == "self_portrait":
        canonical = {
            "report": {
                **common,
                "schema_version": "0.2",
                "claims": [claim],
                "data_coverage": {"sources_read": ["S001"], "covered": [], "not_covered": []},
                "consistency_findings": [],
            }
        }
    else:
        canonical = {
            "criteria": {**common, "schema_version": "0.1", "stated": [claim], "revealed": []},
            "ideal_profiles": {
                "schema_version": "0.1",
                "candidates": [],
                "caveats": ["No fictional profiles were generated."],
            },
        }
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成译文第{index}项。"}
        for index, (path, text) in enumerate(required_localization_sources(kind, canonical).items())
    ]
    return {**canonical, "localized_text": entries}


def generated_preview(store, revisions, correction, digest, kind="self_portrait"):
    service = FullReportRegenerationService(store.base_dir)
    prepared = service.prepare(
        kind,
        [correction.id],
        [RegenerationExcerpt(text=QUOTE + "\n" + UNQUOTED)],
        expected_digest=digest,
    )
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        return {"message": {"content": json.dumps(_paired(full_bundle(kind)), ensure_ascii=False)}}

    proposal = service.generate(
        prepared,
        OllamaChatBackend(
            model="synthetic-full-regeneration",
            transport=transport,
        ),
        confirmed=True,
    )
    assert len(calls) == 1
    return revisions.preview_full_regeneration(kind, proposal, expected_digest=digest)


def assert_regeneration_notice(text):
    literal = _literal(text)
    assert "regenerat" in literal.lower()
    assert "AI" in literal and "unverified" in literal.lower()
    assert "重新生成" in literal and "未经核实" in literal


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_full_generation_save_reopen_select_preserves_originals_and_uncertainty(tmp_path, kind):
    store, revisions, correction, digest, originals = _seed(
        tmp_path,
        kind,
        "claims" if kind == "self_portrait" else "stated",
    )
    preview = generated_preview(store, revisions, correction, digest, kind)
    saved = revisions.save_full_regeneration(preview, confirmed=True)
    assert ActiveReportService(store.base_dir).resolve(kind) is None
    assert revisions.read_revision(kind, saved.id) == preview
    manifest = json.loads((Path(saved.directory_path) / "manifest.json").read_text("utf-8"))
    assert manifest["schema_version"] == "0.4" and manifest["operation"] == "regenerate_report"
    resolved = _select(ActiveReportService(store.base_dir), kind, saved.id)
    report = resolved.canonical["report" if kind == "self_portrait" else "criteria"]
    claims = report["claims" if kind == "self_portrait" else "stated"]
    assert len(claims) == 1 and CLAIM in claims[0]["claim"]
    assert claims[0]["evidence"] == [{"quote": QUOTE, "source": "S001"}]
    assert claims[0]["confidence"] == "low"
    assert "Original uncertainty must remain." in report["caveats"]
    assert_regeneration_notice(resolved.detailed_markdown or resolved.markdown)
    for value in (ANNOTATION, REASON, UNQUOTED, "UNCHANGED_SECOND_CLAIM"):
        assert value not in resolved.markdown
    assert list_evidence_files(Path(saved.directory_path)) == []
    assert list_evidence_files(Path(saved.directory_path) / "regeneration.json") == []
    _assert_originals(originals)


def test_new_excerpt_snapshots_are_not_promoted_by_browser_or_desktop_references(tmp_path):
    store, revisions, correction, digest, originals = _seed(tmp_path)
    saved = revisions.save_full_regeneration(
        generated_preview(store, revisions, correction, digest),
        confirmed=True,
    )
    selected = _select(ActiveReportService(store.base_dir), "self_portrait", saved.id)
    reference, _ = ai_backend.interview_reference_snapshot(store)
    assert_regeneration_notice(reference)
    assert_regeneration_notice(store.load_self_portrait())
    assert_regeneration_notice(
        render_self_portrait_html(
            selected.canonical["report"],
            selected.localized_text,
        )
    )
    for builder in (
        agent_handoff.build_criteria_interview_request,
        agent_handoff.build_criteria_interview_prompt,
    ):
        handoff = builder(store.base_dir)
        assert_regeneration_notice(handoff)
        assert UNQUOTED not in handoff and ANNOTATION not in handoff
    client, recorder = _client(store)
    with client:
        response = client.get("/local/report")
        assert response.status_code == 200
        assert_regeneration_notice(response.json()["md"])
        assert (
            client.post(
                "/local/ai/chat",
                json={
                    "messages": [{"role": "user", "content": "A synthetic new question."}],
                },
            ).status_code
            == 200
        )
    user = str([m for m in recorder.messages if m["role"] == "user"])
    assistant = str([m for m in recorder.messages if m["role"] == "assistant"])
    assert CLAIM not in user and "OWNER_INPUT_ONLY" in user
    assert CLAIM in _literal(assistant)
    assert_regeneration_notice(assistant)
    assert UNQUOTED not in str(recorder.messages) and ANNOTATION not in str(recorder.messages)
    _assert_originals(originals)


@pytest.mark.parametrize("member", ["self_portrait.json", "self_portrait_localization.json"])
def test_source_change_blocks_full_copy_use_but_history_remains_readable(tmp_path, member):
    store, revisions, correction, digest, _ = _seed(tmp_path)
    preview = generated_preview(store, revisions, correction, digest)
    saved = revisions.save_full_regeneration(preview, confirmed=True)
    _select(ActiveReportService(store.base_dir), "self_portrait", saved.id)
    source = store.reports_dir / member
    source.write_bytes(source.read_bytes() + b"\n ")
    with pytest.raises(ReportRevisionError):
        revisions.save_full_regeneration(preview, confirmed=True)
    with pytest.raises(ActiveReportError):
        ai_backend.build_interview_reference(store)
    client, recorder = _client(store)
    with client:
        assert client.get("/local/report").status_code == 409
    assert recorder.messages == []
    assert revisions.read_revision("self_portrait", saved.id) == preview
