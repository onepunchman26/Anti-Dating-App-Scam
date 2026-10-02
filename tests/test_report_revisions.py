import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services import report_revisions as module
from anti_dating_scam.services.report_review import ReportReviewService, _encode, _hash
from anti_dating_scam.services.report_revisions import ReportRevisionError, ReportRevisionService


def _claim(index):
    return {
        "topic": "values",
        "claim": f"Synthetic claim {index}.",
        "type": "inference",
        "confidence": "low",
        "evidence": [{"quote": f"Synthetic note {index}.", "source": "../never-read-this"}],
    }


def _fixture(tmp_path, kind="self_portrait"):
    vault = tmp_path / "vault"
    reports = vault / "reports"
    reports.mkdir(parents=True)
    if kind == "self_portrait":
        canonical = {
            "report": {
                "schema_version": "0.2",
                "report_type": kind,
                "generated_at": "2026-09-28T00:00:00Z",
                "data_coverage": {"sources_read": ["synthetic"], "covered": [], "not_covered": []},
                "claims": [_claim(0), _claim(1)],
                "consistency_findings": [],
                "open_questions": [],
                "caveats": ["Synthetic and uncertain."],
            }
        }
    else:
        canonical = {
            "criteria": {
                "schema_version": "0.1",
                "report_type": kind,
                "stated": [_claim(0), _claim(1)],
                "revealed": [_claim(2)],
                "open_questions": [],
                "caveats": ["Synthetic and uncertain."],
            },
            "ideal_profiles": {
                "schema_version": "0.1",
                "candidates": [
                    {
                        "synthetic_id": "fictional-1",
                        "age": 30,
                        "fictional": True,
                        "description": "A fictional adult.",
                        "choice_reason": None,
                        "evidence": [],
                        "uncertainty_notes": "No real person is described.",
                    }
                ],
                "caveats": ["Fictional only."],
            },
        }
    source = reports / f"{kind}.json"
    source.write_bytes(
        (
            json.dumps(canonical.get("report", canonical.get("criteria")), indent=3) + "\r\n "
        ).encode()
    )
    if kind == "mate_criteria":
        (reports / "ideal_partner_profiles.json").write_bytes(_encode(canonical["ideal_profiles"]))
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成译文{index}"}
        for index, (path, text) in enumerate(required_localization_sources(kind, canonical).items())
    ]
    (reports / f"{kind}_localization.json").write_bytes(
        _encode(
            {
                "schema_version": "0.1",
                "localized_text": entries,
            }
        )
    )
    reviews = ReportReviewService(vault)
    document = reviews.inspect(kind)
    records = []
    for claim in document.claims[:2]:
        records.append(
            reviews.record_correction(
                kind,
                expected_digest=document.report_digest,
                target_path=claim.path,
                correction_text="ANNOTATION_NOT_A_NEW_FACT",
                reason="Synthetic disagreement.",
                confirmed=True,
            )
        )
    return ReportRevisionService(vault), reviews, source, records


def _preview(service, reviews, records, kind="self_portrait"):
    return service.preview_withdrawals(
        kind, [records[0].id], expected_digest=reviews.inspect(kind).report_digest
    )


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_preview_readonly_save_restart_exact_sources_and_no_fact_promotion(tmp_path, kind):
    service, reviews, source, records = _fixture(tmp_path, kind)
    originals = {path: path.read_bytes() for path in source.parent.rglob("*") if path.is_file()}
    preview = _preview(service, reviews, records, kind)
    assert not (source.parent / "reviewed_copies").exists()
    assert "ANNOTATION_NOT_A_NEW_FACT" not in preview.markdown
    assert (
        "未进行新的分析" in preview.markdown
        if kind == "mate_criteria"
        else "未经重新分析" in preview.markdown
    )
    saved = service.save_withdrawals(preview, confirmed=True)
    folder = Path(saved.directory_path)
    assert (folder / "source_report.json").read_bytes() == originals[source]
    assert (folder / "source_localization.json").read_bytes() == originals[
        source.with_name(kind + "_localization.json")
    ]
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    revised = json.loads((folder / "report.json").read_bytes())
    group = "claims" if kind == "self_portrait" else "stated"
    assert revised[group] == [_claim(1)]
    assert "ANNOTATION_NOT_A_NEW_FACT" not in json.dumps(revised)
    if kind == "self_portrait":
        assert revised["generated_at"] == "2026-09-28T00:00:00Z"
        assert saved.created_at != revised["generated_at"]
    else:
        assert json.loads((folder / "ideal_profiles.json").read_bytes())["candidates"] == []
    # Verified historical copies do not depend on current source or mutable annotation files.
    source.write_bytes(b"new malformed source")
    source.with_name(kind + "_localization.json").write_bytes(b"new locale")
    restarted = ReportRevisionService(source.parent.parent)
    assert restarted.list_revisions(kind) == [saved]
    assert restarted.read_revision(kind, saved.id) == preview


@pytest.mark.parametrize("consent", [False, None, 1, 0, "true", [], {}])
def test_strict_confirmation_creates_nothing(tmp_path, consent):
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(preview, confirmed=consent)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("change", ["source", "note", "ideal"])
def test_exact_changed_inputs_rejected_before_writes(tmp_path, change):
    kind = "mate_criteria"
    service, reviews, source, records = _fixture(tmp_path, kind)
    preview = _preview(service, reviews, records, kind)
    if change == "source":
        changed = source
    elif change == "ideal":
        changed = source.parent / "ideal_partner_profiles.json"
    else:
        changed = reviews._history(kind) / records[0].id / "correction.json"
    changed.write_bytes(changed.read_bytes() + b" \n")
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(preview, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("ids", [[], ["../escape"], ["f" * 32], [True], "bad"])
def test_invalid_selection_no_writes(tmp_path, ids):
    service, reviews, source, records = _fixture(tmp_path)
    with pytest.raises(ReportRevisionError):
        service.preview_withdrawals(
            "self_portrait", ids, expected_digest=reviews.inspect("self_portrait").report_digest
        )
    assert not (source.parent / "reviewed_copies").exists()


def test_duplicate_ids_rejected_but_distinct_notes_same_target_coalesce(tmp_path):
    service, reviews, source, records = _fixture(tmp_path)
    digest = reviews.inspect("self_portrait").report_digest
    with pytest.raises(ReportRevisionError):
        service.preview_withdrawals("self_portrait", [records[0].id] * 2, expected_digest=digest)
    second = reviews.record_correction(
        "self_portrait",
        expected_digest=digest,
        target_path="/claims/0",
        correction_text="Second independent annotation.",
        reason="Synthetic.",
        confirmed=True,
    )
    preview = service.preview_withdrawals(
        "self_portrait", [second.id, records[0].id], expected_digest=digest
    )
    assert len(preview.correction_ids) == 2
    assert len(preview.removed_claims) == 1
    service.save_withdrawals(preview, confirmed=True)


@pytest.mark.parametrize("bad", [b"not JSON", b'{"schema_version":"legacy"}', b"{}"])
def test_malformed_original_preserved(tmp_path, bad):
    service, reviews, source, records = _fixture(tmp_path)
    digest = reviews.inspect("self_portrait").report_digest
    source.write_bytes(bad)
    with pytest.raises(ReportRevisionError):
        service.preview_withdrawals("self_portrait", [records[0].id], expected_digest=digest)
    assert source.read_bytes() == bad
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize(
    "filename", ["report.md", "report.json", "source_report.json", "preview.json", "manifest.json"]
)
def test_saved_corruption_fails_closed_list_and_read(tmp_path, filename):
    service, reviews, source, records = _fixture(tmp_path)
    saved = service.save_withdrawals(_preview(service, reviews, records), confirmed=True)
    file = Path(saved.directory_path) / filename
    file.write_bytes(file.read_bytes() + b"tamper")
    for action in (
        lambda: service.list_revisions("self_portrait"),
        lambda: service.read_revision("self_portrait", saved.id),
    ):
        with pytest.raises(ReportRevisionError) as caught:
            action()
        assert "tamper" not in str(caught.value)
        assert str(source) not in str(caught.value)


def test_recomputed_checksums_cannot_hide_modified_derived_output(tmp_path):
    service, reviews, source, records = _fixture(tmp_path)
    saved = service.save_withdrawals(_preview(service, reviews, records), confirmed=True)
    folder = Path(saved.directory_path)
    (folder / "report.md").write_bytes(b"invented fact")
    manifest = json.loads((folder / "manifest.json").read_bytes())
    manifest["files"]["report.md"] = _hash(b"invented fact")
    manifest.pop("manifest_digest")
    manifest["manifest_digest"] = _hash(_encode(manifest))
    (folder / "manifest.json").write_bytes(_encode(manifest))
    with pytest.raises(ReportRevisionError):
        service.read_revision("self_portrait", saved.id)


def test_disk_failure_preserves_originals_and_prior_copy(tmp_path, monkeypatch):
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)
    first = service.save_withdrawals(preview, confirmed=True)
    original = source.read_bytes()
    write = service._review._write_new
    count = 0

    def fail_later(path, raw):
        nonlocal count
        count += 1
        if count == 3:
            raise OSError("private disk detail")
        return write(path, raw)

    monkeypatch.setattr(service._review, "_write_new", fail_later)
    with pytest.raises(ReportRevisionError) as caught:
        service.save_withdrawals(preview, confirmed=True)
    assert "private disk detail" not in str(caught.value)
    assert source.read_bytes() == original
    assert service.list_revisions("self_portrait") == [first]
    assert service.read_revision("self_portrait", first.id) == preview


@pytest.mark.parametrize("changed_input", ["source", "note"])
def test_source_changes_during_stage_never_commits(tmp_path, monkeypatch, changed_input):
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)
    write = service._review._write_new

    def change_source(path, raw):
        result = write(path, raw)
        if path.name == "manifest.json":
            target = (
                source
                if changed_input == "source"
                else (reviews._history("self_portrait") / records[0].id / "correction.json")
            )
            target.write_bytes(target.read_bytes() + b" ")
        return result

    monkeypatch.setattr(service._review, "_write_new", change_source)
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(preview, confirmed=True)
    assert service.list_revisions("self_portrait") == []


def test_concurrent_saves_have_complete_unique_transactions(tmp_path):
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)

    def save(_):
        return ReportRevisionService(source.parent.parent).save_withdrawals(preview, confirmed=True)

    with ThreadPoolExecutor(max_workers=4) as workers:
        saved = list(workers.map(save, range(8)))
    assert len({item.id for item in saved}) == 8
    assert len(service.list_revisions("self_portrait")) == 8
    assert all(service.read_revision("self_portrait", item.id) == preview for item in saved)


@pytest.mark.parametrize("target", ["../escape", "/absolute", "", "f" * 32])
def test_reader_fixed_id_rejects_path_tricks(tmp_path, target):
    service, reviews, source, records = _fixture(tmp_path)
    with pytest.raises(ReportRevisionError):
        service.read_revision("self_portrait", target)


def test_hardlinked_source_and_saved_file_rejected(tmp_path):
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)
    saved = service.save_withdrawals(preview, confirmed=True)
    os.link(Path(saved.directory_path) / "report.md", tmp_path / "alias.md")
    with pytest.raises(ReportRevisionError):
        service.read_revision("self_portrait", saved.id)
    os.link(source, tmp_path / "alias.json")
    with pytest.raises(ReportRevisionError):
        service.preview_withdrawals(
            "self_portrait", [records[0].id], expected_digest=preview.source_digest
        )


def test_empty_vault_listing_does_not_create_dirs(tmp_path):
    service = ReportRevisionService(tmp_path)
    assert service.list_revisions("self_portrait") == []
    assert list(tmp_path.iterdir()) == []


def test_limits_checked_before_new_transaction(tmp_path, monkeypatch):
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)
    first = service.save_withdrawals(preview, confirmed=True)
    monkeypatch.setattr(module, "MAX_REVISIONS", 1)
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(preview, confirmed=True)
    assert service.list_revisions("self_portrait") == [first]


def test_wrong_kind_or_oversized_source_safe(tmp_path):
    service, reviews, source, records = _fixture(tmp_path)
    with pytest.raises(ReportRevisionError):
        service.list_revisions("../outside")
    source.write_bytes(b"x" * (module.MAX_ARTIFACT_BYTES + 1))
    with pytest.raises(ReportRevisionError):
        service.preview_withdrawals("self_portrait", [records[0].id], expected_digest="0" * 64)


def test_no_provider_imports_or_network_needed(tmp_path, monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        pytest.fail("No outbound request is allowed")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    service, reviews, source, records = _fixture(tmp_path)
    preview = _preview(service, reviews, records)
    service.save_withdrawals(preview, confirmed=True)
    assert len(service.list_revisions("self_portrait")) == 1
