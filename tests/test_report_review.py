import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from anti_dating_scam.services import report_review as module
from anti_dating_scam.services.report_review import ReportReviewError, ReportReviewService


def _claim(text="May prefer calm discussion."):
    return {
        "topic": "communication",
        "claim": text,
        "type": "inference",
        "confidence": "low",
        "evidence": [{"quote": "I pause before replying.", "source": "../not-a-file-to-read"}],
    }


def _payload(kind="self_portrait", text="May prefer calm discussion."):
    if kind == "self_portrait":
        return {
            "schema_version": "0.2",
            "report_type": kind,
            "data_coverage": {"sources_read": ["synthetic"], "covered": [], "not_covered": []},
            "claims": [_claim(text)],
            "consistency_findings": [],
            "open_questions": [],
            "caveats": ["One synthetic statement; interpretation remains uncertain."],
        }
    return {
        "schema_version": "0.1",
        "report_type": kind,
        "stated": [_claim(text)],
        "revealed": [],
        "open_questions": [],
        "caveats": ["Limited synthetic interview."],
    }


def _store(tmp_path, kind="self_portrait", text="May prefer calm discussion."):
    vault = tmp_path / "vault"
    reports = vault / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    source = reports / f"{kind}.json"
    # Deliberately preserve original indentation, CRLF and trailing whitespace.
    source.write_bytes((json.dumps(_payload(kind, text), indent=3) + "\r\n  ").encode())
    return ReportReviewService(vault), source


def _save(service, kind="self_portrait", **overrides):
    document = service.inspect(kind)
    arguments = {
        "expected_digest": document.report_digest,
        "target_path": document.claims[0].path,
        "correction_text": "A pause is situational, not a stable preference.",
        "reason": "The note describes one occasion.",
        "confirmed": True,
    }
    arguments.update(overrides)
    return service.record_correction(kind, **arguments)


def _folder(source, record):
    return source.parent / "review_history" / record.kind / record.id


def test_inspection_is_read_only_and_never_reads_evidence_source_labels(tmp_path, monkeypatch):
    service, source = _store(tmp_path)
    original = source.read_bytes()
    calls = []
    original_open = os.open

    def limited_open(path, *args, **kwargs):
        calls.append(Path(path))
        assert Path(path) == source
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", limited_open)
    document = service.inspect("self_portrait")
    assert document.report_digest == hashlib.sha256(original).hexdigest()
    assert document.claims[0].path == "/claims/0"
    assert document.claims[0].evidence[0].source == "../not-a-file-to-read"
    assert calls == [source]
    assert not (source.parent / "review_history").exists()


def test_empty_listing_creates_nothing(tmp_path):
    service = ReportReviewService(tmp_path)
    assert service.list_corrections("self_portrait") == []
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(ReportReviewError):
        service.inspect("self_portrait")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_restart_preserves_exact_snapshot_and_never_changes_other_artifacts(tmp_path, kind):
    service, source = _store(tmp_path, kind)
    original = source.read_bytes()
    companion = source.with_name(kind + "_localization.json")
    companion.write_bytes(b"EXISTING_SYNTHETIC_LOCALIZATION")
    notes = source.parent.parent / "imports" / "original.txt"
    notes.parent.mkdir()
    notes.write_bytes(b"ORIGINAL_SYNTHETIC_NOTES")
    first = _save(service, kind)
    second = _save(service, kind, correction_text="A separate annotation.")
    assert first.id != second.id
    assert (_folder(source, first) / "source.json").read_bytes() == original
    reopened = ReportReviewService(source.parent.parent)
    assert reopened.list_corrections(kind) == [first, second]
    assert reopened.list_corrections(kind, first.report_digest) == [first, second]
    assert reopened.list_corrections(kind, "0" * 64) == []
    assert source.read_bytes() == original
    assert companion.read_bytes() == b"EXISTING_SYNTHETIC_LOCALIZATION"
    assert notes.read_bytes() == b"ORIGINAL_SYNTHETIC_NOTES"
    assert first.original_claim == service.inspect(kind).claims[0].claim


def test_stale_digest_rejected_but_prior_version_history_remains_readable(tmp_path):
    service, source = _store(tmp_path)
    first = _save(service)
    source.write_text(json.dumps(_payload(text="Different current observation.")), encoding="utf-8")
    current = source.read_bytes()
    with pytest.raises(ReportReviewError, match="report changed"):
        _save(service, expected_digest=first.report_digest)
    assert source.read_bytes() == current
    assert service.list_corrections("self_portrait") == [first]
    second = _save(service)
    assert second.report_digest != first.report_digest
    assert service.list_corrections("self_portrait", first.report_digest) == [first]


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true", "false", [], {}])
def test_only_literal_true_confirms_no_history_on_cancel(tmp_path, confirmed):
    service, source = _store(tmp_path)
    with pytest.raises(ReportReviewError, match="confirmation"):
        _save(service, confirmed=confirmed)
    assert not (source.parent / "review_history").exists()


@pytest.mark.parametrize(
    "pointer",
    [
        "/stated/0",
        "/claims/-1",
        "/claims/01",
        "/claims/1",
        "/claims/0/claim",
        "../../source",
        "/claims/0~1claim",
        0,
    ],
)
def test_invalid_or_wrong_kind_pointer_rejected_without_writes(tmp_path, pointer):
    service, source = _store(tmp_path)
    original = source.read_bytes()
    with pytest.raises(ReportReviewError):
        _save(service, target_path=pointer)
    assert source.read_bytes() == original
    assert not (source.parent / "review_history").exists()


@pytest.mark.parametrize("kind", ["../self_portrait", "self_portrait.json", "SELF_PORTRAIT", ""])
def test_kind_is_not_a_path_or_filename(tmp_path, kind):
    service, source = _store(tmp_path)
    with pytest.raises(ReportReviewError):
        service.inspect(kind)
    with pytest.raises(ReportReviewError):
        service.list_corrections(kind)
    assert not (source.parent / "review_history").exists()


@pytest.mark.parametrize(
    "raw",
    [
        b"not JSON",
        b'{"schema_version":"legacy"}',
        b"[]",
        b'{"claims":[],"claims":[]}',
        b"x" * 512_001,
    ],
    ids=["non_json", "legacy", "array", "duplicate_keys", "oversized"],
)
def test_malformed_legacy_or_oversized_source_is_preserved(tmp_path, raw):
    service, source = _store(tmp_path)
    source.write_bytes(raw)
    with pytest.raises(ReportReviewError):
        service.inspect("self_portrait")
    assert source.read_bytes() == raw
    assert not (source.parent / "review_history").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"correction_text": ""},
        {"correction_text": " "},
        {"correction_text": "x" * 8_001},
        {"correction_text": True},
        {"reason": ""},
        {"reason": "x" * 2_001},
        {"expected_digest": "../invalid"},
        {"reason": "\ud800"},
    ],
)
def test_bounds_and_invalid_unicode_raise_safe_errors(tmp_path, changes):
    service, source = _store(tmp_path)
    with pytest.raises(ReportReviewError) as exc:
        _save(service, **changes)
    message = str(exc.value)
    assert "May prefer" not in message and str(source) not in message
    assert "validation error" not in message.lower()
    assert not (source.parent / "review_history").exists()


@pytest.mark.parametrize("character", ["界", "😀", "\x00"])
def test_full_unicode_character_limits_fit_the_bounded_record(tmp_path, character):
    service, _ = _store(tmp_path, text=character * 8_000)
    saved = _save(service, correction_text=character * 8_000, reason=character * 2_000)
    assert service.list_corrections("self_portrait") == [saved]


@pytest.mark.parametrize(
    "tamper",
    [
        "source",
        "record",
        "source_hash",
        "target",
        "extra_file",
        "missing_file",
        "bad_name",
        "duplicate_keys",
    ],
)
def test_corrupt_history_is_rejected_without_overwriting_any_original(tmp_path, tamper):
    service, source = _store(tmp_path)
    record = _save(service)
    folder = _folder(source, record)
    record_path = folder / "correction.json"
    envelope = json.loads(record_path.read_text(encoding="utf-8"))
    if tamper == "source":
        (folder / "source.json").write_bytes(b"CORRUPTED_SYNTHETIC_SOURCE")
    elif tamper == "extra_file":
        (folder / "unexpected.txt").write_text("extra", encoding="utf-8")
    elif tamper == "missing_file":
        (folder / "source.json").unlink()
    elif tamper == "bad_name":
        folder.rename(folder.with_name("unrecognized"))
    elif tamper == "duplicate_keys":
        record_path.write_text('{"schema_version":"0.1","schema_version":"0.1"}', encoding="utf-8")
    else:
        if tamper == "record":
            envelope["record"]["correction_text"] = "Tampered correction."
        elif tamper == "source_hash":
            envelope["record"]["report_digest"] = "0" * 64
        else:
            envelope["record"]["target_path"] = "/claims/1"
        if tamper != "record":  # Even a recomputed record checksum cannot hide source mismatch.
            envelope["record_digest"] = module._hash(module._encode(envelope["record"]))
        record_path.write_text(json.dumps(envelope), encoding="utf-8")
    original = source.read_bytes()
    with pytest.raises(ReportReviewError):
        service.list_corrections("self_portrait", "0" * 64)
    with pytest.raises(ReportReviewError):
        _save(service)
    assert source.read_bytes() == original


def test_concurrent_saves_are_unique_and_preserve_all_annotations(tmp_path):
    service, source = _store(tmp_path)
    original = source.read_bytes()

    def save(index):
        return _save(
            ReportReviewService(source.parent.parent), correction_text=f"Annotation {index}."
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        saved = list(pool.map(save, range(16)))
    assert len({record.id for record in saved}) == 16
    assert {record.id for record in service.list_corrections("self_portrait")} == {
        record.id for record in saved
    }
    assert source.read_bytes() == original


def test_concurrent_processes_commit_complete_unique_records(tmp_path):
    service, source = _store(tmp_path)
    original = source.read_bytes()
    script = """
import sys
from pathlib import Path
from anti_dating_scam.services.report_review import ReportReviewService
service = ReportReviewService(Path(sys.argv[1]))
document = service.inspect('self_portrait')
saved = service.record_correction(
    'self_portrait', expected_digest=document.report_digest, target_path='/claims/0',
    correction_text='Synthetic concurrent annotation.', reason='Synthetic process check.',
    confirmed=True,
)
print(saved.id)
"""
    children = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(source.parent.parent)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    results = [child.communicate(timeout=15) for child in children]
    assert all(child.returncode == 0 for child in children), results
    assert len({stdout.strip() for stdout, _ in results}) == 4
    assert len(service.list_corrections("self_portrait")) == 4
    assert source.read_bytes() == original


def test_disk_failure_leaves_no_visible_partial_record_and_prior_history_intact(
    tmp_path, monkeypatch
):
    service, source = _store(tmp_path)
    previous = _save(service)
    original = source.read_bytes()
    original_write = service._write_new

    def fail_record(path, data):
        if path.name == "correction.json":
            raise OSError("SYNTHETIC_PRIVATE_ERROR")
        original_write(path, data)

    monkeypatch.setattr(service, "_write_new", fail_record)
    with pytest.raises(ReportReviewError) as exc:
        _save(service)
    assert "SYNTHETIC_PRIVATE_ERROR" not in str(exc.value)
    assert service.list_corrections("self_portrait") == [previous]
    assert source.read_bytes() == original


def test_source_change_during_save_rejects_commit_without_rewriting_new_source(
    tmp_path, monkeypatch
):
    service, source = _store(tmp_path)
    original_write = service._write_new
    new_source = json.dumps(_payload(text="New concurrent report.")).encode()

    def replace_source(path, data):
        original_write(path, data)
        if path.name == "correction.json":
            source.write_bytes(new_source)

    monkeypatch.setattr(service, "_write_new", replace_source)
    with pytest.raises(ReportReviewError, match="report changed"):
        _save(service)
    assert service.list_corrections("self_portrait") == []
    assert source.read_bytes() == new_source


def _symlink(link, target, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks unavailable on this host")


def test_symlinked_source_and_vault_are_rejected(tmp_path):
    service, source = _store(tmp_path)
    outside = tmp_path / "outside.json"
    source.rename(outside)
    _symlink(source, outside)
    with pytest.raises(ReportReviewError):
        service.inspect("self_portrait")
    alias = tmp_path / "alias"
    _symlink(alias, source.parent.parent, directory=True)
    with pytest.raises(ReportReviewError):
        ReportReviewService(alias)


def test_symlinked_history_is_never_read_or_written(tmp_path):
    service, source = _store(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    _symlink(source.parent / "review_history", outside, directory=True)
    with pytest.raises(ReportReviewError):
        service.list_corrections("self_portrait")
    with pytest.raises(ReportReviewError):
        _save(service)
    assert list(outside.iterdir()) == []


def test_hardlinked_source_is_rejected(tmp_path):
    service, source = _store(tmp_path)
    alias = tmp_path / "alias.json"
    os.link(source, alias)
    with pytest.raises(ReportReviewError):
        service.inspect("self_portrait")


def test_windows_reparse_metadata_is_rejected_even_without_symlink_support():
    from types import SimpleNamespace

    assert module._unsafe(SimpleNamespace(st_mode=0o100600, st_file_attributes=1024))


def test_history_limits_fail_without_losing_prior_data(tmp_path, monkeypatch):
    service, source = _store(tmp_path)
    previous = _save(service)
    monkeypatch.setattr(module, "MAX_RECORDS", 1)
    with pytest.raises(ReportReviewError):
        _save(service)
    assert service.list_corrections("self_portrait") == [previous]
    monkeypatch.setattr(module, "MAX_HISTORY_BYTES", 1)
    with pytest.raises(ReportReviewError):
        service.list_corrections("self_portrait")
    assert (_folder(source, previous) / "source.json").exists()


def test_review_service_has_no_provider_or_evidence_import_dependencies():
    import ast

    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any(
        name and any(part in name for part in (".ai", "http", "requests", "subprocess"))
        for name in imports
    )
