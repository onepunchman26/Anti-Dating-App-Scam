"""Synthetic correction history and reviewed copies are never implicit original evidence."""

import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.profile_store import ProfileStore
from fastapi.testclient import TestClient

from anti_dating_scam.api import routes_local_ai as browser
from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.services import evidence_paths as paths
from anti_dating_scam.services.active_reports import ActiveReportError
from anti_dating_scam.services.local_client_state import LocalClientState


@pytest.fixture(params=["review_history", "reviewed_copies"])
def vault(tmp_path, request):
    store = ProfileStore(base_dir=tmp_path / "vault", config_path=tmp_path / "device.json")
    store.create_default_directories()
    store.save_import_text("OWNER_ORIGINAL_ONLY", "notes.md")
    history = store.reports_dir / request.param / "self_portrait"
    history.mkdir(parents=True)
    annotation = history / "synthetic-review.json"
    annotation.write_text('{"note":"PRIVATE_REVIEW_HISTORY"}', encoding="utf-8")
    interview = store.imports_dir / "interview"
    interview.mkdir()
    (interview / "criteria_interview_transcript.md").write_text("MIXED_ASSISTANT_TRANSCRIPT")
    (interview / "criteria_interview_user_notes.md").write_text("OWNER_INTERVIEW_ONLY")
    return store, annotation


class Recorder:
    name = "Synthetic source recorder"

    def __init__(self):
        self.messages = []

    def chat(self, messages, system=None):
        self.messages = messages
        return "Synthetic response."


def browser_client(store):
    backend = Recorder()
    app = create_client_app()
    app.state.local_client_state = LocalClientState(
        store.base_dir,
        store.base_dir.parent / "browser-pointer.json",
        backend,
    )
    return TestClient(app, base_url="http://127.0.0.1:8471"), backend


@pytest.mark.parametrize("selected", ["reports", "generated_history", "self_portrait"])
def test_selecting_generated_subtree_as_browser_input_does_not_import_history(vault, selected):
    store, annotation = vault
    selected_root = (
        annotation.parent.parent if selected == "generated_history"
        else next(parent for parent in annotation.parents if parent.name == selected)
    )
    client, backend = browser_client(store)
    response = client.post("/local/data/config", json={"path": str(selected_root)})
    assert response.status_code == 200
    assert all(item["name"] != annotation.name for item in response.json()["files"])
    assert (
        client.post(
            "/local/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "A synthetic question.",
                    }
                ]
            },
        ).status_code
        == 200
    )
    assert "PRIVATE_REVIEW_HISTORY" not in str(backend.messages)
    assert "OWNER_ORIGINAL_ONLY" in str(backend.messages)
    assert "OWNER_INTERVIEW_ONLY" in str(backend.messages)


def test_desktop_and_manual_manifest_preserve_original_answers_but_skip_history(vault):
    store, _annotation = vault
    manifest = agent_handoff.list_vault_data_files(store.base_dir)
    assert Path("imports/interview/criteria_interview_user_notes.md") in manifest
    assert Path("imports/interview/criteria_interview_transcript.md") not in manifest
    assert all(
        not {"review_history", "reviewed_copies"}.intersection(path.parts) for path in manifest
    )
    text = ai_backend.inline_vault_data(store)
    assert "OWNER_INTERVIEW_ONLY" in text and "OWNER_ORIGINAL_ONLY" in text
    assert "PRIVATE_REVIEW_HISTORY" not in text and "MIXED_ASSISTANT_TRANSCRIPT" not in text


def test_hardlink_history_alias_and_direct_browser_notes_fallback_are_rejected(vault):
    store, annotation = vault
    notes = store.imports_dir / "notes.md"
    notes.unlink()
    os.link(annotation, notes)
    alias = store.profile_dir / "ordinary.json"
    os.link(annotation, alias)
    assert not paths.evidence_path_allowed(notes, store.imports_dir)
    assert paths.read_evidence_text(notes, store.imports_dir, max_chars=100) is None
    assert alias.relative_to(store.base_dir) not in agent_handoff.list_vault_data_files(
        store.base_dir
    )
    assert "PRIVATE_REVIEW_HISTORY" not in ai_backend.inline_vault_data(store)
    client, backend = browser_client(store)
    assert (
        client.post(
            "/local/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Synthetic question.",
                    }
                ]
            },
        ).status_code
        == 200
    )
    assert "PRIVATE_REVIEW_HISTORY" not in str(backend.messages)


@pytest.mark.parametrize("location", ["root", "nested", "file"])
def test_windows_reparse_flags_are_rejected_at_every_level(tmp_path, monkeypatch, location):
    root = tmp_path / "input"
    folder = root / "nested"
    folder.mkdir(parents=True)
    source = folder / "notes.md"
    source.write_text("synthetic")
    flagged = {"root": root, "nested": folder, "file": source}[location]
    original_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        actual = original_lstat(path, *args, **kwargs)
        if path == flagged:
            return SimpleNamespace(
                st_mode=actual.st_mode,
                st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            )
        return actual

    monkeypatch.setattr(Path, "lstat", lstat)
    assert paths.list_evidence_files(root) == []
    assert paths.read_evidence_text(source, root, max_chars=100) is None


def test_real_junction_cannot_alias_history_or_be_selected_as_input_root(vault):
    if os.name != "nt":
        pytest.skip("Windows junction regression.")
    store, annotation = vault
    link = store.imports_dir / "ordinary-folder"
    made = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(link), str(annotation.parent)],
        capture_output=True,
        timeout=10,
    )
    assert made.returncode == 0, "Synthetic junction fixture could not be created."
    try:
        assert paths.list_evidence_files(link) == []
        assert paths.read_evidence_text(link / annotation.name, link, max_chars=100) is None
        assert "PRIVATE_REVIEW_HISTORY" not in ai_backend.inline_vault_data(store)
        assert all(
            "ordinary-folder" not in path.parts
            for path in agent_handoff.list_vault_data_files(store.base_dir)
        )
        client, backend = browser_client(store)
        configured = client.post("/local/data/config", json={"path": str(link)})
        assert configured.status_code == 200
        assert client.get("/local/status").json()["settings"]["data_dir"] == str(link)
        client.post("/local/ai/chat", json={"messages": [{"role": "user", "content": "Hello"}]})
        assert "PRIVATE_REVIEW_HISTORY" not in str(backend.messages)
    finally:
        # Remove only the verified synthetic junction itself, never its target tree.
        assert link.parent == store.imports_dir and link.is_junction()
        link.rmdir()


def test_outside_selected_root_is_never_evidence(tmp_path):
    root = tmp_path / "selected"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("PRIVATE_OUTSIDE")
    assert not paths.evidence_path_allowed(outside, root)
    assert paths.read_evidence_text(outside, root, max_chars=100) is None


@pytest.mark.parametrize("generated_reference", [False, True])
def test_read_is_bounded_before_allocation_and_mid_read_changes_are_rejected(
    tmp_path, monkeypatch, generated_reference
):
    source = tmp_path / ("self_model.json" if generated_reference else "large.md")
    reader = paths.read_generated_reference if generated_reference else paths.read_evidence_text
    source.write_bytes(b"x" * 1_000_000)
    original_fdopen = os.fdopen
    reads = []
    mutate = False

    class Reader:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def fileno(self):
            return self.stream.fileno()

        def read(self, size):
            assert 0 < size <= paths.MAX_READ_BYTES
            reads.append(size)
            content = self.stream.read(size)
            if mutate:
                with source.open("ab") as writer:
                    writer.write(b"changed")
            return content

    monkeypatch.setattr(os, "fdopen", lambda fd, mode: Reader(original_fdopen(fd, mode)))
    text = reader(source, tmp_path, max_chars=10)
    assert text == "x" * 10 + "\n...[truncated for length]..."
    assert reads == [44]
    mutate = True
    assert reader(source, tmp_path, max_chars=10) is None


def test_discovery_obeys_file_and_entry_bounds(tmp_path):
    for index in range(12):
        (tmp_path / f"synthetic-{index}.md").write_text("synthetic")
    assert len(paths.list_evidence_files(tmp_path, max_files=2, max_entries=5)) == 2
    assert len(paths.list_evidence_files(tmp_path, max_files=10, max_entries=3)) == 3


def test_browser_actual_read_rechecks_files_after_listing(vault, monkeypatch):
    store, annotation = vault
    candidate = store.imports_dir / "looks-original.md"
    os.link(annotation, candidate)
    monkeypatch.setattr(browser, "VAULT_DIR", store.base_dir)
    monkeypatch.setattr(browser, "SETTINGS_PATH", store.base_dir / "client_settings.json")
    # A stale/malicious file listing cannot bypass the shared read boundary.
    monkeypatch.setattr(browser, "_data_files", lambda: [candidate])
    assert browser._inline_context() == "(no imported data yet)"


@pytest.mark.parametrize("builder", [
    agent_handoff.build_analysis_request, agent_handoff.build_self_portrait_request,
    agent_handoff.build_criteria_interview_request, agent_handoff.build_agent_prompt,
    agent_handoff.build_self_portrait_prompt, agent_handoff.build_criteria_interview_prompt,
])
def test_manual_handoffs_limit_read_all_language_to_checked_manifest(vault, builder):
    store, _annotation = vault
    text = builder(store.base_dir)
    assert "listed original regular files" in text
    assert "Correction notes remain separate annotations" in text
    assert "review_history" in text and "更正注释仍是独立注释" in text
    assert "reviewed_copies" in text
    assert "Reviewed copies are generated reports, not original owner evidence" in text
    assert "复核副本属于生成报告，不是用户原始证据" in text


@pytest.mark.parametrize("selected_depth", [0, 1, 2, 3])
def test_renamed_parent_does_not_hide_reviewed_copy_subtree(vault, selected_depth):
    store, _annotation = vault
    old_parent = store.imports_dir / "original-parent"
    copy_dir = old_parent / "ReViEwEd_CoPiEs" / "self_portrait" / "synthetic-id"
    copy_dir.mkdir(parents=True)
    (copy_dir / "ordinary-notes.md").write_text("PRIVATE_REVIEWED_COPY")
    # Preserve the generated location even after its outer folder is renamed.
    renamed = store.imports_dir / "renamed-parent"
    old_parent.rename(renamed)
    selected = renamed.joinpath(
        *("ReViEwEd_CoPiEs", "self_portrait", "synthetic-id")[:selected_depth]
    )
    source = renamed / "ReViEwEd_CoPiEs" / "self_portrait" / "synthetic-id" / "ordinary-notes.md"
    assert paths.list_evidence_files(selected) == []
    assert paths.read_evidence_text(source, selected, max_chars=100) is None
    assert source.relative_to(store.base_dir) not in agent_handoff.list_vault_data_files(
        store.base_dir
    )
    assert "PRIVATE_REVIEWED_COPY" not in ai_backend.inline_vault_data(store)
    client, backend = browser_client(store)
    assert client.post("/local/data/config", json={"path": str(selected)}).status_code == 200
    assert client.post(
        "/local/ai/chat", json={"messages": [{"role": "user", "content": "Question"}]}
    ).status_code == 200
    assert "PRIVATE_REVIEWED_COPY" not in str(backend.messages)


def test_reviewed_copy_subtree_cannot_become_prior_ai_reference(vault):
    store, _annotation = vault
    copy_root = store.imports_dir / "renamed-parent" / "reviewed_copies" / "synthetic-id"
    copy_root.mkdir(parents=True)
    card = copy_root / "self_model.json"
    card.write_text("PRIVATE_REVIEWED_COPY")
    assert paths.read_generated_reference(card, copy_root, max_chars=100) is None
    report = copy_root / "reports" / "self_portrait.detailed.md"
    report.parent.mkdir()
    report.write_text("PRIVATE_REVIEWED_COPY")
    assert paths.read_generated_reference(report, copy_root, max_chars=100) is None


@pytest.mark.parametrize("relative", [
    "self_model.json", "reports/social_self_portrait.md", "reports/self_portrait.md",
    "reports/self_portrait.detailed.md",
])
def test_fixed_generated_reference_paths_allow_regular_files_but_never_history_hardlinks(
    vault, relative
):
    store, annotation = vault
    candidate = store.base_dir / relative
    candidate.write_text("VALID_PRIOR_GENERATED_REFERENCE", encoding="utf-8")
    assert paths.read_generated_reference(candidate, store.base_dir, max_chars=100) == (
        "VALID_PRIOR_GENERATED_REFERENCE"
    )
    candidate.unlink()
    os.link(annotation, candidate)
    assert paths.read_generated_reference(candidate, store.base_dir, max_chars=100) is None
    if relative == "reports/self_portrait.detailed.md":
        assert ai_backend.build_interview_reference(store) == ""
    client, backend = browser_client(store)
    response = client.post(
        "/local/ai/chat", json={"messages": [{"role": "user", "content": "Synthetic question"}]}
    )
    assert response.status_code == 200
    assert "PRIVATE_REVIEW_HISTORY" not in str(backend.messages)
    assert "OWNER_ORIGINAL_ONLY" in str(backend.messages)


def test_generated_reference_paths_cannot_read_arbitrary_labels_or_history_roots(vault):
    store, annotation = vault
    other = store.reports_dir / "other.md"
    other.write_text("UNLISTED_REPORT")
    disguised_vault_file = annotation.parent / "self_model.json"
    disguised_vault_file.write_text("PRIVATE_REVIEW_HISTORY")
    assert paths.read_generated_reference(other, store.base_dir, max_chars=100) is None
    assert paths.read_generated_reference(annotation, store.base_dir, max_chars=100) is None
    assert paths.read_generated_reference(
        disguised_vault_file, annotation.parent, max_chars=100
    ) is None
    assert paths.read_generated_reference(
        store.imports_dir / "notes.md", store.base_dir, max_chars=100
    ) is None


def test_generated_references_preserve_safe_desktop_and_browser_fallback(vault):
    store, annotation = vault
    store.self_portrait_detailed_path.write_text("VALID_DESKTOP_REFERENCE")
    assert "VALID_DESKTOP_REFERENCE" in ai_backend.build_interview_reference(store)
    os.link(annotation, store.reports_dir / "social_self_portrait.md")
    (store.reports_dir / "self_portrait.md").write_text("VALID_LEGACY_REFERENCE")
    client, backend = browser_client(store)
    response = client.post(
        "/local/ai/chat", json={"messages": [{"role": "user", "content": "Synthetic question"}]}
    )
    assert response.status_code == 200
    assistants = "\n".join(m["content"] for m in backend.messages if m["role"] == "assistant")
    assert "VALID_LEGACY_REFERENCE" in assistants and "not owner evidence" in assistants
    assert "PRIVATE_REVIEW_HISTORY" not in str(backend.messages)


@pytest.mark.parametrize("location", ["root", "reports", "file"])
def test_generated_reference_reparse_flags_rejected(vault, monkeypatch, location):
    store, _annotation = vault
    candidate = store.self_portrait_detailed_path
    candidate.write_text("PRIVATE_REVIEW_HISTORY")
    flagged = {"root": store.base_dir, "reports": store.reports_dir, "file": candidate}[location]
    original_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        actual = original_lstat(path, *args, **kwargs)
        if path == flagged:
            return SimpleNamespace(
                st_mode=actual.st_mode,
                st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            )
        return actual

    monkeypatch.setattr(Path, "lstat", lstat)
    assert paths.read_generated_reference(candidate, store.base_dir, max_chars=100) is None
    if location in {"root", "reports"}:
        # Unsafe selection-journal ancestry stops the request, never hides a choice.
        with pytest.raises(ActiveReportError):
            ai_backend.build_interview_reference(store)
    else:
        assert ai_backend.build_interview_reference(store) == ""


def test_real_reports_junction_cannot_expose_generated_reference(vault, tmp_path):
    if os.name != "nt":
        pytest.skip("Windows junction regression.")
    store, annotation = vault
    alias_root = tmp_path / "synthetic-alias-vault"
    alias_root.mkdir()
    for filename in ("social_self_portrait.md", "self_portrait.md", "self_portrait.detailed.md"):
        (annotation.parent / filename).write_text("PRIVATE_REVIEW_HISTORY")
    link = alias_root / "reports"
    made = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(link), str(annotation.parent)],
        capture_output=True, timeout=10,
    )
    assert made.returncode == 0, "Synthetic junction fixture could not be created."
    try:
        for filename in (
            "social_self_portrait.md", "self_portrait.md", "self_portrait.detailed.md"
        ):
            assert paths.read_generated_reference(
                link / filename, alias_root, max_chars=100
            ) is None
        alias_store = SimpleNamespace(
            base_dir=alias_root, self_portrait_detailed_path=link / "self_portrait.detailed.md"
        )
        with pytest.raises(ActiveReportError):
            ai_backend.build_interview_reference(alias_store)
        client, backend = browser_client(alias_store)
        response = client.post(
            "/local/ai/chat", json={"messages": [{"role": "user", "content": "Question"}]}
        )
        assert response.status_code == 409
        assert backend.messages == []
    finally:
        assert link.parent == alias_root and link.is_junction()
        link.rmdir()
