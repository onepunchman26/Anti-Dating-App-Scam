"""Independent synthetic acceptance tests for withdrawal-only report copies."""

import json

import pytest

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionError, ReportRevisionService


def _seed(vault, kind, *, same_claim=False, caveat_count=1, profile_caveat_count=1):
    texts = (
        ("The same synthetic claim.", "The same synthetic claim.")
        if same_claim else ("FIRST_SYNTHETIC_CLAIM", "SECOND_SYNTHETIC_CLAIM")
    )
    claims = [{
        "topic": "communication", "claim": text, "type": "inference", "confidence": "low",
        "evidence": [{"quote": f"Synthetic original quote {index}.", "source": "synthetic-note"}],
    } for index, text in enumerate(texts)]
    common = {
        "report_type": kind, "open_questions": [],
        "caveats": [f"Original uncertainty caveat {index}." for index in range(caveat_count)],
    }
    if kind == "self_portrait":
        canonical = {"report": {
            **common, "schema_version": "0.2", "claims": claims,
            "data_coverage": {"sources_read": ["synthetic-note"], "covered": [], "not_covered": []},
            "consistency_findings": [],
        }}
        source = canonical["report"]
        claim_prefix = "/report/claims"
    else:
        canonical = {
            "criteria": {**common, "schema_version": "0.1", "stated": claims, "revealed": []},
            "ideal_profiles": {
                "schema_version": "0.1", "candidates": [],
                "caveats": [
                    f"Synthetic scenario uncertainty {index}."
                    for index in range(profile_caveat_count)
                ],
            },
        }
        source = canonical["criteria"]
        claim_prefix = "/criteria/stated"
    reports = vault / "reports"
    reports.mkdir(parents=True)
    source_path = reports / f"{kind}.json"
    source_path.write_bytes((json.dumps(source, indent=3) + "\r\n").encode("utf-8"))
    if kind == "mate_criteria":
        (reports / "ideal_partner_profiles.json").write_bytes(
            (json.dumps(canonical["ideal_profiles"], indent=3) + "\r\n").encode("utf-8")
        )
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"原始不确定性译文第{index}项"}
        for index, (path, text) in enumerate(required_localization_sources(kind, canonical).items())
    ]
    translations = {
        f"{claim_prefix}/0/claim": "应该撤回的第一条独立译文",
        f"{claim_prefix}/1/claim": "应该保留的第二条独立译文",
    }
    for entry in entries:
        entry["zh"] = translations.get(entry["path"], entry["zh"])
    locale_path = reports / f"{kind}_localization.json"
    locale_path.write_bytes(json.dumps(
        {"schema_version": "0.1", "localized_text": entries}, ensure_ascii=False, indent=2,
    ).encode("utf-8"))
    reviews = ReportReviewService(vault)
    document = reviews.inspect(kind)
    records = [reviews.record_correction(
        kind, expected_digest=document.report_digest, target_path=claim.path,
        correction_text="REPLACEMENT_FACT_MUST_NOT_BE_INSERTED",
        reason="REASON_MUST_NOT_BECOME_REPORT_EVIDENCE", confirmed=True,
    ) for claim in document.claims]
    before = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    return ReportRevisionService(vault), records, document.report_digest, locale_path, before


def _assert_originals(before):
    assert all(path.read_bytes() == original for path, original in before.items())


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_identical_claim_text_keeps_its_own_pointer_translation_after_reindex(tmp_path, kind):
    service, records, digest, _locale, before = _seed(tmp_path, kind, same_claim=True)
    preview = service.preview_withdrawals(kind, [records[0].id], expected_digest=digest)
    text = preview.detailed_markdown or preview.markdown
    assert "应该保留的第二条独立译文" in text
    assert "应该撤回的第一条独立译文" not in text
    assert len(preview.removed_claims) == 1
    assert preview.removed_claims[0].path == records[0].target_path
    saved = service.save_withdrawals(preview, confirmed=True)
    reopened = service.read_revision(kind, saved.id)
    assert (reopened.detailed_markdown or reopened.markdown) == text
    _assert_originals(before)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_withdrawing_all_claims_saves_valid_copy_without_replacement_facts(tmp_path, kind):
    service, records, digest, _locale, before = _seed(tmp_path, kind)
    preview = service.preview_withdrawals(kind, [r.id for r in records], expected_digest=digest)
    assert {claim.path for claim in preview.removed_claims} == {r.target_path for r in records}
    text = preview.detailed_markdown or preview.markdown
    for marker in (
        "FIRST_SYNTHETIC_CLAIM", "SECOND_SYNTHETIC_CLAIM",
        "REPLACEMENT_FACT_MUST_NOT_BE_INSERTED", "REASON_MUST_NOT_BECOME_REPORT_EVIDENCE",
    ):
        assert marker not in text
    assert "Original uncertainty caveat 0" in text
    assert "English" in text and "中文版" in text
    saved = service.save_withdrawals(preview, confirmed=True)
    assert len(service.list_revisions(kind)) == 1
    reopened = service.read_revision(kind, saved.id)
    assert (reopened.detailed_markdown or reopened.markdown) == text
    _assert_originals(before)


@pytest.mark.parametrize("kind,target", [
    ("self_portrait", "report"), ("mate_criteria", "report"), ("mate_criteria", "profiles"),
])
def test_full_caveat_budget_rejects_instead_of_dropping_original_uncertainty(
    tmp_path, kind, target,
):
    service, records, digest, _locale, before = _seed(
        tmp_path, kind,
        caveat_count=30 if target == "report" else 1,
        profile_caveat_count=30 if target == "profiles" else 1,
    )
    with pytest.raises(ReportRevisionError):
        service.preview_withdrawals(kind, [records[0].id], expected_digest=digest)
    assert service.list_revisions(kind) == []
    assert not (tmp_path / "reports" / "reviewed_copies").exists()
    _assert_originals(before)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("field", ["markdown", "removed_claims"])
def test_shallow_preview_copy_cannot_change_confirmed_output_or_withdrawal_list(
    tmp_path, kind, field,
):
    service, records, digest, _locale, before = _seed(tmp_path, kind)
    preview = service.preview_withdrawals(kind, [records[0].id], expected_digest=digest)
    # Pydantic model_copy(update=...) deliberately bypasses field validation.
    tampered = preview.model_copy(update={
        field: "TAMPERED_PREVIEW_FACT" if field == "markdown" else [],
    })
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(tampered, confirmed=True)
    assert service.list_revisions(kind) == []
    assert not (tmp_path / "reports" / "reviewed_copies").exists()
    _assert_originals(before)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_whitespace_only_locale_change_requires_a_new_preview(tmp_path, kind):
    service, records, digest, locale, before = _seed(tmp_path, kind)
    preview = service.preview_withdrawals(kind, [records[0].id], expected_digest=digest)
    locale.write_bytes(locale.read_bytes() + b"\r\n  ")
    assert ReportReviewService(tmp_path).inspect(kind).report_digest == digest
    changed_locale = locale.read_bytes()
    with pytest.raises(ReportRevisionError):
        service.save_withdrawals(preview, confirmed=True)
    assert service.list_revisions(kind) == []
    assert not (tmp_path / "reports" / "reviewed_copies").exists()
    assert locale.read_bytes() == changed_locale
    _assert_originals({path: raw for path, raw in before.items() if path != locale})
    renewed = service.preview_withdrawals(kind, [records[0].id], expected_digest=digest)
    saved = service.save_withdrawals(renewed, confirmed=True)
    assert service.read_revision(kind, saved.id).markdown == renewed.markdown
