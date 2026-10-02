"""Synthetic, deterministic user-proposed reinterpretations, never fact promotion."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.report_review import ReportReviewService, _encode, _hash
from anti_dating_scam.services.report_revisions import (
    ReplacementPreview,
    ReplacementProposal,
    ReportRevisionError,
    ReportRevisionService,
)


def _fixture(tmp_path, kind="self_portrait", *, caveat_count=1, profile_caveat_count=1):
    vault = tmp_path / "vault"
    reports = vault / "reports"
    reports.mkdir(parents=True)
    claims = [
        {
            "topic": "communication",
            "claim": f"Synthetic original claim {index}.",
            "type": "observation",
            "confidence": "high",
            "evidence": [
                {"quote": f"Synthetic original quotation {index}.", "source": "../unread-label"}
            ],
        }
        for index in range(2)
    ]
    common = {
        "report_type": kind,
        "open_questions": ["What remains unclear?"],
        "caveats": [f"Original uncertainty {i}." for i in range(caveat_count)],
    }
    if kind == "self_portrait":
        canonical = {
            "report": {
                **common,
                "schema_version": "0.2",
                "claims": claims,
                "generated_at": "2026-09-28T00:00:00Z",
                "headline": {"en": "Original headline.", "zh": "原有标题"},
                "summary": {"en": "Original summary.", "zh": "原有摘要"},
                "data_coverage": {"sources_read": ["synthetic"], "covered": [], "not_covered": []},
                "consistency_findings": [
                    {
                        "kind": "temporal_drift",
                        "stated": "Earlier statement.",
                        "contradicting": "Later statement.",
                        "confidence": "low",
                        "framing": "Contexts might differ.",
                        "clarifying_question": "Did context change?",
                        "alt_benign_explanation": "Circumstances may differ.",
                        "quotes": [item["evidence"][0] for item in claims],
                    }
                ],
            }
        }
        group = "claims"
    else:
        canonical = {
            "criteria": {
                **common,
                "schema_version": "0.1",
                "stated": [],
                "revealed": claims,
            },
            "ideal_profiles": {
                "schema_version": "0.1",
                "candidates": [
                    {
                        "synthetic_id": "fictional-1",
                        "age": 30,
                        "fictional": True,
                        "description": "An explicitly fictional adult.",
                        "choice_reason": None,
                        "evidence": [],
                        "uncertainty_notes": "No real person described.",
                    }
                ],
                "caveats": [f"Fictional warning {i}." for i in range(profile_caveat_count)],
            },
        }
        group = "revealed"
    source = reports / f"{kind}.json"
    source.write_bytes(
        (
            json.dumps(canonical["report" if kind == "self_portrait" else "criteria"], indent=2)
            + "\r\n  "
        ).encode()
    )
    if kind == "mate_criteria":
        (reports / "ideal_partner_profiles.json").write_bytes(_encode(canonical["ideal_profiles"]))
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"原始合成译文{index}"}
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
        target_path=f"/{group}/1",
        correction_text="ANNOTATION_NOT_AUTOMATIC_FACT",
        reason="Synthetic disagreement.",
        confirmed=True,
    )
    proposal = ReplacementProposal(
        correction_id=note.id,
        text_en="This might reflect one situation, not a stable preference.",
        text_zh="这可能只是某个情境中的反应，并非稳定的偏好。",
    )
    return ReportRevisionService(vault), reviews, source, proposal, canonical


def _preview(service, reviews, proposal, kind="self_portrait"):
    return service.preview_replacement(
        kind, proposal, expected_digest=reviews.inspect(kind).report_digest
    )


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_replacement_exact_original_preservation_restart_and_mixed_history(tmp_path, kind):
    service, reviews, source, proposal, canonical = _fixture(tmp_path, kind)
    originals = {p: p.read_bytes() for p in source.parent.rglob("*") if p.is_file()}
    preview = _preview(service, reviews, proposal, kind)
    assert not (source.parent / "reviewed_copies").exists()
    assert isinstance(preview, ReplacementPreview)
    assert preview.correction_ids == [proposal.correction_id]
    assert "ANNOTATION_NOT_AUTOMATIC_FACT" not in preview.markdown
    assert "User-proposed interpretation (unverified):" in preview.markdown.replace("\\", "")
    assert "用户提出的解释（未经核实）" in preview.markdown
    assert preview.replacement_claim.type == "speculation"
    assert preview.replacement_claim.confidence == "low"
    for field in ("path", "topic", "evidence"):
        assert getattr(preview.replacement_claim, field) == getattr(
            preview.removed_claims[0], field
        )
    saved = service.save_replacement(preview, confirmed=True)
    folder = Path(saved.directory_path)
    assert (folder / "source_report.json").read_bytes() == originals[source]
    assert _encode(proposal.model_dump(mode="json")) == (folder / "proposal.json").read_bytes()
    assert all(p.read_bytes() == raw for p, raw in originals.items())
    manifest = json.loads((folder / "manifest.json").read_bytes())
    assert manifest["schema_version"] == "0.2" and manifest["operation"] == "replace_claim"
    bundle = service.read_verified_bundle(kind, saved.id)
    root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "revealed")
    report = bundle.canonical[root]
    assert report[group][0] == canonical[root][group][0]
    assert report["open_questions"] == canonical[root]["open_questions"]
    assert report["caveats"][:-1] == canonical[root]["caveats"]
    if kind == "self_portrait":
        assert not report["consistency_findings"]
        assert "headline" not in report and "summary" not in report
        assert report["generated_at"] == canonical[root]["generated_at"]
    else:
        assert not report["stated"] and not bundle.canonical["ideal_profiles"]["candidates"]
    # New and old copy formats can coexist and be verified without conversion.
    withdrawn = service.save_withdrawals(
        service.preview_withdrawals(
            kind, [proposal.correction_id], expected_digest=reviews.inspect(kind).report_digest
        ),
        confirmed=True,
    )
    old_bytes = {p.name: p.read_bytes() for p in Path(withdrawn.directory_path).iterdir()}
    assert json.loads(old_bytes["manifest.json"])["schema_version"] == "0.1"
    assert "proposal.json" not in old_bytes
    restarted = ReportRevisionService(source.parent.parent)
    assert len(restarted.list_revisions(kind)) == 2
    assert restarted.read_revision(kind, saved.id) == preview
    assert {p.name: p.read_bytes() for p in Path(withdrawn.directory_path).iterdir()} == old_bytes
    assert not (source.parent / "active_selections").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"text_en": ""},
        {"text_en": "   "},
        {"text_en": "中文而已"},
        {"text_zh": "English only"},
        {"text_zh": "中"},
        {"text_zh": ""},
        {"text_en": "Same 双语", "text_zh": "Same 双语"},
        {"text_en": "x" * 4001},
        {"text_zh": "文" * 4001},
        {"text_en": 123},
        {"correction_id": "../outside"},
    ],
)
def test_input_language_and_bounds_are_checked_before_fixed_prefixes(tmp_path, changes):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    malformed = proposal.model_copy(update=changes)
    with pytest.raises(ReportRevisionError) as caught:
        _preview(service, reviews, malformed)
    assert "Synthetic" not in str(caught.value)
    assert not (source.parent / "reviewed_copies").exists()


def test_language_boundaries_and_mixed_names_preserved_without_translation_call(tmp_path):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    proposal = proposal.model_copy(update={"text_en": "A中文" + "x" * 3997, "text_zh": "文" * 4000})
    preview = _preview(service, reviews, proposal)
    saved = service.save_replacement(preview, confirmed=True)
    assert service.read_revision("self_portrait", saved.id).proposal == proposal


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true"])
def test_explicit_consent_required_and_originals_untouched(tmp_path, confirmed):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    preview = _preview(service, reviews, proposal)
    original = source.read_bytes()
    with pytest.raises(ReportRevisionError):
        service.save_replacement(preview, confirmed=confirmed)
    assert source.read_bytes() == original
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("target_name", ["source", "locale", "ideal", "note"])
def test_exact_input_byte_change_invalidates_preview(tmp_path, target_name):
    kind = "mate_criteria"
    service, reviews, source, proposal, canonical = _fixture(tmp_path, kind)
    preview = _preview(service, reviews, proposal, kind)
    target = {
        "source": source,
        "locale": source.with_name(f"{kind}_localization.json"),
        "ideal": source.with_name("ideal_partner_profiles.json"),
        "note": reviews._history(kind) / proposal.correction_id / "correction.json",
    }[target_name]
    target.write_bytes(target.read_bytes() + b" \n")
    with pytest.raises(ReportRevisionError):
        service.save_replacement(preview, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize(
    "target_name", ["proposal.json", "report.md", "localization.json", "source_report.json"]
)
def test_tampered_saved_snapshot_rejected_without_echoing_contents(tmp_path, target_name):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    saved = service.save_replacement(_preview(service, reviews, proposal), confirmed=True)
    target = Path(saved.directory_path) / target_name
    target.write_bytes(target.read_bytes() + b"PRIVATE_TAMPER")
    with pytest.raises(ReportRevisionError) as caught:
        service.read_revision("self_portrait", saved.id)
    assert "PRIVATE_TAMPER" not in str(caught.value)
    with pytest.raises(ReportRevisionError):
        service.list_revisions("self_portrait")


def test_recomputed_file_checksums_cannot_hide_proposal_derivation_mismatch(tmp_path):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    saved = service.save_replacement(_preview(service, reviews, proposal), confirmed=True)
    folder = Path(saved.directory_path)
    data = json.loads((folder / "proposal.json").read_bytes())
    data["text_en"] = "A different interpretation."
    raw = _encode(data)
    (folder / "proposal.json").write_bytes(raw)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    manifest["files"]["proposal.json"] = _hash(raw)
    manifest.pop("manifest_digest")
    manifest["manifest_digest"] = _hash(_encode(manifest))
    (folder / "manifest.json").write_bytes(_encode(manifest))
    with pytest.raises(ReportRevisionError):
        service.read_verified_bundle("self_portrait", saved.id)


def test_withdrawal_and_replacement_preview_types_not_interchangeable(tmp_path):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    replacement = _preview(service, reviews, proposal)
    withdrawal = service.preview_withdrawals(
        "self_portrait",
        [proposal.correction_id],
        expected_digest=reviews.inspect("self_portrait").report_digest,
    )
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(replacement, confirmed=True)
    with pytest.raises(ReportRevisionError):
        service.save_replacement(withdrawal, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize(
    "kind,main_count,profile_count",
    [
        ("self_portrait", 30, 1),
        ("mate_criteria", 30, 1),
        ("mate_criteria", 1, 30),
    ],
)
def test_full_original_caveats_reject_instead_of_dropping_warning(
    tmp_path, kind, main_count, profile_count
):
    service, reviews, source, proposal, canonical = _fixture(
        tmp_path, kind, caveat_count=main_count, profile_caveat_count=profile_count
    )
    raw = source.read_bytes()
    with pytest.raises(ReportRevisionError):
        _preview(service, reviews, proposal, kind)
    assert source.read_bytes() == raw


@pytest.mark.parametrize("failure", ["write", "source", "note"])
def test_staging_failure_preserves_original_and_prior_valid_copy(tmp_path, monkeypatch, failure):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    preview = _preview(service, reviews, proposal)
    prior = service.save_replacement(preview, confirmed=True)
    write = service._review._write_new

    def interfere(path, raw):
        if failure == "write" and path.name == "proposal.json":
            raise OSError("PRIVATE_DISK_ERROR")
        result = write(path, raw)
        if failure != "write" and path.name == "manifest.json":
            target = (
                source
                if failure == "source"
                else reviews._history("self_portrait") / proposal.correction_id / "correction.json"
            )
            target.write_bytes(target.read_bytes() + b" ")
        return result

    monkeypatch.setattr(service._review, "_write_new", interfere)
    with pytest.raises(ReportRevisionError) as caught:
        service.save_replacement(preview, confirmed=True)
    assert "PRIVATE_DISK_ERROR" not in str(caught.value)
    assert service.list_revisions("self_portrait") == [prior]
    assert service.read_revision("self_portrait", prior.id) == preview


def test_concurrent_replacements_commit_unique_complete_copies(tmp_path):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    preview = _preview(service, reviews, proposal)

    def save(_):
        return ReportRevisionService(source.parent.parent).save_replacement(preview, confirmed=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        saved = list(pool.map(save, range(4)))
    assert len({item.id for item in saved}) == 4
    assert len(service.list_revisions("self_portrait")) == 4
    assert all(service.read_revision("self_portrait", item.id) == preview for item in saved)


def test_hardlinked_proposal_snapshot_rejected(tmp_path):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    saved = service.save_replacement(_preview(service, reviews, proposal), confirmed=True)
    os.link(Path(saved.directory_path) / "proposal.json", tmp_path / "alias.json")
    with pytest.raises(ReportRevisionError):
        service.read_revision("self_portrait", saved.id)


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": "0.1"},
        {"schema_version": "0.3"},
        {"operation": "withdraw_claim"},
    ],
)
def test_manifest_version_operation_mismatch_rejected_after_checksum_repair(tmp_path, changes):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    saved = service.save_replacement(_preview(service, reviews, proposal), confirmed=True)
    target = Path(saved.directory_path) / "manifest.json"
    value = json.loads(target.read_bytes())
    value.update(changes)
    value.pop("manifest_digest")
    value["manifest_digest"] = _hash(_encode(value))
    target.write_bytes(_encode(value))
    with pytest.raises(ReportRevisionError):
        service.read_revision("self_portrait", saved.id)


def test_swapped_valid_proposal_and_correction_do_not_retarget_saved_claim(tmp_path):
    service, reviews, source, proposal, canonical = _fixture(tmp_path)
    other = reviews.record_correction(
        "self_portrait",
        expected_digest=reviews.inspect("self_portrait").report_digest,
        target_path="/claims/0",
        correction_text="Other synthetic correction.",
        reason="A different target.",
        confirmed=True,
    )
    saved = service.save_replacement(_preview(service, reviews, proposal), confirmed=True)
    folder = Path(saved.directory_path)
    changed = proposal.model_copy(update={"correction_id": other.id})
    (folder / "proposal.json").write_bytes(_encode(changed.model_dump(mode="json")))
    old_name = f"correction-{proposal.correction_id}.json"
    new_name = f"correction-{other.id}.json"
    (folder / old_name).rename(folder / new_name)
    (folder / new_name).write_bytes(
        (reviews._history("self_portrait") / other.id / "correction.json").read_bytes()
    )
    manifest = json.loads((folder / "manifest.json").read_bytes())
    manifest["files"].pop(old_name)
    for name in ("proposal.json", new_name):
        manifest["files"][name] = _hash((folder / name).read_bytes())
    manifest.pop("manifest_digest")
    manifest["manifest_digest"] = _hash(_encode(manifest))
    (folder / "manifest.json").write_bytes(_encode(manifest))
    with pytest.raises(ReportRevisionError):
        service.read_verified_bundle("self_portrait", saved.id)
