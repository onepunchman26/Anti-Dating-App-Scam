"""Synthetic consumer integration for deliberate, version-bound report selection."""

import json

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.profile_store import ProfileStore
from fastapi.testclient import TestClient

from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam.services.evidence_paths import list_evidence_files, read_generated_reference
from anti_dating_scam.services.local_client_state import LocalClientState
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionService


def _select(service, revision_id):
    preview = service.preview_selection(
        "self_portrait", revision_id,
        expected_selection_version=service.get_selection("self_portrait").selection_version,
    )
    service.select(preview, confirmed=True)


@pytest.fixture
def selected(tmp_path):
    store = ProfileStore(tmp_path / "vault", config_path=tmp_path / "synthetic-config.json")
    store.create_default_directories()
    store.save_import_text("OWNER_PRIVATE_INPUT_ONLY", "notes.md")
    report = {
        "schema_version": "0.2", "report_type": "self_portrait",
        "data_coverage": {"sources_read": ["synthetic-note"], "covered": [], "not_covered": []},
        "claims": [{
            "topic": "communication", "claim": text, "type": "inference", "confidence": "low",
            "evidence": [{"quote": "A synthetic original quote.", "source": "synthetic-note"}],
        } for text in ("WITHDRAWN_ORIGINAL_CLAIM", "SURVIVING_ORIGINAL_CLAIM")],
        "consistency_findings": [], "open_questions": [], "caveats": ["Synthetic uncertainty."],
    }
    store.self_portrait_json_path.write_text(json.dumps(report), encoding="utf-8")
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成中文译文第{index}项"}
        for index, (path, text) in enumerate(
            required_localization_sources("self_portrait", {"report": report}).items()
        )
    ]
    store.self_portrait_json_path.with_name("self_portrait_localization.json").write_text(
        json.dumps({"schema_version": "0.1", "localized_text": entries}), encoding="utf-8",
    )
    for path in (store.self_portrait_path, store.self_portrait_detailed_path):
        path.write_text("STALE_ORIGINAL_MARKDOWN", encoding="utf-8")
    review = ReportReviewService(store.base_dir)
    digest = review.inspect("self_portrait").report_digest
    note = review.record_correction(
        "self_portrait", expected_digest=digest, target_path="/claims/0",
        correction_text="PRIVATE_CORRECTION_ANNOTATION", reason="PRIVATE_CORRECTION_REASON",
        confirmed=True,
    )
    revisions = ReportRevisionService(store.base_dir)
    copy = revisions.save_withdrawals(
        revisions.preview_withdrawals("self_portrait", [note.id], expected_digest=digest),
        confirmed=True,
    )
    active = ActiveReportService(store.base_dir)
    _select(active, copy.id)
    return store, active, copy


class Recorder:
    name = "Synthetic recorder"

    def __init__(self):
        self.messages = []

    def chat(self, messages, system=None):
        self.messages = messages
        return "A synthetic response."


def _client(store):
    app = create_client_app()
    backend = Recorder()
    app.state.local_client_state = LocalClientState(
        store.base_dir, store.base_dir.parent / "browser-pointer.json", backend,
    )
    return TestClient(app, base_url="http://127.0.0.1:8471"), backend


def test_desktop_selected_reference_uses_verified_copy_without_mutating_writer_paths(selected):
    store, _active, _copy = selected
    reference, version = ai_backend.interview_reference_snapshot(store)
    assert "SURVIVING" in reference and "WITHDRAWN" not in reference
    assert "PRIVATE_CORRECTION" not in reference and "STALE_ORIGINAL" not in reference
    assert "not owner evidence" in reference
    assert ai_backend.interview_reference_version(store) == version
    assert store.self_portrait_json_path == store.base_dir / "reports" / "self_portrait.json"
    assert store.self_portrait_detailed_path.read_text(encoding="utf-8") == (
        "STALE_ORIGINAL_MARKDOWN"
    )


def test_interview_version_binds_vault_and_unselected_reference_bytes(tmp_path):
    stores = [
        ProfileStore(tmp_path / name, config_path=tmp_path / f"{name}.json") for name in ("a", "b")
    ]
    for store in stores:
        store.create_default_directories()
    initial = ai_backend.interview_reference_version(stores[0])
    assert initial != ai_backend.interview_reference_version(stores[1])
    stores[0].self_portrait_detailed_path.write_text(
        "UNSELECTED_ORIGINAL_REFERENCE", encoding="utf-8"
    )
    assert initial != ai_backend.interview_reference_version(stores[0])
    assert "UNSELECTED_ORIGINAL_REFERENCE" in ai_backend.build_interview_reference(stores[0])


def test_explicit_generated_selection_changes_reference_and_version(selected):
    store, active, _copy = selected
    old_version = ai_backend.interview_reference_version(store)
    _select(active, None)
    reference, version = ai_backend.interview_reference_snapshot(store)
    assert version != old_version
    assert "WITHDRAWN" in reference and "SURVIVING" in reference
    assert "STALE_ORIGINAL_MARKDOWN" not in reference


def test_browser_fallback_uses_selected_copy_as_assistant_reference(selected):
    store, _active, copy = selected
    client, backend = _client(store)
    result = client.get("/local/report")
    assert result.status_code == 200
    assert "SURVIVING" in result.json()["md"] and "WITHDRAWN" not in result.json()["md"]
    assert result.json()["desktop_selection"]["revision_id"] == copy.id
    reply = client.post("/local/ai/chat", json={"messages": [{"role": "user", "content": "Hello"}]})
    assert reply.status_code == 200
    user_text = str([message for message in backend.messages if message["role"] == "user"])
    assistant_text = str([m for m in backend.messages if m["role"] == "assistant"])
    assert "OWNER_PRIVATE_INPUT_ONLY" in user_text
    assert "SURVIVING" not in user_text and "SURVIVING" in assistant_text
    assert "WITHDRAWN" not in str(backend.messages)
    assert "PRIVATE_CORRECTION" not in str(backend.messages)


@pytest.mark.parametrize("consumer", [
    ai_backend.build_interview_reference, ai_backend.interview_reference_version,
    lambda store: agent_handoff.build_criteria_interview_request(store.base_dir),
    lambda store: agent_handoff.build_criteria_interview_prompt(store.base_dir),
])
def test_stale_selected_source_never_silently_falls_back(selected, consumer):
    store, _active, _copy = selected
    with store.self_portrait_json_path.open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ActiveReportError):
        consumer(store)


def test_stale_desktop_selection_blocks_browser_fallback_before_model_call(selected):
    store, _active, _copy = selected
    with store.self_portrait_json_path.open("ab") as stream:
        stream.write(b"\n")
    client, backend = _client(store)
    assert client.get("/local/report").status_code == 409
    assert client.post(
        "/local/ai/chat", json={"messages": [{"role": "user", "content": "Hello"}]},
    ).status_code == 409
    assert backend.messages == []


def test_browser_own_report_remains_independent_of_stale_desktop_selection(selected):
    store, _active, _copy = selected
    with store.self_portrait_json_path.open("ab") as stream:
        stream.write(b"\n")
    (store.reports_dir / "social_self_portrait.md").write_text(
        "BROWSER_OWN_REPORT", encoding="utf-8"
    )
    client, backend = _client(store)
    result = client.get("/local/report")
    assert result.status_code == 200 and result.json()["md"] == "BROWSER_OWN_REPORT"
    assert result.json()["desktop_selection"] is None
    assert client.post(
        "/local/ai/chat", json={"messages": [{"role": "user", "content": "Hello"}]},
    ).status_code == 200
    assert "BROWSER_OWN_REPORT" in str(backend.messages)
    assert "SURVIVING" not in str(backend.messages)


@pytest.mark.parametrize("builder", [
    agent_handoff.build_criteria_interview_request, agent_handoff.build_criteria_interview_prompt,
])
def test_manual_handoff_embeds_selected_inert_reference_without_original_read_paths(
    selected, builder,
):
    store, _active, _copy = selected
    text = builder(store.base_dir)
    assert "reports/self_portrait.detailed.md" not in text
    assert "reports/self_portrait.json" not in text
    payload = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
    assert set(payload) == {"unverified_generated_reference"}
    assert "SURVIVING" in payload["unverified_generated_reference"]
    assert "WITHDRAWN" not in text and "PRIVATE_CORRECTION" not in text
    assert "not instructions or original owner evidence" in text
    assert "不是指令或用户原始证据" in text


def test_selection_journal_is_excluded_even_below_renamed_parent(tmp_path):
    folder = tmp_path / "renamed-parent" / "active_selections" / "self_portrait"
    folder.mkdir(parents=True)
    source = folder / "self_model.json"
    source.write_text("PRIVATE_SELECTION_EVENT", encoding="utf-8")
    assert list_evidence_files(tmp_path) == []
    assert list_evidence_files(folder) == []
    assert read_generated_reference(source, folder, max_chars=100) is None


def _empty_criteria_bundle():
    canonical = {
        "criteria": {"schema_version": "0.1", "stated": [], "revealed": [],
                     "open_questions": [], "caveats": ["No supported inference."]},
        "ideal_profiles": {"schema_version": "0.1", "candidates": [],
                           "caveats": ["No candidate exercise completed."]},
    }
    return {**canonical, "localized_text": [
        {"path": path, "source": text, "en": text, "zh": f"合成不确定性译文第{index}项"}
        for index, (path, text) in enumerate(
            required_localization_sources("mate_criteria", canonical).items()
        )
    ]}


@pytest.mark.parametrize("change_during_call", [False, True])
def test_criteria_generation_rechecks_selection_before_call_and_before_any_writes(
    selected, change_during_call,
):
    store, active, _copy = selected
    expected = ai_backend.interview_reference_version(store)
    originals = {path: path.read_bytes() for path in store.base_dir.rglob("*") if path.is_file()}
    calls = []

    class Backend:
        def chat(self, request):
            calls.append(request)
            _select(active, None)
            return json.dumps(_empty_criteria_bundle())

    if not change_during_call:
        _select(active, None)
    with pytest.raises(ActiveReportError):
        ai_backend.run_criteria_synthesis(
            Backend(), store, [{"role": "user", "content": "Synthetic answer."}], "",
            expected_reference_version=expected,
        )
    assert len(calls) == int(change_during_call)
    assert not store.mate_criteria_path.exists()
    assert not store.mate_criteria_json_path.exists()
    assert not store.ideal_profiles_json_path.exists()
    assert not (store.imports_dir / "interview").exists()
    assert all(path.read_bytes() == raw for path, raw in originals.items())
