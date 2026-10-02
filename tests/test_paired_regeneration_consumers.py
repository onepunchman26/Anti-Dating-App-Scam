"""Independent paired-wire integration; every provider reply is synthetic/injected.

Exercise public preparation, the Ollama adapter, immutable saving, reopening and
existing consumers together. Passing these checks does not establish model quality.
"""

import copy
import json
from pathlib import Path

import pytest
from anti_dating_scam_desktop import ai_backend
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
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.evidence_paths import list_evidence_files
from anti_dating_scam.services.report_full_regeneration import (
    FullReportRegenerationError,
    FullReportRegenerationService,
)
from anti_dating_scam.services.report_full_regeneration_contract import RegenerationExcerpt
from anti_dating_scam.services.report_revisions import ReportRevisionService

QUOTE_ONE = "I prefer morning conversations."
QUOTE_TWO = "I prefer evening conversations."
UNQUOTED = "UNQUOTED_SYNTHETIC_CONTENT_NOT_FOR_REFERENCE"
KINDS = ["self_portrait", "mate_criteria"]


def _pair(en, zh):
    return {"en": en, "zh": zh}


def _wire(kind):
    claim = {
        "topic": "communication", "type": "observation", "confidence": "high",
        "claim": _pair(
            "One supplied note states a preference for morning conversations.",
            "一份提供的笔记表达了对早晨交流的偏好。",
        ),
        "evidence": [{"quote": QUOTE_ONE, "source": "S001"}],
    }
    common = {
        "report_type": kind,
        "open_questions": [_pair(
            "Does the preferred time depend on the situation?", "偏好的交流时间是否取决于情境？",
        )],
        "caveats": [
            _pair("Only two fictional notes were supplied.", "只提供了两份虚构笔记。"),
            _pair("Preferences may vary with context.", "偏好可能随情境而变化。"),
        ],
    }
    if kind == "self_portrait":
        return {"report": {
            **common, "schema_version": "0.2", "claims": [claim],
            "data_coverage": {
                "sources_read": ["S001", "S002"],
                "covered": [_pair("Two stated time preferences.", "两项陈述的时间偏好。")],
                "not_covered": [_pair("Reasons for the difference are unknown.", "差异原因未知。")],
            },
            "consistency_findings": [{
                "kind": "temporal_drift",
                "stated": _pair("The first note prefers mornings.", "第一份笔记偏好早晨。"),
                "contradicting": _pair("The second note prefers evenings.", "第二份笔记偏好晚上。"),
                "quotes": [{"quote": QUOTE_ONE, "source": "S001"},
                           {"quote": QUOTE_TWO, "source": "S002"}],
                "confidence": "high",
                "framing": _pair("The difference needs context.", "这项差异需要背景信息。"),
                "clarifying_question": _pair(
                    "Did the circumstances differ?", "当时的情况是否不同？",
                ),
                "alt_benign_explanation": _pair(
                    "Different schedules could explain the difference.",
                    "日程不同可能解释这一差异。",
                ),
            }],
        }}
    return {
        "criteria": {**common, "schema_version": "0.1", "stated": [claim], "revealed": []},
        "ideal_profiles": {"schema_version": "0.1", "candidates": [], "caveats": [
            _pair("No fictional profile exercise was performed.", "未进行虚构档案练习。"),
            _pair("No participant choices were supplied.", "未提供参与者选择。"),
        ]},
    }


def _pairs(value, path=""):
    """Inventory fixture narratives independently of production projection helpers."""
    if isinstance(value, dict):
        if set(value) == {"en", "zh"}:
            yield path, value
        else:
            for name, child in value.items():
                yield from _pairs(child, path + "/" + name)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _pairs(child, path + "/" + str(index))


def _value_at(value, path):
    for component in path.lstrip("/").split("/"):
        value = value[int(component)] if isinstance(value, list) else value[component]
    return value


def _files(directory):
    return {path: path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def _prepared(tmp_path, kind):
    store, revisions, correction, digest, originals = _seed(
        tmp_path, kind, "claims" if kind == "self_portrait" else "stated",
    )
    withdrawal = revisions.save_withdrawals(revisions.preview_withdrawals(
        kind, [correction.id], expected_digest=digest,
    ), confirmed=True)
    _select(ActiveReportService(store.base_dir), kind, withdrawal.id)
    service = FullReportRegenerationService(store.base_dir)
    prepared = service.prepare(kind, [correction.id], [
        RegenerationExcerpt(text="Fictional first note:\r\n" + QUOTE_ONE + "\n" + UNQUOTED),
        RegenerationExcerpt(text="Fictional second note:\n" + QUOTE_TWO),
    ], expected_digest=digest)
    return store, revisions, service, prepared, originals


def _backend(wire):
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append((url, copy.deepcopy(payload)))
        return {"message": {"content": json.dumps(wire, ensure_ascii=False)}}

    return OllamaChatBackend(model="synthetic-paired-consumer", transport=transport), calls


@pytest.mark.parametrize("kind", KINDS)
def test_paired_reply_survives_storage_activation_and_existing_consumers(tmp_path, kind):
    store, revisions, service, prepared, originals = _prepared(tmp_path, kind)
    active = ActiveReportService(store.base_dir)
    previous = active.get_selection(kind)
    before = _files(store.base_dir)
    wire = _wire(kind)
    backend, calls = _backend(wire)
    proposal = service.generate(prepared, backend, confirmed=True)
    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:11434/api/chat"
    assert calls[0][1]["format"] == prepared.request.response_schema
    assert prepared.request.allow_schema_fallback is False
    assert _files(store.base_dir) == before
    expected = dict(_pairs(wire))
    entries = {entry["path"]: entry for entry in proposal.bundle["localized_text"]}
    assert set(entries) == set(expected)
    for path, pair in expected.items():
        assert _value_at(proposal.bundle, path) == pair["en"]
        assert entries[path] == {"path": path, "source": pair["en"], **pair}
    preview = revisions.preview_full_regeneration(
        kind, proposal, expected_digest=prepared.source_digest,
    )
    saved = revisions.save_full_regeneration(preview, confirmed=True)
    assert active.get_selection(kind) == previous
    assert all(path.read_bytes() == raw for path, raw in before.items())
    fresh = ReportRevisionService(store.base_dir)
    assert fresh.read_revision(kind, saved.id) == preview
    snapshot = json.loads((Path(saved.directory_path) / "regeneration.json").read_text("utf-8"))
    assert snapshot["bundle"] == proposal.bundle
    assert isinstance(snapshot["bundle"]["localized_text"], list)
    manifest = json.loads((Path(saved.directory_path) / "manifest.json").read_text("utf-8"))
    assert manifest["schema_version"] == "0.4"
    selected = _select(ActiveReportService(store.base_dir), kind, saved.id)
    assert selected.selection_version != previous.selection_version
    localized = {item["path"]: item for item in selected.localized_text}
    rendered = _literal(selected.detailed_markdown or selected.markdown)
    for path, pair in expected.items():
        assert _value_at(selected.canonical, path) == pair["en"]
        assert localized[path] == entries[path]
        assert pair["en"] in rendered and pair["zh"] in rendered
    root = "report" if kind == "self_portrait" else "criteria"
    report = selected.canonical[root]
    claim = report["claims" if kind == "self_portrait" else "stated"][0]
    assert claim["evidence"] == [{"quote": QUOTE_ONE, "source": "S001"}]
    assert claim["confidence"] == "low"
    assert "Original uncertainty must remain." in report["caveats"]
    assert "AI" in rendered and "unverified" in rendered and "未经核实" in rendered
    assert all(value not in rendered for value in (ANNOTATION, REASON, UNQUOTED))
    assert list_evidence_files(Path(saved.directory_path)) == []
    if kind == "self_portrait":
        assert report["consistency_findings"][0]["confidence"] == "low"
        assert store.load_self_portrait_json() == selected.canonical["report"]
        reference, _ = ai_backend.interview_reference_snapshot(store)
        assert "unverified" in _literal(reference)
        assert UNQUOTED not in reference and ANNOTATION not in reference
        client, recorder = _client(store)
        with client:
            response = client.get("/local/report")
            assert response.status_code == 200
            assert expected["/report/claims/0/claim"]["zh"] in response.json()["md"]
            assert client.post("/local/ai/chat", json={"messages": [
                {"role": "user", "content": "A new synthetic question."},
            ]}).status_code == 200
        user_messages = str([item for item in recorder.messages if item["role"] == "user"])
        assistant_messages = str([
            item for item in recorder.messages if item["role"] == "assistant"
        ])
        assert QUOTE_ONE not in user_messages
        assert expected["/report/claims/0/claim"]["en"] in _literal(assistant_messages)
        assert UNQUOTED not in str(recorder.messages)
    else:
        assert selected.canonical["ideal_profiles"]["candidates"] == []
        assert "No candidate inference." in selected.canonical["ideal_profiles"]["caveats"]
        assert expected["/criteria/stated/0/claim"]["zh"] in store.load_mate_criteria()
    _assert_originals(originals)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("failure", [
    "missing_translation", "english_in_chinese", "chinese_in_english", "unknown_pair",
    "unknown_root", "cross_source", "spliced_quote", "foreign_report_field",
])
def test_rejected_paired_reply_preserves_selected_copy_and_all_existing_bytes(
    tmp_path, kind, failure,
):
    store, revisions, service, prepared, originals = _prepared(tmp_path, kind)
    prior = ActiveReportService(store.base_dir).get_selection(kind)
    history = revisions.list_revisions(kind)
    before = _files(store.base_dir)
    wire = _wire(kind)
    root = wire["report" if kind == "self_portrait" else "criteria"]
    claim = root["claims" if kind == "self_portrait" else "stated"][0]
    if failure == "missing_translation":
        del claim["claim"]["zh"]
    elif failure == "english_in_chinese":
        claim["claim"]["zh"] = "An English-only translation."
    elif failure == "chinese_in_english":
        claim["claim"]["en"] = "仅有中文的合成内容。"
    elif failure == "unknown_pair":
        claim["claim"]["hidden_note"] = "Unknown material must not disappear."
    elif failure == "unknown_root":
        wire["localized_text"] = []
    elif failure == "cross_source":
        claim["evidence"][0]["source"] = "S002"
    elif failure == "spliced_quote":
        claim["evidence"][0]["quote"] = QUOTE_ONE + " " + QUOTE_TWO
    else:
        root["public_personality_score"] = 100
    backend, calls = _backend(wire)
    with pytest.raises(FullReportRegenerationError):
        service.generate(prepared, backend, confirmed=True)
    assert len(calls) == 1
    assert _files(store.base_dir) == before
    assert ActiveReportService(store.base_dir).get_selection(kind) == prior
    assert ReportRevisionService(store.base_dir).list_revisions(kind) == history
    _assert_originals(originals)
