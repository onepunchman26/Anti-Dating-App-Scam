"""Lossless synthetic legacy preservation without semantic conversion or activation."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services import legacy_reports as module
from anti_dating_scam.services.legacy_reports import LegacyReportError, LegacyReportService
from anti_dating_scam.services.report_review import _encode, _hash


def _fixture(tmp_path, kind="self_portrait", raw=None):
    vault = tmp_path / "vault"
    reports = vault / "reports"
    reports.mkdir(parents=True)
    value = (
        {
            "schema_version": "0.3",
            "top_values": [{"name": {"en": "Example", "zh": "例子"}}],
            "unknown_extension": {"kept": [1, None, "untouched"]},
        }
        if kind == "self_portrait"
        else {
            "schema_version": "0.1",
            "stated_criteria": [{"criterion": "Legacy text", "evidence": ""}],
            "unknown_extension": "Do not discard this legacy field.",
        }
    )
    source = reports / f"{kind}.json"
    source.write_bytes(
        raw
        if raw is not None
        else b"\xef\xbb\xbf" + (json.dumps(value, indent=3) + "\r\n  ").encode()
    )
    (reports / f"{kind}.md").write_bytes(
        b"# Synthetic legacy source\r\nNo invented translations.\r\n"
    )
    return LegacyReportService(vault), source


def _preview(service, kind="self_portrait"):
    return service.preview_archive(kind, expected_digest=service.inspect(kind).source_digest)


@pytest.mark.parametrize(
    "kind,expected_format",
    [
        ("self_portrait", "self_portrait_v03"),
        ("mate_criteria", "mate_criteria_legacy_v01"),
    ],
)
def test_exact_bundle_preserved_reopened_and_originals_never_rewritten(
    tmp_path, kind, expected_format
):
    service, source = _fixture(tmp_path, kind)
    if kind == "self_portrait":
        source.with_name("self_portrait.html").write_bytes(b"<script>do_not_execute()</script>")
    original = {path.name: path.read_bytes() for path in source.parent.iterdir()}
    inspection = service.inspect(kind)
    assert inspection.format == expected_format
    preview = _preview(service, kind)
    assert not (source.parent / "legacy_archives").exists()
    assert any(item.pointer == "/unknown_extension" for item in preview.field_ledger)
    assert all(item.status == "preserved_only" for item in preview.field_ledger)
    assert "no conversion" in preview.review_text_en
    assert "不进行格式转换" in preview.review_text_zh
    assert preview.files[0].text.startswith("\ufeff")
    saved = service.save_archive(preview, confirmed=True)
    assert all(source.with_name(label).read_bytes() == raw for label, raw in original.items())
    assert not (source.parent / "reviewed_copies").exists()
    assert not (source.parent / "active_selections").exists()
    restarted = LegacyReportService(source.parent.parent)
    assert restarted.list_archives(kind) == [saved]
    assert restarted.read_archive(kind, saved.id) == preview
    assert all(
        restarted.read_snapshot(kind, saved.id, label) == raw for label, raw in original.items()
    )
    source.write_bytes(b"A newer source replaces only the current file.")
    assert restarted.read_snapshot(kind, saved.id, source.name) == original[source.name]
    assert restarted.read_archive(kind, saved.id) == preview


@pytest.mark.parametrize(
    "raw",
    [
        b'{"broken":',
        b'{"duplicate":1,"duplicate":2}',
        b"\xff\xfe\x00\x80",
        b"\x00not JSON",
        b'{"nonfinite":NaN}',
        b'{"surrogate":"\\ud800"}',
        b"[]",
        b"null",
        b'"plain JSON string"',
        b"",
    ],
)
def test_arbitrary_bytes_and_uninterpretable_json_round_trip(tmp_path, raw):
    service, source = _fixture(tmp_path, raw=raw)
    preview = _preview(service)
    assert preview.format == "unrecognized"
    saved = service.save_archive(preview, confirmed=True)
    assert service.read_snapshot("self_portrait", saved.id, source.name) == raw
    assert source.read_bytes() == raw
    if raw.startswith(b"\xff"):
        entry = next(item for item in preview.files if item.label == source.name)
        assert entry.text is None and entry.encoding == "binary"


def test_identical_schema_version_detected_by_structure_not_version(tmp_path):
    service, source = _fixture(tmp_path, "mate_criteria")
    assert service.inspect("mate_criteria").format == "mate_criteria_legacy_v01"
    current = {
        "schema_version": "0.1",
        "report_type": "mate_criteria",
        "stated": [],
        "revealed": [],
        "open_questions": [],
        "caveats": ["Unknown context."],
    }
    source.write_bytes(_encode(current))
    assert service.inspect("mate_criteria").format == "current_structured"
    current["stated_criteria"] = []
    source.write_bytes(_encode(current))
    assert service.inspect("mate_criteria").format == "unrecognized"


def test_missing_members_not_filled_or_translated_and_presence_bound(tmp_path):
    service, source = _fixture(tmp_path)
    preview = _preview(service)
    missing = next(
        item for item in preview.files if item.label == "self_portrait_localization.json"
    )
    assert not missing.present and missing.sha256 is None and missing.text is None
    source.with_name(missing.label).write_bytes(b"")
    assert service.inspect("self_portrait").source_digest != preview.source_digest
    with pytest.raises(LegacyReportError):
        service.save_archive(preview, confirmed=True)
    assert not (source.parent / "legacy_archives").exists()


def test_markdown_only_and_completely_missing_sources(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    service = LegacyReportService(vault)
    assert service.inspect("self_portrait").format == "missing"
    assert service.list_archives("self_portrait") == []
    assert not (vault / "reports").exists()
    with pytest.raises(LegacyReportError):
        _preview(service)
    (vault / "reports").mkdir()
    (vault / "reports" / "self_portrait.md").write_bytes(b"Only an old report narrative.")
    assert service.inspect("self_portrait").format == "markdown_only"
    saved = service.save_archive(_preview(service), confirmed=True)
    with pytest.raises(LegacyReportError):
        service.read_snapshot("self_portrait", saved.id, "self_portrait.json")


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true", []])
def test_confirmation_is_strict_and_cancel_makes_no_archive(tmp_path, confirmed):
    service, source = _fixture(tmp_path)
    with pytest.raises(LegacyReportError):
        service.save_archive(_preview(service), confirmed=confirmed)
    assert not (source.parent / "legacy_archives").exists()


@pytest.mark.parametrize("change", ["bytes", "missing", "new_member"])
def test_source_tuple_changes_including_absence_rejected(tmp_path, change):
    service, source = _fixture(tmp_path)
    preview = _preview(service)
    if change == "bytes":
        source.write_bytes(source.read_bytes() + b" ")
    elif change == "missing":
        source.rename(source.with_suffix(".preserved"))
    else:
        source.with_name("self_portrait.detailed.md").write_bytes(b"A new source file.")
    with pytest.raises(LegacyReportError):
        service.save_archive(preview, confirmed=True)
    assert not (source.parent / "legacy_archives").exists()


@pytest.mark.parametrize("field", ["review_text_en", "preview_digest", "files", "field_ledger"])
def test_shallow_or_nested_preview_tampering_rejected(tmp_path, field):
    service, source = _fixture(tmp_path)
    preview = _preview(service)
    updates = {
        "review_text_en": "Unreviewed text",
        "preview_digest": "a" * 64,
        "files": preview.files[:-1],
        "field_ledger": [],
    }
    with pytest.raises(LegacyReportError):
        service.save_archive(preview.model_copy(update={field: updates[field]}), confirmed=True)
    assert not (source.parent / "legacy_archives").exists()


@pytest.mark.parametrize(
    "label",
    [
        "../outside",
        "self_portrait.json/../outside",
        "manifest.json",
        "",
        "ideal_partner_profiles.json",
    ],
)
def test_snapshot_labels_are_fixed_and_kind_scoped(tmp_path, label):
    service, source = _fixture(tmp_path)
    saved = service.save_archive(_preview(service), confirmed=True)
    with pytest.raises(LegacyReportError):
        service.read_snapshot("self_portrait", saved.id, label)


@pytest.mark.parametrize("label", ["self_portrait.json", "preview.json", "manifest.json"])
def test_corruption_fails_closed_before_any_snapshot_return(tmp_path, label):
    service, source = _fixture(tmp_path)
    saved = service.save_archive(_preview(service), confirmed=True)
    path = Path(saved.directory_path) / label
    path.write_bytes(path.read_bytes() + b"PRIVATE_CORRUPTION")
    for action in (
        lambda: service.read_archive("self_portrait", saved.id),
        lambda: service.read_snapshot("self_portrait", saved.id, "self_portrait.md"),
        lambda: service.list_archives("self_portrait"),
    ):
        with pytest.raises(LegacyReportError) as caught:
            action()
        assert "PRIVATE_CORRUPTION" not in str(caught.value)
        assert str(source) not in str(caught.value)


def test_repaired_checksums_do_not_hide_changed_preview_derivation(tmp_path):
    service, source = _fixture(tmp_path)
    saved = service.save_archive(_preview(service), confirmed=True)
    folder = Path(saved.directory_path)
    preview = json.loads((folder / "preview.json").read_bytes())
    preview["format"] = "current_structured"
    raw = _encode(preview)
    (folder / "preview.json").write_bytes(raw)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    manifest["files"]["preview.json"] = _hash(raw)
    manifest.pop("manifest_digest")
    manifest["manifest_digest"] = _hash(_encode(manifest))
    (folder / "manifest.json").write_bytes(_encode(manifest))
    with pytest.raises(LegacyReportError):
        service.read_archive("self_portrait", saved.id)


@pytest.mark.parametrize("change", ["write_failure", "new_member", "changed_member"])
def test_staging_failure_retains_originals_and_previous_archive(tmp_path, monkeypatch, change):
    service, source = _fixture(tmp_path)
    preview = _preview(service)
    saved = service.save_archive(preview, confirmed=True)
    write = service._io._write_new

    def interfere(path, raw):
        if change == "write_failure" and path.name == "preview.json":
            raise OSError("PRIVATE_DISK_ERROR")
        result = write(path, raw)
        if change != "write_failure" and path.name == "manifest.json":
            target = (
                source if change == "changed_member" else source.with_name("self_portrait.html")
            )
            target.write_bytes(b"Synthetic concurrent update.")
        return result

    monkeypatch.setattr(service._io, "_write_new", interfere)
    with pytest.raises(LegacyReportError) as caught:
        service.save_archive(preview, confirmed=True)
    assert "PRIVATE_DISK_ERROR" not in str(caught.value)
    assert service.list_archives("self_portrait") == [saved]
    assert service.read_archive("self_portrait", saved.id) == preview


def test_concurrent_save_list_and_restart_have_complete_unique_archives(tmp_path):
    service, source = _fixture(tmp_path)
    preview = _preview(service)

    def save(_):
        archive = LegacyReportService(source.parent.parent).save_archive(preview, confirmed=True)
        service.list_archives("self_portrait")
        return archive

    with ThreadPoolExecutor(max_workers=4) as pool:
        saved = list(pool.map(save, range(8)))
    assert len({item.id for item in saved}) == 8
    restarted = LegacyReportService(source.parent.parent)
    assert len(restarted.list_archives("self_portrait")) == 8
    assert all(restarted.read_archive("self_portrait", item.id) == preview for item in saved)


def test_large_field_ledger_grouping_is_explicit_and_full_source_survives(tmp_path):
    data = {f"unknown{i}": i for i in range(module.MAX_LEDGER_FIELDS + 1)}
    raw = _encode(data)
    service, source = _fixture(tmp_path, raw=raw)
    preview = _preview(service)
    assert any(issue.code == "ledger_grouped" for issue in preview.issues)
    assert any(
        item.pointer == "" and item.file_label == source.name for item in preview.field_ledger
    )
    saved = service.save_archive(preview, confirmed=True)
    assert service.read_snapshot("self_portrait", saved.id, source.name) == raw


def test_limits_reject_without_truncation_or_overwriting_history(tmp_path, monkeypatch):
    service, source = _fixture(tmp_path)
    preview = _preview(service)
    saved = service.save_archive(preview, confirmed=True)
    monkeypatch.setattr(module, "MAX_ARCHIVES", 1)
    with pytest.raises(LegacyReportError):
        service.save_archive(preview, confirmed=True)
    assert service.list_archives("self_portrait") == [saved]
    source.write_bytes(b"x" * (module.MAX_FILE_BYTES + 1))
    with pytest.raises(LegacyReportError):
        service.inspect("self_portrait")
    assert source.stat().st_size == module.MAX_FILE_BYTES + 1


def test_hardlinked_source_and_saved_snapshot_rejected(tmp_path):
    service, source = _fixture(tmp_path)
    saved = service.save_archive(_preview(service), confirmed=True)
    os.link(Path(saved.directory_path) / source.name, tmp_path / "snapshot-alias")
    with pytest.raises(LegacyReportError):
        service.read_archive("self_portrait", saved.id)
    os.link(source, tmp_path / "source-alias")
    with pytest.raises(LegacyReportError):
        service.inspect("self_portrait")


def test_no_outbound_calls_or_source_label_reads(tmp_path, monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        pytest.fail("Archives cannot make outbound calls")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    service, source = _fixture(tmp_path, raw=b'{"claims":[{"source":"../not-a-file"}]}')
    saved = service.save_archive(_preview(service), confirmed=True)
    assert service.read_snapshot("self_portrait", saved.id, source.name) == source.read_bytes()


@pytest.mark.parametrize(
    "companion",
    [
        "missing_locale",
        "bad_locale",
        "incomplete_locale",
        "missing_profiles",
        "bad_profiles",
        "complete",
    ],
)
def test_current_shape_has_explicit_complete_or_incomplete_companion_diagnostics(
    tmp_path, companion
):
    service, source = _fixture(tmp_path, "mate_criteria")
    criteria = {
        "schema_version": "0.1",
        "report_type": "mate_criteria",
        "stated": [],
        "revealed": [],
        "open_questions": [],
        "caveats": ["Unknown context."],
    }
    profiles = {"schema_version": "0.1", "candidates": [], "caveats": ["Fictional only."]}
    canonical = {"criteria": criteria, "ideal_profiles": profiles}
    source.write_bytes(_encode(criteria))
    profile_path = source.with_name("ideal_partner_profiles.json")
    if companion != "missing_profiles":
        profile_path.write_bytes(
            b"invalid JSON" if companion == "bad_profiles" else _encode(profiles)
        )
    if companion != "missing_locale":
        entries = [
            {"path": pointer, "source": text, "en": text, "zh": "合成译文"}
            for pointer, text in required_localization_sources("mate_criteria", canonical).items()
        ]
        locale_raw = _encode({"schema_version": "0.1", "localized_text": entries})
        if companion == "bad_locale":
            locale_raw = b'{"malformed":'
        elif companion == "incomplete_locale":
            locale_raw = _encode({"schema_version": "0.1", "localized_text": []})
        source.with_name("mate_criteria_localization.json").write_bytes(locale_raw)
    inspection = service.inspect("mate_criteria")
    assert inspection.format == "current_structured"
    codes = {issue.code for issue in inspection.issues}
    assert "current_shape_only" in codes
    assert ("complete_current_bundle" in codes) is (companion == "complete")
    assert ("invalid_current_bundle" in codes) is (companion != "complete")
    expected = {
        "missing_locale": "missing_localization",
        "bad_locale": "invalid_localization",
        "incomplete_locale": "invalid_localization",
        "missing_profiles": "missing_ideal_profiles",
        "bad_profiles": "invalid_ideal_profiles",
        "complete": "complete_current_bundle",
    }
    assert expected[companion] in codes
    preview = _preview(service, "mate_criteria")
    saved = service.save_archive(preview, confirmed=True)
    assert service.read_archive("mate_criteria", saved.id) == preview


def test_long_escaped_json_pointer_groups_ledger_without_losing_original(tmp_path, monkeypatch):
    raw = _encode({"~" * 60: 1})
    service, source = _fixture(tmp_path, raw=raw)
    monkeypatch.setattr(module, "MAX_FILE_BYTES", 100)
    preview = _preview(service)
    assert any(issue.code == "ledger_grouped" for issue in preview.issues)
    saved = service.save_archive(preview, confirmed=True)
    assert service.read_snapshot("self_portrait", saved.id, source.name) == raw
