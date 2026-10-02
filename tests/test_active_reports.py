"""Synthetic acceptance tests for explicit, version-bound local report selection."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services import active_reports as module
from anti_dating_scam.services.active_reports import ActiveReportError, ActiveReportService
from anti_dating_scam.services.report_review import ReportReviewService, _encode, _hash
from anti_dating_scam.services.report_revisions import ReportRevisionService


def _seed(tmp_path, kind="self_portrait"):
    vault = tmp_path / "vault"
    reports = vault / "reports"
    reports.mkdir(parents=True)
    claims = [
        {
            "topic": "communication",
            "claim": f"Synthetic claim {index}.",
            "type": "inference",
            "confidence": "low",
            "evidence": [{"quote": f"Synthetic statement {index}.", "source": "../unread-label"}],
        }
        for index in range(2)
    ]
    common = {"report_type": kind, "open_questions": [], "caveats": ["Uncertain synthetic input."]}
    canonical = (
        {
            "report": {
                **common,
                "schema_version": "0.2",
                "claims": claims,
                "data_coverage": {"sources_read": ["synthetic"], "covered": [], "not_covered": []},
                "consistency_findings": [],
            }
        }
        if kind == "self_portrait"
        else {
            "criteria": {**common, "schema_version": "0.1", "stated": claims, "revealed": []},
            "ideal_profiles": {
                "schema_version": "0.1",
                "candidates": [],
                "caveats": ["Fictional only."],
            },
        }
    )
    source = reports / f"{kind}.json"
    source.write_bytes(_encode(canonical["report" if kind == "self_portrait" else "criteria"]))
    if kind == "mate_criteria":
        (reports / "ideal_partner_profiles.json").write_bytes(_encode(canonical["ideal_profiles"]))
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成译文{index}"}
        for index, (path, text) in enumerate(required_localization_sources(kind, canonical).items())
    ]
    (reports / f"{kind}_localization.json").write_bytes(
        _encode({"schema_version": "0.1", "localized_text": entries})
    )
    reviews = ReportReviewService(vault)
    document = reviews.inspect(kind)
    note = reviews.record_correction(
        kind,
        expected_digest=document.report_digest,
        target_path=document.claims[0].path,
        correction_text="PRIVATE_ANNOTATION_NOT_REPORT_TEXT",
        reason="Synthetic disagreement.",
        confirmed=True,
    )
    revisions = ReportRevisionService(vault)
    copy = revisions.save_withdrawals(
        revisions.preview_withdrawals(kind, [note.id], expected_digest=document.report_digest),
        confirmed=True,
    )
    return ActiveReportService(vault), source, copy


def _preview(service, kind="self_portrait", revision_id=None):
    return service.preview_selection(
        kind,
        revision_id,
        expected_selection_version=service.get_selection(kind).selection_version,
    )


def _journal(source, kind="self_portrait"):
    return source.parent / "active_selections" / kind


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_select_copy_restart_resolve_restore_no_original_writes(tmp_path, kind):
    service, source, copy = _seed(tmp_path, kind)
    originals = {path: path.read_bytes() for path in source.parent.rglob("*") if path.is_file()}
    assert service.resolve(kind) is None
    initial = service.get_selection(kind)
    assert initial.selection_version == "0" * 64 and initial.selected_at is None
    preview = _preview(service, kind, copy.id)
    assert not _journal(source, kind).exists()
    selected = service.select(preview, confirmed=True)
    resolved = ActiveReportService(source.parent.parent).resolve(kind)
    assert resolved.selection_version == selected.selection_version
    assert resolved.revision_id == copy.id
    assert resolved.markdown == preview.markdown
    assert resolved.content_digest == preview.target_bundle_digest
    assert "PRIVATE_ANNOTATION_NOT_REPORT_TEXT" not in str(resolved.model_dump())
    assert "source_file_digests" not in resolved.model_dump()
    key, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "stated")
    assert len(resolved.canonical[key][group]) == 1
    original = _preview(service, kind)
    returned = service.select(original, confirmed=True)
    assert returned.revision_id is None and returned.selected_at is not None
    resolved = service.resolve(kind)
    assert len(resolved.canonical[key][group]) == 2
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert len(list(_journal(source, kind).glob("*/selection.json"))) == 2


def test_pristine_missing_or_empty_vault_default_read_is_noncreating(tmp_path):
    for vault in (tmp_path, tmp_path / "absent" / "vault"):
        service = ActiveReportService(vault)
        assert service.resolve("self_portrait") is None
        assert service.get_selection("mate_criteria").selected_at is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("consent", [False, None, 0, 1, "true", [], {}])
def test_confirmation_is_strict_and_cancel_creates_no_journal(tmp_path, consent):
    service, source, copy = _seed(tmp_path)
    with pytest.raises(ActiveReportError):
        service.select(_preview(service, revision_id=copy.id), confirmed=consent)
    assert not _journal(source).exists()


@pytest.mark.parametrize("change", ["source", "locale", "ideal", "copy"])
def test_changes_after_preview_reject_without_selection(tmp_path, change):
    kind = "mate_criteria"
    service, source, copy = _seed(tmp_path, kind)
    preview = _preview(service, kind, copy.id)
    target = {
        "source": source,
        "locale": source.with_name(f"{kind}_localization.json"),
        "ideal": source.with_name("ideal_partner_profiles.json"),
        "copy": Path(copy.directory_path) / "report.md",
    }[change]
    target.write_bytes(target.read_bytes() + b" \n")
    with pytest.raises(ActiveReportError):
        service.select(preview, confirmed=True)
    assert not _journal(source, kind).exists()


@pytest.mark.parametrize("select_copy", [False, True])
def test_regeneration_invalidates_explicit_choice_requires_reselect(tmp_path, select_copy):
    service, source, copy = _seed(tmp_path)
    selected = service.select(
        _preview(service, revision_id=copy.id if select_copy else None), confirmed=True
    )
    source.write_bytes(source.read_bytes() + b" \n")
    with pytest.raises(ActiveReportError):
        service.resolve("self_portrait")
    assert service.get_selection("self_portrait") == selected
    with pytest.raises(ActiveReportError):
        _preview(service, revision_id=copy.id)
    service.select(_preview(service), confirmed=True)
    assert service.resolve("self_portrait").revision_id is None


def test_corrupt_copy_can_be_deselected_without_reading_it(tmp_path):
    service, source, copy = _seed(tmp_path)
    service.select(_preview(service, revision_id=copy.id), confirmed=True)
    (Path(copy.directory_path) / "manifest.json").write_bytes(b"private corrupt copy")
    with pytest.raises(ActiveReportError):
        service.resolve("self_portrait")
    service.select(_preview(service), confirmed=True)
    assert service.resolve("self_portrait").revision_id is None


@pytest.mark.parametrize(
    "field,value",
    [("markdown", "invented"), ("revision_id", None), ("target_bundle_digest", "f" * 64)],
)
def test_shallow_model_copy_tampered_preview_rejected(tmp_path, field, value):
    service, source, copy = _seed(tmp_path)
    preview = _preview(service, revision_id=copy.id)
    with pytest.raises(ActiveReportError):
        service.select(preview.model_copy(update={field: value}), confirmed=True)
    assert service.resolve("self_portrait") is None


def test_stale_selection_and_concurrent_same_preview_only_one_commits(tmp_path):
    service, source, copy = _seed(tmp_path)
    preview = _preview(service, revision_id=copy.id)

    def select(_):
        try:
            return ActiveReportService(source.parent.parent).select(preview, confirmed=True)
        except ActiveReportError:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(select, range(4)))
    assert sum(item is not None for item in results) == 1
    assert len(list(_journal(source).glob("*/selection.json"))) == 1
    assert service.resolve("self_portrait").revision_id == copy.id
    with pytest.raises(ActiveReportError):
        service.preview_selection("self_portrait", None, expected_selection_version="0" * 64)


@pytest.mark.parametrize("operation", ["checksum", "unknown_file", "chain", "sequence"])
def test_journal_corruption_fails_closed_even_restore(tmp_path, operation):
    service, source, copy = _seed(tmp_path)
    service.select(_preview(service, revision_id=copy.id), confirmed=True)
    path = next(_journal(source).glob("*/selection.json"))
    if operation == "unknown_file":
        (path.parent / "unexpected.txt").write_bytes(b"unknown")
    elif operation == "checksum":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        value = json.loads(path.read_bytes())
        value["previous_selection_version" if operation == "chain" else "sequence"] = (
            "a" * 64 if operation == "chain" else 2
        )
        value.pop("event_digest")
        value["event_digest"] = _hash(_encode(value))
        path.write_bytes(_encode(value))
    for action in (
        lambda: service.get_selection("self_portrait"),
        lambda: service.resolve("self_portrait"),
        lambda: service.preview_selection(
            "self_portrait", None, expected_selection_version="0" * 64
        ),
    ):
        with pytest.raises(ActiveReportError) as caught:
            action()
        assert str(source) not in str(caught.value)
    assert path.exists()


@pytest.mark.parametrize("change", ["source", "copy", "disk"])
def test_failure_during_staging_preserves_previous_selection(tmp_path, monkeypatch, change):
    service, source, copy = _seed(tmp_path)
    previous = service.select(_preview(service), confirmed=True)
    preview = _preview(service, revision_id=copy.id)
    write = ReportReviewService._write_new

    def interfere(io, path, raw):
        if change == "disk" and path.name == "selection.json":
            raise OSError("PRIVATE_OS_DIAGNOSTIC")
        result = write(io, path, raw)
        if path.name == "selection.json":
            target = source if change == "source" else Path(copy.directory_path) / "report.md"
            target.write_bytes(target.read_bytes() + b" ")
        return result

    monkeypatch.setattr(ReportReviewService, "_write_new", interfere)
    with pytest.raises(ActiveReportError) as caught:
        service.select(preview, confirmed=True)
    assert "PRIVATE_OS_DIAGNOSTIC" not in str(caught.value)
    assert service.get_selection("self_portrait") == previous
    assert len(list(_journal(source).glob("[!.]*/selection.json"))) == 1


def test_limit_reserves_last_return_to_generated_without_pruning(tmp_path, monkeypatch):
    service, source, copy = _seed(tmp_path)
    monkeypatch.setattr(module, "MAX_SELECTIONS", 2)
    service.select(_preview(service, revision_id=copy.id), confirmed=True)
    with pytest.raises(ActiveReportError):
        service.select(_preview(service, revision_id=copy.id), confirmed=True)
    service.select(_preview(service), confirmed=True)
    with pytest.raises(ActiveReportError):
        service.select(_preview(service), confirmed=True)
    assert len(list(_journal(source).glob("*/selection.json"))) == 2


def test_oversized_journal_and_hardlinked_event_fail_before_contents(tmp_path, monkeypatch):
    service, source, copy = _seed(tmp_path)
    service.select(_preview(service), confirmed=True)
    path = next(_journal(source).glob("*/selection.json"))
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_JOURNAL_BYTES", 1)
        with pytest.raises(ActiveReportError):
            service.resolve("self_portrait")
    os.link(path, tmp_path / "alias.json")
    with pytest.raises(ActiveReportError):
        service.get_selection("self_portrait")


@pytest.mark.parametrize("identifier", ["../escape", "absolute/path", "", True, "f" * 32])
def test_fixed_revision_identifier_and_missing_target(tmp_path, identifier):
    service, source, copy = _seed(tmp_path)
    with pytest.raises(ActiveReportError):
        _preview(service, revision_id=identifier)
    assert not _journal(source).exists()


def test_symlink_vault_or_journal_never_default_fallback(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("host cannot create symlinks")
    with pytest.raises(ActiveReportError):
        ActiveReportService(alias)


def test_legacy_default_preserved_but_explicit_selection_needs_valid_bundle(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "self_portrait.md").write_text("Legacy report", encoding="utf-8")
    service = ActiveReportService(tmp_path)
    assert service.resolve("self_portrait") is None
    with pytest.raises(ActiveReportError):
        _preview(service)


def test_network_not_used_by_selection(tmp_path, monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        pytest.fail("selection must make no network calls")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    service, source, copy = _seed(tmp_path)
    service.select(_preview(service, revision_id=copy.id), confirmed=True)
    assert service.resolve("self_portrait").revision_id == copy.id


def test_source_change_during_copy_verification_rejected(tmp_path, monkeypatch):
    service, source, copy = _seed(tmp_path)
    read = ReportRevisionService.read_verified_bundle

    def mutate(revisions, kind, identifier):
        bundle = read(revisions, kind, identifier)
        source.write_bytes(source.read_bytes() + b" ")
        return bundle

    monkeypatch.setattr(ReportRevisionService, "read_verified_bundle", mutate)
    with pytest.raises(ActiveReportError):
        _preview(service, revision_id=copy.id)
    assert not _journal(source).exists()


def test_inconsistent_preview_digest_rejected_even_with_recomputed_event_checksum(tmp_path):
    service, source, copy = _seed(tmp_path)
    service.select(_preview(service, revision_id=copy.id), confirmed=True)
    path = next(_journal(source).glob("*/selection.json"))
    value = json.loads(path.read_bytes())
    value["preview_digest"] = "a" * 64
    value.pop("event_digest")
    value["event_digest"] = _hash(_encode(value))
    path.write_bytes(_encode(value))
    with pytest.raises(ActiveReportError):
        service.resolve("self_portrait")


def test_verified_bundle_accessor_exposes_only_report_and_detached_source_hashes(tmp_path):
    service, source, copy = _seed(tmp_path)
    revisions = ReportRevisionService(source.parent.parent)
    bundle = revisions.read_verified_bundle("self_portrait", copy.id)
    assert set(bundle.model_dump()) == {
        "kind",
        "revision_id",
        "integrity_digest",
        "source_file_digests",
        "canonical",
        "localized_text",
        "markdown",
        "detailed_markdown",
    }
    assert "PRIVATE_ANNOTATION_NOT_REPORT_TEXT" not in str(bundle.model_dump())
    assert all(len(value) == 64 for value in bundle.source_file_digests.values())
    bundle.canonical["report"]["claims"].clear()
    assert (
        len(revisions.read_verified_bundle("self_portrait", copy.id).canonical["report"]["claims"])
        == 1
    )
