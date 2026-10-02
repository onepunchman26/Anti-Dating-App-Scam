"""AI-assisted copies remain attributed references across existing consumers."""

import json
from pathlib import Path

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.self_portrait_html import render_self_portrait_html
from test_report_replacement_consumers import (
    ANNOTATION,
    CASES,
    QUOTE,
    REASON,
    SOURCE,
    _assert_originals,
    _client,
    _literal,
    _seed,
    _select,
)

from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam.services.evidence_paths import list_evidence_files
from anti_dating_scam.services.report_revisions import (
    AIReplacementProposal,
    ReplacementProposal,
    ReportRevisionError,
    ReportRevisionService,
)

DRAFT_EN = "A synthetic AI draft: this single quotation may reflect a temporary response."
DRAFT_ZH = "合成 AI 草稿：这一条引文可能反映当时的反应。"


def _ai_preview(service, correction, digest, kind="self_portrait"):
    context = service.context_for_ai_replacement(
        kind, correction.id, expected_digest=digest,
    )
    proposal = AIReplacementProposal(
        correction_id=correction.id, text_en=DRAFT_EN, text_zh=DRAFT_ZH,
        context_digest=context.context_digest, request_digest="a" * 64,
    )
    return service.preview_ai_replacement(kind, proposal, expected_digest=digest)


def _assert_ai_attribution(text):
    literal = _literal(text)
    assert "AI-assisted" in literal
    assert "AI 辅助" in literal
    assert "unverified" in literal.lower()
    assert "未经核实" in literal
    assert "User-proposed interpretation (unverified):" not in literal
    assert "用户提出的解释（未经核实）：" not in literal


@pytest.mark.parametrize("kind,group", CASES)
def test_all_three_revision_formats_coexist_and_selection_keeps_ai_attribution(
    tmp_path, kind, group,
):
    store, service, correction, digest, originals = _seed(tmp_path, kind, group)
    withdrawal = service.save_withdrawals(service.preview_withdrawals(
        kind, [correction.id], expected_digest=digest,
    ), confirmed=True)
    manual = service.save_replacement(service.preview_replacement(kind, ReplacementProposal(
        correction_id=correction.id, text_en="My synthetic proposal.", text_zh="我的合成提议。",
    ), expected_digest=digest), confirmed=True)
    older = {path: path.read_bytes() for item in (withdrawal, manual)
             for path in Path(item.directory_path).iterdir()}
    preview = _ai_preview(service, correction, digest, kind)
    saved = service.save_ai_replacement(preview, confirmed=True)
    assert ActiveReportService(store.base_dir).resolve(kind) is None
    reopened = ReportRevisionService(store.base_dir).read_revision(kind, saved.id)
    assert reopened == preview
    assert len(service.list_revisions(kind)) == 3
    selected = _select(ActiveReportService(store.base_dir), kind, saved.id)
    report = selected.canonical["report" if kind == "self_portrait" else "criteria"]
    claim = report[group][0]
    assert claim["evidence"] == [{"quote": QUOTE, "source": SOURCE}]
    assert claim["type"] == "speculation" and claim["confidence"] == "low"
    assert report[group][1]["claim"] == "UNCHANGED_SECOND_CLAIM"
    _assert_ai_attribution(selected.detailed_markdown or selected.markdown)
    assert ANNOTATION not in selected.markdown and REASON not in selected.markdown
    _assert_originals(originals)
    _assert_originals(older)


def test_desktop_browser_handoff_keep_ai_copy_out_of_original_evidence(tmp_path):
    store, service, correction, digest, originals = _seed(tmp_path)
    saved = service.save_ai_replacement(_ai_preview(service, correction, digest), confirmed=True)
    selected = _select(ActiveReportService(store.base_dir), "self_portrait", saved.id)
    reference, _ = ai_backend.interview_reference_snapshot(store)
    _assert_ai_attribution(reference)
    _assert_ai_attribution(store.load_self_portrait())
    _assert_ai_attribution(render_self_portrait_html(
        selected.canonical["report"], selected.localized_text,
    ))
    for builder in (agent_handoff.build_criteria_interview_request,
                    agent_handoff.build_criteria_interview_prompt):
        handoff = builder(store.base_dir)
        payload = json.loads(handoff.split("```json\n", 1)[1].split("\n```", 1)[0])
        assert set(payload) == {"unverified_generated_reference"}
        _assert_ai_attribution(payload["unverified_generated_reference"])
        assert ANNOTATION not in handoff and REASON not in handoff
    client, backend = _client(store)
    with client:
        response = client.get("/local/report")
        assert response.status_code == 200
        _assert_ai_attribution(response.json()["md"])
        assert client.post("/local/ai/chat", json={
            "messages": [{"role": "user", "content": "Synthetic current question."}],
        }).status_code == 200
    user_text = _literal(str([m for m in backend.messages if m["role"] == "user"]))
    assistant_text = _literal(str([m for m in backend.messages if m["role"] == "assistant"]))
    assert "OWNER_INPUT_ONLY" in user_text and DRAFT_EN not in user_text
    assert DRAFT_EN in assistant_text
    _assert_ai_attribution(assistant_text)
    assert ANNOTATION not in str(backend.messages) and REASON not in str(backend.messages)
    assert list_evidence_files(Path(saved.directory_path)) == []
    _assert_originals(originals)


def test_changed_translation_stops_selected_ai_reference_but_saved_history_reopens(tmp_path):
    store, service, correction, digest, _ = _seed(tmp_path)
    preview = _ai_preview(service, correction, digest)
    saved = service.save_ai_replacement(preview, confirmed=True)
    _select(ActiveReportService(store.base_dir), "self_portrait", saved.id)
    locale = store.reports_dir / "self_portrait_localization.json"
    locale.write_bytes(locale.read_bytes() + b"\n ")
    with pytest.raises(ReportRevisionError):
        service.save_ai_replacement(preview, confirmed=True)
    with pytest.raises(ActiveReportError):
        ai_backend.build_interview_reference(store)
    client, backend = _client(store)
    with client:
        assert client.get("/local/report").status_code == 409
        assert client.post("/local/ai/chat", json={
            "messages": [{"role": "user", "content": "Synthetic question."}],
        }).status_code == 409
    assert backend.messages == []
    assert service.read_revision("self_portrait", saved.id) == preview
