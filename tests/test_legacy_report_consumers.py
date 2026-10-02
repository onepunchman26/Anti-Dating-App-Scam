"""Archived legacy material remains inert, including through renamed input roots."""

import json
import os
import subprocess

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.profile_store import ProfileStore
from fastapi.testclient import TestClient

from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services import evidence_paths as paths
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.legacy_reports import LegacyReportError, LegacyReportService
from anti_dating_scam.services.local_client_state import LocalClientState

ARCHIVED = "PRIVATE_LEGACY_ARCHIVE_ONLY"
OWNER = "OWNER_ORIGINAL_NOTES_ONLY"
CURRENT = "CURRENT_VERIFIED_SHAPE_REFERENCE"


def _store(tmp_path):
    store = ProfileStore(tmp_path / "vault", config_path=tmp_path / "device.json")
    store.create_default_directories()
    store.save_import_text(OWNER, "notes.md")
    return store


class Recorder:
    name = "Synthetic local recorder"

    def __init__(self):
        self.messages = []

    def chat(self, messages, system=None):
        self.messages = messages
        return "Synthetic reply."


def _client(store):
    backend = Recorder()
    app = create_client_app()
    app.state.local_client_state = LocalClientState(
        store.base_dir, store.base_dir.parent / "browser-pointer.json", backend,
    )
    return TestClient(app, base_url="http://127.0.0.1:8471"), backend


def _request_without_archive(store, selected_root):
    client, backend = _client(store)
    response = client.post("/local/data/config", json={"path": str(selected_root)})
    assert response.status_code == 200
    assert all("ordinary-notes" not in item["name"] for item in response.json()["files"])
    assert client.post("/local/ai/chat", json={
        "messages": [{"role": "user", "content": "Synthetic current question."}],
    }).status_code == 200
    assert ARCHIVED not in str(backend.messages)
    assert OWNER in str(backend.messages)
    return backend.messages


@pytest.mark.parametrize("history_name", ["legacy_archives", "converted_reports"])
@pytest.mark.parametrize("depth", [0, 1, 2, 3])
def test_renamed_outer_directory_and_selected_archive_roots_never_become_evidence(
    tmp_path, depth, history_name,
):
    store = _store(tmp_path)
    original_parent = store.imports_dir / "original-parent"
    # A non-canonical member name proves the directory boundary itself is enforced.
    folder = original_parent / history_name.swapcase() / "self_portrait" / ("a" * 32)
    folder.mkdir(parents=True)
    (folder / "ordinary-notes.md").write_text(ARCHIVED, encoding="utf-8")
    renamed = store.imports_dir / "renamed-parent"
    original_parent.rename(renamed)
    parts = (history_name.swapcase(), "self_portrait", "a" * 32)
    selected = renamed.joinpath(*parts[:depth])
    source = renamed.joinpath(*parts, "ordinary-notes.md")
    assert paths.list_evidence_files(selected) == []
    assert not paths.evidence_path_allowed(source, selected)
    assert paths.read_evidence_text(source, selected, max_chars=500) is None
    assert source.relative_to(store.base_dir) not in agent_handoff.list_vault_data_files(
        store.base_dir,
    )
    assert ARCHIVED not in ai_backend.inline_vault_data(store)
    _request_without_archive(store, selected)


@pytest.mark.parametrize("history_name", ["legacy_archives", "converted_reports"])
@pytest.mark.parametrize("relative", [
    "self_model.json", "reports/self_portrait.md", "reports/self_portrait.detailed.md",
    "reports/social_self_portrait.md",
])
def test_archive_subtree_cannot_masquerade_as_a_vault_for_fixed_prior_references(
    tmp_path, relative, history_name,
):
    root = tmp_path / "renamed-outer" / history_name / "self_portrait" / ("b" * 32)
    source = root / relative
    source.parent.mkdir(parents=True)
    source.write_text(ARCHIVED, encoding="utf-8")
    assert paths.read_generated_reference(source, root, max_chars=500) is None


@pytest.mark.parametrize("history_name", ["legacy_archives", "converted_reports"])
def test_archive_hardlinks_cannot_enter_owner_input_or_fixed_assistant_reference(
    tmp_path, history_name,
):
    store = _store(tmp_path)
    folder = store.reports_dir / history_name / "self_portrait" / ("c" * 32)
    folder.mkdir(parents=True)
    snapshot = folder / "snapshot.md"
    snapshot.write_text(ARCHIVED, encoding="utf-8")
    aliases = [store.imports_dir / "ordinary-notes.md", store.profile_dir / "ordinary.json",
               store.self_portrait_detailed_path]
    try:
        for alias in aliases:
            os.link(snapshot, alias)
    except OSError:
        pytest.skip("Host filesystem cannot create synthetic hardlinks.")
    assert ARCHIVED not in ai_backend.inline_vault_data(store)
    assert ARCHIVED not in ai_backend.build_interview_reference(store)
    assert paths.read_generated_reference(aliases[-1], store.base_dir, max_chars=500) is None
    assert all(path not in agent_handoff.list_vault_data_files(store.base_dir)
               for path in (alias.relative_to(store.base_dir) for alias in aliases))
    _request_without_archive(store, folder)


@pytest.mark.parametrize("history_name", ["legacy_archives", "converted_reports"])
def test_real_junction_cannot_expose_legacy_archive_as_original_input(tmp_path, history_name):
    if os.name != "nt":
        pytest.skip("Windows junction regression.")
    store = _store(tmp_path)
    folder = store.reports_dir / history_name / "self_portrait" / ("d" * 32)
    folder.mkdir(parents=True)
    (folder / "ordinary-notes.md").write_text(ARCHIVED, encoding="utf-8")
    alias = store.imports_dir / "alias"
    created = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(alias), str(folder)],
        capture_output=True, timeout=10,
    )
    assert created.returncode == 0, "Synthetic junction could not be created."
    try:
        assert paths.list_evidence_files(alias) == []
        assert ARCHIVED not in ai_backend.inline_vault_data(store)
        _request_without_archive(store, alias)
    finally:
        assert alias.parent == store.imports_dir and alias.is_junction()
        alias.rmdir()  # Remove the verified synthetic junction itself, never its target.


def _current_report(store, kind):
    claim = {"topic": "communication", "claim": CURRENT, "type": "inference", "confidence": "low",
             "evidence": [{"quote": "Synthetic original quotation.", "source": "synthetic-note"}]}
    common = {"report_type": kind, "open_questions": [], "caveats": ["Synthetic uncertainty."]}
    if kind == "self_portrait":
        canonical = {"report": {**common, "schema_version": "0.2", "claims": [claim],
                                "data_coverage": {"sources_read": [], "covered": [],
                                                  "not_covered": []}, "consistency_findings": []}}
    else:
        canonical = {"criteria": {**common, "schema_version": "0.1", "stated": [claim],
                                  "revealed": []}, "ideal_profiles": {
            "schema_version": "0.1", "candidates": [], "caveats": ["No candidates."]}}
        store.ideal_profiles_json_path.write_text(
            json.dumps(canonical["ideal_profiles"]), encoding="utf-8",
        )
    (store.reports_dir / f"{kind}.json").write_text(
        json.dumps(canonical["report" if kind == "self_portrait" else "criteria"]),
        encoding="utf-8",
    )
    entries = [{"path": path, "source": text, "en": text, "zh": f"合成不确定性译文第{index}项"}
               for index, (path, text) in enumerate(
                   required_localization_sources(kind, canonical).items())]
    (store.reports_dir / f"{kind}_localization.json").write_text(
        json.dumps({"schema_version": "0.1", "localized_text": entries}), encoding="utf-8",
    )
    active = ActiveReportService(store.base_dir)
    choice = active.preview_selection(
        kind, None, expected_selection_version=active.get_selection(kind).selection_version,
    )
    active.select(choice, confirmed=True)
    return active


def _archive(service, kind):
    inspection = service.inspect(kind)
    preview = service.preview_archive(kind, expected_digest=inspection.source_digest)
    return service.save_archive(preview, confirmed=True), preview


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_actual_archive_preserves_originals_and_deliberate_current_selection(tmp_path, kind):
    store = _store(tmp_path)
    active = _current_report(store, kind)
    before_selection = active.resolve(kind)
    before_version = ai_backend.interview_reference_version(store)
    originals = {path: path.read_bytes() for path in store.base_dir.rglob("*") if path.is_file()}
    service = LegacyReportService(store.base_dir)
    inspection = service.inspect(kind)
    preview = service.preview_archive(kind, expected_digest=inspection.source_digest)
    assert inspection.format == "current_structured"
    assert not (store.reports_dir / "legacy_archives").exists()
    saved = service.save_archive(preview, confirmed=True)
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert active.resolve(kind) == before_selection
    assert ai_backend.interview_reference_version(store) == before_version
    assert service.read_archive(kind, saved.id) == preview
    for member in preview.files:
        if member.present:
            assert service.read_snapshot(kind, saved.id, member.label) == (
                store.reports_dir / member.label
            ).read_bytes()
    assert all("legacy_archives" not in path.parts
               for path in agent_handoff.list_vault_data_files(store.base_dir))


def test_old_archive_does_not_reappear_after_explicit_report_regeneration(tmp_path):
    store = _store(tmp_path)
    store.self_portrait_json_path.write_bytes(
        ('{"schema_version":"0.3","headline":"' + ARCHIVED + '","top_values":[]}').encode(),
    )
    store.self_portrait_path.write_text(ARCHIVED, encoding="utf-8")
    store.self_portrait_detailed_path.write_text(ARCHIVED, encoding="utf-8")
    service = LegacyReportService(store.base_dir)
    saved, preview = _archive(service, "self_portrait")
    assert preview.format == "self_portrait_v03"
    # Synthetic regeneration supplies a different valid report; archiving never does this.
    _current_report(store, "self_portrait")
    reference = ai_backend.build_interview_reference(store)
    assert CURRENT in reference.replace("\\", "") and ARCHIVED not in reference
    assert ARCHIVED not in ai_backend.inline_vault_data(store)
    for builder in (agent_handoff.build_criteria_interview_request,
                    agent_handoff.build_criteria_interview_prompt):
        assert ARCHIVED not in builder(store.base_dir)
    for root in (store.reports_dir / "legacy_archives",
                 store.reports_dir / "legacy_archives" / "self_portrait",
                 store.reports_dir / "legacy_archives" / "self_portrait" / saved.id):
        messages = _request_without_archive(store, root)
        owners = str([message for message in messages if message["role"] == "user"])
        assistants = str([message for message in messages if message["role"] == "assistant"])
        assert CURRENT not in owners.replace("\\", "")
        assert CURRENT in assistants.replace("\\", "")
    # Later regeneration does not invalidate the independent retained archive.
    assert service.read_archive("self_portrait", saved.id) == preview
    assert ARCHIVED.encode() == service.read_snapshot("self_portrait", saved.id, "self_portrait.md")


@pytest.mark.parametrize("changed", ["new_companion", "removed_companion", "byte_change"])
def test_archive_stale_failure_does_not_change_active_selection_or_prior_archive(tmp_path, changed):
    store = _store(tmp_path)
    active = _current_report(store, "self_portrait")
    choice = active.get_selection("self_portrait")
    service = LegacyReportService(store.base_dir)
    saved, preview = _archive(service, "self_portrait")
    archive_files = {
        path: path.read_bytes()
        for path in (store.reports_dir / "legacy_archives" / "self_portrait" / saved.id).iterdir()
    }
    if changed == "new_companion":
        store.self_portrait_path.write_text("New source member", encoding="utf-8")
    elif changed == "removed_companion":
        (store.reports_dir / "self_portrait_localization.json").unlink()
    else:
        with store.self_portrait_json_path.open("ab") as stream:
            stream.write(b"\r\n ")
    source_files = {
        path: path.read_bytes() for path in store.reports_dir.iterdir() if path.is_file()
    }
    with pytest.raises(LegacyReportError):
        service.save_archive(preview, confirmed=True)
    assert active.get_selection("self_portrait") == choice
    assert service.list_archives("self_portrait") == [saved]
    assert service.read_archive("self_portrait", saved.id) == preview
    assert all(path.read_bytes() == raw for path, raw in archive_files.items())
    assert all(path.read_bytes() == raw for path, raw in source_files.items())
