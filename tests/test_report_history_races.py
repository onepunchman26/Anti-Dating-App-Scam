"""Deterministic enumerate/commit interleavings for all append-only report histories."""

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_legacy_conversion_concurrency import seed_legacy_conversion

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.legacy_reports import LegacyReportService
from anti_dating_scam.services.report_review import ReportReviewService, _encode
from anti_dating_scam.services.report_revisions import ReportRevisionService


def _seed(tmp_path, domain):
    vault = tmp_path / "vault"
    if domain == "conversion":
        service, preview = seed_legacy_conversion(vault)
        service.save_conversion(preview, confirmed=True)
        return service._root("self_portrait"), lambda: service._history("self_portrait")
    reports = vault / "reports"
    reports.mkdir(parents=True)
    claim = {
        "topic": "values",
        "claim": "Synthetic uncertain claim.",
        "type": "inference",
        "confidence": "low",
        "evidence": [{"quote": "Synthetic quotation.", "source": "synthetic-note"}],
    }
    portrait = {
        "schema_version": "0.2",
        "report_type": "self_portrait",
        "data_coverage": {"sources_read": [], "covered": [], "not_covered": []},
        "claims": [claim],
        "consistency_findings": [],
        "open_questions": [],
        "caveats": ["Synthetic and uncertain."],
    }
    (reports / "self_portrait.json").write_bytes(_encode(portrait))
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成译文{index}"}
        for index, (path, text) in enumerate(
            required_localization_sources("self_portrait", {"report": portrait}).items()
        )
    ]
    (reports / "self_portrait_localization.json").write_bytes(
        _encode(
            {
                "schema_version": "0.1",
                "localized_text": entries,
            }
        )
    )
    if domain == "archive":
        archives = LegacyReportService(vault)
        archives.save_archive(archives.preview_archive(
            "self_portrait", expected_digest=archives.inspect("self_portrait").source_digest,
        ), confirmed=True)
        return archives._root("self_portrait"), lambda: archives._history("self_portrait")
    review = ReportReviewService(vault)
    document = review.inspect("self_portrait")
    note = review.record_correction(
        "self_portrait",
        expected_digest=document.report_digest,
        target_path="/claims/0",
        correction_text="A synthetic disagreement.",
        reason="Uncertain context.",
        confirmed=True,
    )
    if domain == "review":
        return review._history("self_portrait"), lambda: review._load_history("self_portrait")
    revisions = ReportRevisionService(vault)
    revisions.save_withdrawals(
        revisions.preview_withdrawals(
            "self_portrait", [note.id], expected_digest=document.report_digest
        ),
        confirmed=True,
    )
    if domain == "revision":
        return revisions._root("self_portrait"), lambda: revisions._history("self_portrait")
    active = ActiveReportService(vault)
    active.select(
        active.preview_selection(
            "self_portrait",
            None,
            expected_selection_version=active.get_selection("self_portrait").selection_version,
        ),
        confirmed=True,
    )
    return active._root("self_portrait"), lambda: active._history("self_portrait")


def _committed(root):
    return next(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))


@pytest.mark.parametrize("domain", ["review", "revision", "selection", "archive", "conversion"])
def test_pending_rename_after_enumeration_is_a_safe_old_snapshot(tmp_path, monkeypatch, domain):
    root, read = _seed(tmp_path, domain)
    final = _committed(root)
    pending = final.with_name(".pending-" + final.name)
    final.rename(pending)
    entries = ReportReviewService._entries
    captured = False

    def enumerate_then_commit(io, directory):
        nonlocal captured
        result = entries(io, directory)
        if directory == root and not captured:
            captured = True
            assert pending in result
            pending.rename(final)
        return result

    monkeypatch.setattr(ReportReviewService, "_entries", enumerate_then_commit)
    # This uses the internal reader to expose unexpected raw filesystem exceptions.
    assert read()[0] == []
    assert captured and final.is_dir()
    assert len(read()[0]) == 1


@pytest.mark.parametrize("domain", ["review", "revision", "selection", "archive", "conversion"])
def test_pending_commit_during_path_resolution_retains_safe_snapshot(tmp_path, monkeypatch, domain):
    root, read = _seed(tmp_path, domain)
    final = _committed(root)
    pending = final.with_name(".pending-" + final.name)
    final.rename(pending)
    resolve = Path.resolve
    triggered = False

    def resolving_handle(path, *args, **kwargs):
        nonlocal triggered
        if path == pending and not triggered:
            triggered = True
            pending.rename(final)
            return resolve(final, *args, **kwargs)
        return resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolving_handle)
    assert read()[0] == []
    assert triggered and final.is_dir()
    assert len(read()[0]) == 1


@pytest.mark.parametrize("attack", ["wrong_target", "recreated_pending", "different_identity"])
def test_pending_resolution_change_does_not_hide_unsafe_replacement(tmp_path, monkeypatch, attack):
    root, read = _seed(tmp_path, "archive")
    final = _committed(root)
    pending = final.with_name(".pending-" + final.name)
    final.rename(pending)
    resolve = Path.resolve
    triggered = False

    def resolving_handle(path, *args, **kwargs):
        nonlocal triggered
        if path == pending and not triggered:
            triggered = True
            if attack == "wrong_target":
                other = final.with_name("f" * 32 if final.name != "f" * 32 else "e" * 32)
                pending.rename(other)
                return resolve(other, *args, **kwargs)
            pending.rename(final)
            if attack == "recreated_pending":
                pending.mkdir()
            else:
                final.rename(root / "different-directory")
                final.mkdir()
            return resolve(final, *args, **kwargs)
        return resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolving_handle)
    with pytest.raises(ValueError):
        read()
    assert triggered


@pytest.mark.parametrize("domain", ["review", "revision", "selection", "archive", "conversion"])
@pytest.mark.parametrize("removed", ["committed", "lock", "parent"])
def test_disappearance_of_authoritative_entry_or_parent_is_not_swallowed(
    tmp_path, monkeypatch, domain, removed
):
    root, read = _seed(tmp_path, domain)
    final = _committed(root)
    pending = final.with_name(".pending-" + final.name)
    if removed == "parent":
        final.rename(pending)
    entries = ReportReviewService._entries
    triggered = False

    def enumerate_then_remove(io, directory):
        nonlocal triggered
        result = entries(io, directory)
        if directory == root and not triggered:
            triggered = True
            # Moves stay inside the synthetic workspace; nothing is deleted.
            if removed == "parent":
                root.rename(root.with_name(root.name + "-moved"))
                result.sort(key=lambda path: not path.name.startswith(".pending-"))
            elif removed == "lock":
                (root / ".writer.lock").rename(root / ".writer-moved")
            else:
                final.rename(root / "committed-moved")
        return result

    monkeypatch.setattr(ReportReviewService, "_entries", enumerate_then_remove)
    with pytest.raises((OSError, ValueError)):
        read()
    assert triggered


@pytest.mark.parametrize("domain", ["review", "revision", "selection", "archive", "conversion"])
@pytest.mark.parametrize("unsafe", ["file", "bad_name", "reparse"])
def test_existing_malformed_or_reparse_pending_entries_stay_rejected(
    tmp_path, monkeypatch, domain, unsafe
):
    root, read = _seed(tmp_path, domain)
    pending = root / (".pending-invalid" if unsafe == "bad_name" else ".pending-" + "a" * 32)
    if unsafe == "file":
        pending.write_bytes(b"Not a directory.")
    else:
        pending.mkdir()
    if unsafe == "reparse":
        original = Path.lstat

        def reparse_metadata(path, *args, **kwargs):
            if path == pending:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400, st_nlink=1)
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "lstat", reparse_metadata)
    with pytest.raises((OSError, ValueError)):
        read()


@pytest.mark.parametrize("domain", ["review", "revision", "selection", "archive", "conversion"])
def test_lock_creation_zero_byte_window_is_metadata_only(tmp_path, domain):
    root, read = _seed(tmp_path, domain)
    lock = root / ".writer.lock"
    lock.write_bytes(b"")
    assert len(read()[0]) == 1
    lock.write_bytes(b"0")
    assert len(read()[0]) == 1
