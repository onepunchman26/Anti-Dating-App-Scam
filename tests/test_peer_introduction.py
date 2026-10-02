"""Synthetic selected-memory generation and consent/evidence regression tests."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from test_peer_coordinator import invitation, member, node, profile  # noqa: F401

from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.matchmaking.peer_models import AdultDeclaration, PeerReport, ProfileUpdate
from anti_dating_scam.services.dating_introduction import IntroductionFormat, IntroductionService
from anti_dating_scam.services.peer_ai import comparison_request, generate_comparison


class SyntheticBackend:
    recipient = "https://synthetic.invalid"

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def chat(self, request):
        self.calls.append(request)
        return json.dumps(self.reply)


def reviewed(request, backend):
    return build_reviewed_request(
        request.messages, system=request.system, recipient=backend.recipient
    ).model_copy(
        update={"response_schema": request.response_schema, "allow_schema_fallback": False}
    )


def seeded(vault):
    service = IntroductionService(vault)
    state = service.memory.change(0, confirmed=True, action="add", text="I enjoy reading.")
    service.memory.change(state.revision, confirmed=True, action="enable")
    eligible = AdultDeclaration(age=30, adult_confirmed=True)
    source = service.list_sources(eligible)[0]
    request = service.prepare(eligible, [source["id"]], [], IntroductionFormat())
    response = {
        "fields": [
            {
                "label": "About me",
                "text": "I enjoy reading.",
                "evidence": [{"source": source["id"], "quote": "I enjoy reading."}],
            },
            {"label": "What I value", "text": "", "evidence": []},
        ],
        "missing": ["What I value"],
    }
    return service, eligible, source, request, response


def test_generate_edit_approve_export_and_corrected_source(tmp_path):
    service, eligible, source, request, response = seeded(tmp_path)
    backend = SyntheticBackend(response)
    draft = service.generate(backend, reviewed(request, backend))
    assert draft.missing == ["What I value"] and not (tmp_path / ".dating-introduction").exists()
    with pytest.raises(ValueError, match="approval_required"):
        service.approve({"About me": "Reading", "What I value": ""}, confirmed=False)
    approved = service.approve({"About me": "I like reading.", "What I value": ""}, confirmed=True)
    assert approved["source_ids"] == [source["id"]]
    service.export(tmp_path / "intro.json", as_json=True)
    exported = json.loads((tmp_path / "intro.json").read_text())
    assert set(exported) == {"About me", "What I value"}
    with pytest.raises(FileExistsError):
        service.export(tmp_path / "intro.json")
    state = service.memory.read()
    service.memory.change(
        state.revision,
        action="correct",
        entry_id=source["id"],
        text="I prefer music.",
        confirmed=True,
    )
    with pytest.raises(ValueError, match="source_changed"):
        service.read_approved()
    with pytest.raises(ValueError, match="source_changed"):
        service.generate(backend, reviewed(request, backend))
    assert len(backend.calls) == 1


@pytest.mark.parametrize(
    "mutation", ["invented_source", "bad_quote", "no_evidence", "private", "labels", "long"]
)
def test_reject_invalid_drafts(tmp_path, mutation):
    service, _, _, request, response = seeded(tmp_path)
    first = response["fields"][0]
    if mutation == "invented_source":
        first["evidence"][0]["source"] = "0" * 32
    if mutation == "bad_quote":
        first["evidence"][0]["quote"] = "not approved"
    if mutation == "no_evidence":
        first["evidence"] = []
    if mutation == "private":
        first["text"] = "My ex has a diagnosis."
    if mutation == "labels":
        first["label"] = "Invented platform field"
    if mutation == "long":
        first["text"] = "x" * 801
    backend = SyntheticBackend(response)
    with pytest.raises(ValueError):
        service.generate(backend, reviewed(request, backend))
    assert service.draft is None


def test_selection_excludes_private_inferred_disabled_and_requires_old_reconfirmation(tmp_path):
    service, eligible, source, _, _ = seeded(tmp_path)
    for text, kind in [
        ("My childhood trauma", "self_report"),
        ("My ex likes music", "self_report"),
        ("May be avoidant", "interpretation"),
    ]:
        service.memory.change(
            service.memory.read().revision, action="add", confirmed=True, text=text, kind=kind
        )
    assert [s["id"] for s in service.list_sources(eligible)] == [source["id"]]
    path = service.memory.directory / "state.json"
    document = json.loads(path.read_text())
    document["entries"][0]["approved_at"] = (datetime.now(UTC) - timedelta(days=91)).isoformat()
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="reconfirm_outdated"):
        service.prepare(eligible, [source["id"]], [], IntroductionFormat())
    service.prepare(eligible, [source["id"]], [source["id"]], IntroductionFormat())
    service.memory.change(service.memory.read().revision, action="revoke", confirmed=True)
    assert service.list_sources(eligible) == []


def test_cancellation_during_response_cannot_restore_draft(tmp_path):
    service, _, _, request, response = seeded(tmp_path)
    backend = SyntheticBackend(response)
    original = backend.chat

    def cancel(request):
        service.cancel_generation()
        return original(request)

    backend.chat = cancel
    with pytest.raises(ValueError, match="source_changed"):
        service.generate(backend, reviewed(request, backend))
    assert service.draft is None
    with pytest.raises(ValidationError):
        IntroductionFormat(fields=["About me", "About me"])


def test_old_response_does_not_destroy_replacement_draft(tmp_path):
    service, adult, source, request, response = seeded(tmp_path)
    old = service.prepared
    next_request = service.prepare(adult, [source["id"]], [], IntroductionFormat())
    backend = SyntheticBackend(response)
    newer = service.generate(backend, reviewed(next_request, backend))
    with pytest.raises(ValueError, match="source_changed"):
        service._current(old)
    assert service.draft is newer
    assert json.loads(request.messages[0].content)["eligibility"]["adult_confirmed"] is True


def report_data(sources):
    a = next(s for s in sources if s["id"].startswith("A"))
    b = next(s for s in sources if s["id"].startswith("B"))
    return {
        "alignment": [
            {
                "text": {"en": "Both state the same intention.", "zh": "双方自述意向相同。"},
                "evidence": [{"source": s["id"], "quote": s["text"]} for s in (a, b)],
            }
        ],
        "tensions": [],
        "uncertain_differences": [],
        "unknowns": [{"en": "Actual behavior is unknown.", "zh": "实际行为未知。"}],
        "questions": [
            {"en": "What does this intention mean to you?", "zh": "这个意向对你意味着什么？"}
        ],
        "caveat": {
            "en": "Self-reports only, no success prediction.",
            "zh": "仅为自述，不预测关系成功。",
        },
    }


def test_exact_ai_request_private_cache_and_revoke(node):  # noqa: F811
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    invite = invitation(node, a, b)
    prepared = node.prepare_comparison(a["token"], invite)
    backend = SyntheticBackend(report_data(prepared["sources"]))
    request = comparison_request(prepared)
    report = generate_comparison(backend, prepared, reviewed(request, backend))
    node.finish_comparison(a["token"], invite, prepared["ticket"], report)
    assert node.read_comparison(a["token"], invite)["report"] == report.model_dump()
    with pytest.raises(ValueError, match="no_current_result"):
        node.read_comparison(b["token"], invite)
    wrong = reviewed(request, backend).model_copy(update={"system": "different"})
    with pytest.raises(ValueError, match="disclosure_required"):
        generate_comparison(backend, prepared, wrong)
    node.update_profile(
        b["token"],
        ProfileUpdate(
            expected_version=1,
            profile=profile("Synthetic B", priorities=["availability"]),
            approved=True,
        ),
    )
    with pytest.raises(ValueError):
        node.read_comparison(a["token"], invite)
    with pytest.raises(ValueError):
        node.finish_comparison(a["token"], invite, prepared["ticket"], report)
    assert len(backend.calls) == 1


def test_fabricated_peer_evidence_rejected(node):  # noqa: F811
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    invite = invitation(node, a, b)
    prepared = node.prepare_comparison(a["token"], invite)
    data = report_data(prepared["sources"])
    data["alignment"][0]["evidence"][1]["quote"] = "secret invented data"
    with pytest.raises(ValueError, match="invalid_evidence"):
        node.finish_comparison(
            a["token"], invite, prepared["ticket"], PeerReport.model_validate(data)
        )
