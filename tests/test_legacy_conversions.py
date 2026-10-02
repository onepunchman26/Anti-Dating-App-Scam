"""Synthetic complete-entry conversion; no model, real profile or external source reads."""

import copy
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from anti_dating_scam.reports.local_artifacts import validate_local_artifact
from anti_dating_scam.reports.localized_reports import validate_localization
from anti_dating_scam.services import legacy_conversions as module
from anti_dating_scam.services.legacy_conversions import (
    LegacyConversionError,
    LegacyConversionService,
)
from anti_dating_scam.services.legacy_reports import LegacyReportService
from anti_dating_scam.services.report_review import ReportReviewService, _encode, _hash


def _claim(kind="self_portrait"):
    return {
        "topic": "communication",
        "claim" if kind == "self_portrait" else "criterion": {
            "en": "May prefer a quiet pause.", "zh": "可能偏好安静地暂停。",
        },
        "type": "inference", "confidence": "low",
        "evidence": [{"quote": "I take a quiet pause.\r\nSynthetic only.",
                      "source": "synthetic-note"}],
        "unknown_claim_field": {"opaque": ["KEEP", None, 2]},
    }


def _value(kind):
    value = {
        "schema_version": "0.3" if kind == "self_portrait" else "0.1",
        "caveats": [{"en": "Synthetic source; not proof.", "zh": "合成来源，不能作为证明。"}],
        "unknown_extension": {"preserve": ["EXACT", None, 1]},
    }
    if kind == "self_portrait":
        value.update(claims=[_claim(kind)], top_values=[{"name": "Unsupported inference"}],
                     consistency_findings=[{"quotes": ["Incomplete"]}])
    else:
        value.update(stated_criteria=[_claim(kind)], revealed_criteria=[],
                     contradictions=["Incomplete contradiction"])
    return value


def _fixture(tmp_path, kind="self_portrait", value=None):
    vault = tmp_path / "vault"
    reports = vault / "reports"
    reports.mkdir(parents=True)
    value = _value(kind) if value is None else value
    source = reports / f"{kind}.json"
    source.write_bytes(b"\xef\xbb\xbf" + json.dumps(value, ensure_ascii=False, indent=3).encode()
                       + b"\r\n  ")
    (reports / f"{kind}.md").write_bytes(b"# Unconverted synthetic original\r\n")
    archive_service = LegacyReportService(vault)
    archive = archive_service.save_archive(archive_service.preview_archive(
        kind, expected_digest=archive_service.inspect(kind).source_digest,
    ), confirmed=True)
    return LegacyConversionService(vault), source, archive


def _preview(service, archive):
    return service.preview_conversion(archive.kind, archive.id)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_convert_only_complete_claims_and_reopen_after_original_changes(tmp_path, kind):
    service, source, archive = _fixture(tmp_path, kind)
    original = {path.name: path.read_bytes() for path in source.parent.iterdir() if path.is_file()}
    preview = _preview(service, archive)
    assert preview.eligible and preview.converted_count == 1
    target = preview.canonical["report" if kind == "self_portrait" else "criteria"]
    claims = target["claims" if kind == "self_portrait" else "stated"]
    expected = _claim(kind)
    assert claims == [{
        "claim": expected["claim" if kind == "self_portrait" else "criterion"]["zh"],
        **{key: expected[key] for key in ("topic", "type", "confidence", "evidence")},
    }]
    assert target["caveats"][0] == _value(kind)["caveats"][0]["zh"]
    assert target["open_questions"] == []
    if kind == "self_portrait":
        assert target["data_coverage"]["sources_read"] == []
        assert target["consistency_findings"] == []
        assert "headline" not in target
    else:
        assert preview.canonical["ideal_profiles"]["candidates"] == []
    assert any(item.pointer == "/unknown_extension" and item.status == "archive_only"
               for item in preview.field_ledger)
    assert any(item.pointer.endswith("/evidence") and item.status == "copied"
               for item in preview.field_ledger)
    validate_local_artifact(target, kind)
    validate_localization(kind, preview.canonical, preview.localized_text)
    assert "Partial legacy conversion" in preview.markdown
    assert "旧报告的部分转换" in preview.markdown
    saved = service.save_conversion(preview, confirmed=True)
    assert {
        path.name: path.read_bytes() for path in source.parent.iterdir() if path.is_file()
    } == original
    assert not (source.parent / "active_selections").exists()
    assert not (source.parent / "reviewed_copies").exists()
    restarted = LegacyConversionService(source.parent.parent)
    assert restarted.list_conversions(kind) == [saved]
    assert restarted.read_conversion(kind, saved.id) == preview
    bundle = restarted.read_verified_bundle(kind, saved.id)
    assert bundle.canonical == preview.canonical
    assert bundle.source_digest == archive.source_digest
    assert bundle.integrity_digest == saved.integrity_digest
    source.write_bytes(b"Replaced current original, outside conversion history.")
    assert restarted.read_conversion(kind, saved.id) == preview
    with pytest.raises(LegacyConversionError):
        _preview(restarted, archive)
    assert LegacyReportService(source.parent.parent).read_snapshot(
        kind, archive.id, source.name,
    ) == original[source.name]


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("missing", ["topic", "type", "confidence", "evidence", "bilingual"])
def test_missing_metadata_never_defaulted_or_promoted(tmp_path, kind, missing):
    value = _value(kind)
    group = "claims" if kind == "self_portrait" else "stated_criteria"
    entry = value[group][0]
    if missing == "bilingual":
        entry["claim" if kind == "self_portrait" else "criterion"] = "Untranslated statement"
    else:
        del entry[missing]
    service, source, archive = _fixture(tmp_path, kind, value)
    preview = _preview(service, archive)
    assert not preview.eligible and preview.converted_count == 0
    assert any(issue.code == "no_complete_claims" for issue in preview.issues)
    assert any(item.pointer == f"/{group}/0" and item.status == "archive_only"
               for item in preview.field_ledger)
    with pytest.raises(LegacyConversionError):
        service.save_conversion(preview, confirmed=True)
    assert not (source.parent / "converted_reports").exists()


def test_actual_historical_sample_is_blocked_without_fabrication(tmp_path):
    from test_self_portrait_html import SAMPLE

    service, _, archive = _fixture(tmp_path, value=copy.deepcopy(SAMPLE))
    preview = _preview(service, archive)
    assert not preview.eligible and preview.converted_count == 0
    assert preview.canonical["report"]["claims"] == []
    assert preview.canonical["report"]["consistency_findings"] == []
    with pytest.raises(LegacyConversionError):
        service.save_conversion(preview, confirmed=True)


def test_mixed_entries_have_explicit_partial_ledger(tmp_path):
    value = _value("self_portrait")
    value["claims"].append({"claim": {"en": "Unsupported statement", "zh": "无依据的陈述"}})
    service, _, archive = _fixture(tmp_path, value=value)
    preview = _preview(service, archive)
    assert preview.eligible and preview.converted_count == 1
    assert any(item.pointer == "/claims/1" and item.status == "archive_only"
               for item in preview.field_ledger)
    service.save_conversion(preview, confirmed=True)


@pytest.mark.parametrize("key", ["x" * 4_000, "~" * 2_000])
def test_overlong_field_pointer_is_explicitly_grouped_without_losing_original(tmp_path, key):
    value = _value("self_portrait")
    value[key] = {"opaque": "Keep this synthetic extension exactly."}
    service, source, archive = _fixture(tmp_path, value=value)
    original = source.read_bytes()
    preview = _preview(service, archive)
    assert preview.eligible and preview.converted_count == 1
    assert any(item.code == "ledger_grouped" for item in preview.issues)
    assert any(item.pointer == "" and item.status == "partial" for item in preview.field_ledger)
    assert all(len(item.pointer) <= 4_000 for item in preview.field_ledger)
    saved = service.save_conversion(preview, confirmed=True)
    assert service.read_conversion("self_portrait", saved.id) == preview
    assert LegacyReportService(source.parent.parent).read_snapshot(
        "self_portrait", archive.id, source.name,
    ) == original


def test_criteria_single_quote_and_source_copied_exactly(tmp_path):
    value = _value("mate_criteria")
    entry = value["stated_criteria"][0]
    entry.update(evidence="Exact synthetic quotation.\r\n", source="not-a-file-to-open")
    service, _, archive = _fixture(tmp_path, "mate_criteria", value)
    preview = _preview(service, archive)
    assert preview.canonical["criteria"]["stated"][0]["evidence"] == [{
        "quote": "Exact synthetic quotation.\r\n", "source": "not-a-file-to-open",
    }]
    service.save_conversion(preview, confirmed=True)


@pytest.mark.parametrize("caveats", [["Untranslated warning"], [], None,
                                     [{"en": "Incomplete"}],
                                     [{"en": "Warning", "zh": "警示"}] * 30])
def test_existing_caveats_cannot_silently_disappear(tmp_path, caveats):
    value = _value("self_portrait")
    value["caveats"] = caveats
    service, _, archive = _fixture(tmp_path, value=value)
    preview = _preview(service, archive)
    assert preview.converted_count == 1
    if caveats == []:
        assert preview.eligible
        service.save_conversion(preview, confirmed=True)
    else:
        assert not preview.eligible
        with pytest.raises(LegacyConversionError):
            service.save_conversion(preview, confirmed=True)


@pytest.mark.parametrize("value", [None, [], "old prose", {"schema_version": "0.2"}])
def test_unknown_primary_shape_is_inspectable_but_ineligible(tmp_path, value):
    service, _, archive = _fixture(tmp_path, value={"unrecognized": value})
    preview = _preview(service, archive)
    assert not preview.eligible
    assert any(issue.code == "unsupported_shape" for issue in preview.issues)


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "yes", []])
def test_strict_explicit_confirmation_has_no_write(tmp_path, confirmed):
    service, source, archive = _fixture(tmp_path)
    with pytest.raises(LegacyConversionError):
        service.save_conversion(_preview(service, archive), confirmed=confirmed)
    assert not (source.parent / "converted_reports").exists()


@pytest.mark.parametrize("mutation", ["source", "added_companion", "removed_companion"])
def test_preview_bound_to_current_presence_and_exact_bytes(tmp_path, mutation):
    service, source, archive = _fixture(tmp_path)
    preview = _preview(service, archive)
    if mutation == "source":
        source.write_bytes(source.read_bytes() + b" ")
    elif mutation == "added_companion":
        source.with_name("self_portrait.html").write_bytes(b"new synthetic companion")
    else:
        source.with_suffix(".md").rename(source.with_suffix(".moved"))
    with pytest.raises(LegacyConversionError):
        service.save_conversion(preview, confirmed=True)
    assert not (source.parent / "converted_reports").exists()


@pytest.mark.parametrize("field,value", [("eligible", False), ("converted_count", 0),
                                        ("markdown", "Tampered"),
                                        ("archive_digest", "a" * 64)])
def test_preview_mutation_cannot_authorize_output(tmp_path, field, value):
    service, _, archive = _fixture(tmp_path)
    preview = _preview(service, archive).model_copy(update={field: value})
    with pytest.raises(LegacyConversionError):
        service.save_conversion(preview, confirmed=True)


@pytest.mark.parametrize("member", ["preview.json", "canonical.json", "report.md",
                                    "report.detailed.md", "manifest.json"])
def test_saved_member_tampering_fails_closed(tmp_path, member):
    service, _, archive = _fixture(tmp_path)
    saved = service.save_conversion(_preview(service, archive), confirmed=True)
    target = Path(saved.directory_path) / member
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(LegacyConversionError):
        service.read_conversion("self_portrait", saved.id)
    with pytest.raises(LegacyConversionError):
        service.list_conversions("self_portrait")


def test_recomputed_file_checksums_cannot_change_deterministic_derivation(tmp_path):
    service, _, archive = _fixture(tmp_path)
    saved = service.save_conversion(_preview(service, archive), confirmed=True)
    folder = Path(saved.directory_path)
    target = folder / "report.md"
    target.write_bytes(b"An invented report")
    manifest = json.loads((folder / "manifest.json").read_bytes())
    manifest["files"]["report.md"] = _hash(target.read_bytes())
    manifest["integrity_digest"] = _hash(_encode({k: v for k, v in manifest.items()
                                                 if k != "integrity_digest"}))
    (folder / "manifest.json").write_bytes(_encode(manifest))
    with pytest.raises(LegacyConversionError):
        service.read_verified_bundle("self_portrait", saved.id)


def test_archive_companion_tampering_invalidates_entire_conversion(tmp_path):
    service, source, archive = _fixture(tmp_path)
    saved = service.save_conversion(_preview(service, archive), confirmed=True)
    (Path(archive.directory_path) / source.with_suffix(".md").name).write_bytes(b"TAMPER")
    with pytest.raises(LegacyConversionError):
        service.read_conversion("self_portrait", saved.id)


@pytest.mark.parametrize("identifier", ["../escape", "", "A" * 32, "g" * 32, 1, None])
def test_fixed_archive_and_conversion_ids_only(tmp_path, identifier):
    service, _, _ = _fixture(tmp_path)
    with pytest.raises(LegacyConversionError):
        service.preview_conversion("self_portrait", identifier)
    with pytest.raises(LegacyConversionError):
        service.read_conversion("self_portrait", identifier)


def test_no_error_echoes_private_synthetic_payload(tmp_path):
    service, _, archive = _fixture(tmp_path)
    preview = _preview(service, archive).model_copy(update={"markdown": {"SECRET_SENTINEL": 1}})
    with pytest.raises(LegacyConversionError) as error:
        service.save_conversion(preview, confirmed=True)
    assert "SECRET_SENTINEL" not in str(error.value)
    assert str(tmp_path) not in str(error.value)


def test_partial_write_remains_pending_and_originals_unchanged(tmp_path, monkeypatch):
    service, source, archive = _fixture(tmp_path)
    original = source.read_bytes()
    write = ReportReviewService._write_new

    def fail_on_render(io, path, raw):
        if path.name == "report.md":
            raise OSError("synthetic write failure")
        return write(io, path, raw)

    monkeypatch.setattr(ReportReviewService, "_write_new", fail_on_render)
    with pytest.raises(LegacyConversionError):
        service.save_conversion(_preview(service, archive), confirmed=True)
    assert service.list_conversions("self_portrait") == []
    assert source.read_bytes() == original


@pytest.mark.parametrize("constant", ["MAX_CONVERSIONS", "MAX_CONVERSION_BYTES",
                                      "MAX_HISTORY_BYTES"])
def test_bounded_storage_rejects_without_committed_output(tmp_path, monkeypatch, constant):
    service, _, archive = _fixture(tmp_path)
    preview = _preview(service, archive)
    monkeypatch.setattr(module, constant, 0)
    with pytest.raises(LegacyConversionError):
        service.save_conversion(preview, confirmed=True)
    assert service.list_conversions("self_portrait") == []


def test_multiple_thread_writes_are_complete_distinct_and_reopenable(tmp_path):
    service, source, archive = _fixture(tmp_path)
    preview = _preview(service, archive)

    def save(_):
        return LegacyConversionService(source.parent.parent).save_conversion(
            preview, confirmed=True,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(save, range(4)))
    assert len({record.id for record in records}) == 4
    assert len(service.list_conversions("self_portrait")) == 4
    assert all(service.read_conversion("self_portrait", record.id) == preview for record in records)


def test_hardlinked_member_is_not_accepted(tmp_path):
    service, _, archive = _fixture(tmp_path)
    saved = service.save_conversion(_preview(service, archive), confirmed=True)
    path = Path(saved.directory_path) / "report.md"
    os.link(path, tmp_path / "synthetic-hardlink.md")
    with pytest.raises(LegacyConversionError):
        service.read_conversion("self_portrait", saved.id)


def test_preview_reads_only_fixed_report_and_archive_paths(tmp_path):
    value = _value("mate_criteria")
    value["stated_criteria"][0]["evidence"][0]["source"] = "../../private-source-never-opened"
    service, _, archive = _fixture(tmp_path, "mate_criteria", value)
    preview = _preview(service, archive)
    assert preview.eligible
    assert preview.canonical["criteria"]["stated"][0]["evidence"][0]["source"] == (
        "../../private-source-never-opened"
    )
