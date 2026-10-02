"""Pending profile copies are inert even when chosen directly as an input root."""

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from test_legacy_report_consumers import ARCHIVED, _request_without_archive, _store

from anti_dating_scam.services import evidence_paths as paths


@pytest.mark.parametrize(
    "directory", [".profile-migration", ".pending-profile-migration-" + "a" * 32],
)
@pytest.mark.parametrize("direct", [False, True])
def test_pending_or_metadata_cannot_become_input_via_selected_root(tmp_path, directory, direct):
    store = _store(tmp_path)
    parent = store.imports_dir / "original-outer"
    pending = parent / directory.swapcase() / "nested"
    pending.mkdir(parents=True)
    (pending / "ordinary-notes.md").write_text(ARCHIVED, encoding="utf-8")
    renamed = store.imports_dir / "renamed-outer"
    parent.rename(renamed)
    pending = renamed / directory.swapcase() / "nested"
    source = pending / "ordinary-notes.md"
    selected = pending if direct else renamed
    assert paths.list_evidence_files(selected) == []
    assert paths.read_evidence_text(source, selected, max_chars=500) is None
    assert source.relative_to(store.base_dir) not in agent_handoff.list_vault_data_files(
        store.base_dir,
    )
    assert ARCHIVED not in ai_backend.inline_vault_data(store)
    _request_without_archive(store, selected)


@pytest.mark.parametrize(
    "directory", [".profile-migration", ".pending-profile-migration-" + "b" * 32],
)
def test_pending_directory_cannot_masquerade_as_generated_reference_vault(tmp_path, directory):
    pending = tmp_path / directory / "renamed-vault"
    reports = pending / "reports"
    reports.mkdir(parents=True)
    source = reports / "self_portrait.md"
    source.write_text(ARCHIVED, encoding="utf-8")
    assert paths.read_generated_reference(source, pending, max_chars=500) is None
