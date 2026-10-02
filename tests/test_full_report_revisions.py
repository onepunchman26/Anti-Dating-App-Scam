"""Synthetic source-grounded regeneration copies; no model calls or private vaults."""

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_report_replacements import _fixture

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.report_full_regeneration_contract import (
    FullRegenerationProposal,
    RegenerationExcerpt,
    excerpt_sources,
    validate_full_bundle,
)
from anti_dating_scam.services.report_review import _encode
from anti_dating_scam.services.report_revisions import (
    AIReplacementProposal,
    FullRegenerationPreview,
    ReportRevisionError,
    ReportRevisionService,
)


def _localize(kind, canonical):
    return {
        **canonical,
        "localized_text": [
            {"path": path, "source": text, "en": text, "zh": f"新的合成译文{index}"}
            for index, (path, text) in enumerate(
                required_localization_sources(kind, canonical).items()
            )
        ],
    }


def _setup(tmp_path, kind="self_portrait", **kwargs):
    service, reviews, source, replacement, old = _fixture(tmp_path, kind, **kwargs)
    context = service.context_for_full_regeneration(
        kind, [replacement.correction_id], expected_digest=reviews.inspect(kind).report_digest
    )
    claim = {
        "topic": "communication", "claim": "One explicit preference is described.",
        "type": "observation", "confidence": "high",
        "evidence": [{"quote": "I prefer a short pause.", "source": "S001"}],
    }
    common = {"caveats": ["New input remains limited."], "open_questions": []}
    canonical = (
        {"report": {
            **common, "schema_version": "0.2", "report_type": kind,
            "claims": [claim], "consistency_findings": [],
            "data_coverage": {
                "sources_read": ["S001", "S002"], "covered": [], "not_covered": [],
            },
        }}
        if kind == "self_portrait" else
        {"criteria": {
            **common, "schema_version": "0.1", "report_type": kind,
            "stated": [claim], "revealed": [],
        }, "ideal_profiles": {
            "schema_version": "0.1", "candidates": [], "caveats": ["No exercise supplied."],
        }}
    )
    proposal = FullRegenerationProposal(
        correction_ids=[replacement.correction_id],
        excerpts=[
            RegenerationExcerpt(text="A fictional adult wrote: I prefer a short pause."),
            RegenerationExcerpt(text="A different fictional note states: I ask before calling."),
        ],
        bundle=_localize(kind, canonical), context_digest=context.context_digest,
        request_digest="a" * 64,
    )
    return service, reviews, source, proposal, old, context, replacement


def _preview(service, proposal, context):
    return service.preview_full_regeneration(
        context.kind, proposal, expected_digest=context.source_digest
    )


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_complete_copy_retains_originals_warnings_history_and_separate_activation(tmp_path, kind):
    service, _, source, proposal, old, context, _ = _setup(tmp_path, kind)
    before = {path: path.read_bytes() for path in source.parent.rglob("*") if path.is_file()}
    preview = _preview(service, proposal, context)
    assert isinstance(preview, FullRegenerationPreview)
    assert preview.operation == "regenerate_report"
    assert "AI-regenerated report" in preview.markdown.replace("\\", "")
    assert "AI 重新生成的报告" in preview.markdown
    assert "ANNOTATION_NOT_AUTOMATIC_FACT" not in preview.markdown
    assert "Synthetic original claim" not in preview.markdown
    saved = service.save_full_regeneration(preview, confirmed=True)
    folder = Path(saved.directory_path)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    assert manifest["schema_version"] == "0.4"
    assert manifest["operation"] == "regenerate_report"
    assert (folder / "regeneration.json").read_bytes() == _encode(proposal.model_dump(mode="json"))
    assert all(path.read_bytes() == value for path, value in before.items())
    assert not (source.parent / "active_selections").exists()
    fresh = ReportRevisionService(source.parent.parent)
    assert fresh.read_revision(kind, saved.id) == preview
    bundle = fresh.read_verified_bundle(kind, saved.id)
    root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "stated")
    assert bundle.canonical[root][group][0]["confidence"] == "low"
    assert bundle.canonical[root][group][0]["evidence"] == [
        {"quote": "I prefer a short pause.", "source": "S001"}
    ]
    assert bundle.canonical[root]["caveats"][1:-1] == old[root]["caveats"]
    old_translations = json.loads(before[source.with_name(f"{kind}_localization.json")])
    old_warning = next(
        item for item in old_translations["localized_text"] if item["path"] == f"/{root}/caveats/0"
    )
    new_warning = next(
        item for item in bundle.localized_text if item["path"] == f"/{root}/caveats/1"
    )
    assert {k: v for k, v in old_warning.items() if k != "path"} == {
        k: v for k, v in new_warning.items() if k != "path"
    }
    if kind == "mate_criteria":
        assert bundle.canonical["ideal_profiles"]["candidates"] == []
        assert (
            bundle.canonical["ideal_profiles"]["caveats"][1:-1]
            == old["ideal_profiles"]["caveats"]
        )
    active = ActiveReportService(source.parent.parent)
    selection = active.preview_selection(
        kind, saved.id, expected_selection_version=active.get_selection(kind).selection_version
    )
    active.select(selection, confirmed=True)
    assert active.resolve(kind).canonical == bundle.canonical
    source.write_bytes(b"new invalid source")
    assert fresh.read_revision(kind, saved.id) == preview
    with pytest.raises(ValueError):
        active.resolve(kind)


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true"])
def test_separate_strict_confirmation_is_required(tmp_path, confirmed):
    service, _, source, proposal, _, context, _ = _setup(tmp_path)
    with pytest.raises(ReportRevisionError):
        service.save_full_regeneration(_preview(service, proposal, context), confirmed=confirmed)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("quote,source", [
    ("I prefer a short pause.", "S002"),
    ("I prefer a short pause.", "../../private"),
    ("I prefer  a short pause.", "S001"),
    ("I prefer a short pause. I ask before calling.", "S001"),
    ("Synthetic original quotation 1.", "S001"),
    ("ANNOTATION_NOT_AUTOMATIC_FACT", "S001"),
])
def test_exact_source_identity_and_quote_boundaries_are_enforced(tmp_path, kind, quote, source):
    service, _, report, proposal, _, context, _ = _setup(tmp_path, kind)
    root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "stated")
    proposal.bundle[root][group][0]["evidence"] = [{"quote": quote, "source": source}]
    with pytest.raises(ReportRevisionError) as failure:
        _preview(service, proposal, context)
    assert quote not in str(failure.value)
    assert not (report.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("ids", [[], ["S001"], ["S002", "S001"], ["S001", "S001"], ["file.md"]])
def test_portrait_coverage_uses_exact_application_assigned_source_ids(tmp_path, ids):
    service, _, _, proposal, _, context, _ = _setup(tmp_path)
    proposal.bundle["report"]["data_coverage"]["sources_read"] = ids
    with pytest.raises(ReportRevisionError):
        _preview(service, proposal, context)


def test_fictional_profiles_cannot_be_invented_by_excerpt_regeneration(tmp_path):
    service, _, _, proposal, old, context, _ = _setup(tmp_path, "mate_criteria")
    canonical = {key: value for key, value in proposal.bundle.items() if key != "localized_text"}
    canonical["ideal_profiles"]["candidates"] = old["ideal_profiles"]["candidates"]
    proposal = proposal.model_copy(update={"bundle": _localize("mate_criteria", canonical)})
    with pytest.raises(ReportRevisionError):
        _preview(service, proposal, context)


@pytest.mark.parametrize("stage", ["preview", "save"])
@pytest.mark.parametrize("member", ["report", "localization", "profiles", "correction"])
def test_any_source_or_correction_byte_change_rejects_stale_result(tmp_path, stage, member):
    service, reviews, source, proposal, _, context, _ = _setup(tmp_path, "mate_criteria")
    preview = _preview(service, proposal, context)
    target = {
        "report": source,
        "localization": source.with_name("mate_criteria_localization.json"),
        "profiles": source.with_name("ideal_partner_profiles.json"),
        "correction": (
            reviews._history(context.kind) / proposal.correction_ids[0] / "correction.json"
        ),
    }[member]
    target.write_bytes(target.read_bytes() + b" \r\n")
    with pytest.raises(ReportRevisionError):
        if stage == "preview":
            _preview(service, proposal, context)
        else:
            service.save_full_regeneration(preview, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("field,value", [
    ("context_digest", "b" * 64), ("origin", "user"), ("request_digest", "invalid"),
    ("correction_ids", []), ("excerpts", []), ("bundle", {}),
])
def test_unvalidated_model_copies_cannot_bypass_contract(tmp_path, field, value):
    service, _, _, proposal, _, context, _ = _setup(tmp_path)
    with pytest.raises(ReportRevisionError):
        _preview(service, proposal.model_copy(update={field: value}), context)


@pytest.mark.parametrize("member", [
    "regeneration.json", "report.json", "localization.json", "report.md",
])
def test_saved_copy_tampering_is_rejected(tmp_path, member):
    service, _, _, proposal, _, context, _ = _setup(tmp_path)
    saved = service.save_full_regeneration(_preview(service, proposal, context), confirmed=True)
    target = Path(saved.directory_path) / member
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ReportRevisionError):
        service.read_revision(context.kind, saved.id)


@pytest.mark.parametrize("kind,kwargs", [
    ("self_portrait", {"caveat_count": 30}),
    ("mate_criteria", {"caveat_count": 30}),
    ("mate_criteria", {"profile_caveat_count": 30}),
])
def test_warning_capacity_rejects_instead_of_dropping_historical_warnings(tmp_path, kind, kwargs):
    service, _, _, proposal, _, context, _ = _setup(tmp_path, kind, **kwargs)
    with pytest.raises(ReportRevisionError):
        _preview(service, proposal, context)


def test_all_four_manifest_versions_coexist_and_reopen(tmp_path):
    service, _, _, proposal, _, context, replacement = _setup(tmp_path)
    withdrawal = service.preview_withdrawals(
        context.kind, proposal.correction_ids, expected_digest=context.source_digest
    )
    manual = service.preview_replacement(
        context.kind, replacement, expected_digest=context.source_digest
    )
    assisted = service.preview_ai_replacement(
        context.kind,
        AIReplacementProposal(
            **replacement.model_dump(), context_digest=context.context_digest,
            request_digest="b" * 64,
        ),
        expected_digest=context.source_digest,
    )
    full = _preview(service, proposal, context)
    saved = [
        service.save_withdrawals(withdrawal, confirmed=True),
        service.save_replacement(manual, confirmed=True),
        service.save_ai_replacement(assisted, confirmed=True),
        service.save_full_regeneration(full, confirmed=True),
    ]
    assert len(service.list_revisions(context.kind)) == 4
    pairs = zip(saved, [withdrawal, manual, assisted, full], strict=True)
    for index, (record, preview) in enumerate(pairs, 1):
        manifest = json.loads((Path(record.directory_path) / "manifest.json").read_bytes())
        assert manifest["schema_version"] == f"0.{index}"
        assert service.read_revision(context.kind, record.id) == preview


def test_failure_before_publish_leaves_originals_and_no_visible_copy(tmp_path, monkeypatch):
    service, _, source, proposal, _, context, _ = _setup(tmp_path)
    before = source.read_bytes()
    preview = _preview(service, proposal, context)
    original = service._review._write_new

    def fail(path, raw):
        if path.name == "regeneration.json":
            raise OSError("synthetic failure")
        return original(path, raw)

    monkeypatch.setattr(service._review, "_write_new", fail)
    with pytest.raises(ReportRevisionError):
        service.save_full_regeneration(preview, confirmed=True)
    assert source.read_bytes() == before
    assert service.list_revisions(context.kind) == []


@pytest.mark.parametrize("values", [[], ["x"] * 6, ["x" * 12000] * 3])
def test_excerpt_count_and_aggregate_bounds(values):
    with pytest.raises(ValueError):
        excerpt_sources([RegenerationExcerpt(text=text) for text in values])


@pytest.mark.parametrize("text", ["", " \r\n", "x" * 12001])
def test_each_excerpt_requires_bounded_literal_text(text):
    with pytest.raises(ValidationError):
        RegenerationExcerpt(text=text)


def test_validating_input_does_not_mutate_provider_bundle(tmp_path):
    _, _, _, proposal, _, context, _ = _setup(tmp_path)
    original = copy.deepcopy(proposal.bundle)
    checked = validate_full_bundle(context.kind, proposal.bundle, proposal.excerpts)
    assert checked["report"]["claims"][0]["confidence"] == "low"
    assert proposal.bundle == original


def test_zero_supported_claims_remains_honest_complete_report_with_caveats(tmp_path):
    service, _, _, proposal, _, context, _ = _setup(tmp_path)
    canonical = copy.deepcopy({
        key: value for key, value in proposal.bundle.items() if key != "localized_text"
    })
    canonical["report"]["claims"] = []
    proposal = proposal.model_copy(update={"bundle": _localize(context.kind, canonical)})
    preview = _preview(service, proposal, context)
    saved = service.save_full_regeneration(preview, confirmed=True)
    assert service.read_verified_bundle(context.kind, saved.id).canonical["report"]["claims"] == []


def test_full_proposals_cannot_be_saved_as_older_copy_operations(tmp_path):
    service, _, source, proposal, _, context, _ = _setup(tmp_path)
    preview = _preview(service, proposal, context)
    for method in [service.save_withdrawals, service.save_replacement, service.save_ai_replacement]:
        with pytest.raises(ReportRevisionError):
            method(preview, confirmed=True)
    assert not (source.parent / "reviewed_copies").exists()


def test_consistency_quotes_are_source_checked_and_confidence_remains_low(tmp_path):
    service, _, _, proposal, _, context, _ = _setup(tmp_path)
    canonical = copy.deepcopy({
        key: value for key, value in proposal.bundle.items() if key != "localized_text"
    })
    finding = {
        "kind": "temporal_drift", "stated": "One preference was stated.",
        "contradicting": "Another note concerns asking.", "confidence": "high",
        "framing": "The excerpts may address different situations.",
        "clarifying_question": "What was the surrounding context?",
        "alt_benign_explanation": "These statements may be compatible.",
        "quotes": [
            {"quote": "I prefer a short pause.", "source": "S001"},
            {"quote": "I ask before calling.", "source": "S002"},
        ],
    }
    canonical["report"]["consistency_findings"] = [finding]
    proposal = proposal.model_copy(update={"bundle": _localize(context.kind, canonical)})
    preview = _preview(service, proposal, context)
    saved = service.save_full_regeneration(preview, confirmed=True)
    checked = service.read_verified_bundle(context.kind, saved.id).canonical["report"]
    assert checked["consistency_findings"][0]["confidence"] == "low"
    proposal.bundle["report"]["consistency_findings"][0]["quotes"][1]["source"] = "S001"
    with pytest.raises(ReportRevisionError):
        _preview(service, proposal, context)


def test_four_versions_publish_concurrently_in_four_processes_and_fresh_read(tmp_path):
    from test_ai_report_revision_concurrency import _READER, _WRITER

    service, _, source, proposal, _, context, _ = _setup(tmp_path)
    vault = source.parent.parent
    control = tmp_path / "control"
    control.mkdir()
    (control / "proposal.json").write_bytes(_encode(proposal.model_dump(mode="json")))
    before = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    full_writer = '''
import json, sys, time
from pathlib import Path
from anti_dating_scam.services.report_full_regeneration_contract import FullRegenerationProposal
from anti_dating_scam.services.report_revisions import ReportRevisionService
vault, control = Path(sys.argv[1]), Path(sys.argv[3])
service = ReportRevisionService(vault)
raw = json.loads((control / 'proposal.json').read_bytes())
proposal = FullRegenerationProposal.model_validate(raw)
context = service.context_for_full_regeneration(
    'self_portrait', proposal.correction_ids, expected_digest=sys.argv[6])
preview = service.preview_full_regeneration(
    'self_portrait', proposal, expected_digest=context.source_digest)
(control / ('ready-' + sys.argv[4])).write_text('ready', encoding='ascii')
deadline = time.monotonic() + 20
while not (control / 'start').exists():
    if time.monotonic() > deadline:
        raise RuntimeError('Synthetic process barrier timed out.')
    time.sleep(0.01)
saved = service.save_full_regeneration(preview, confirmed=True)
print(json.dumps(dict(id=saved.id, operation='regenerate_report', digest=preview.preview_digest)))
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["ADS_NO_AUTOCONNECT"] = "1"
    options = {
        "cwd": tmp_path, "env": environment, "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8",
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }
    children = []
    try:
        for index, operation in enumerate((
            "withdraw_claim", "replace_claim", "ai_replace_claim", "regenerate_report",
        )):
            script = full_writer if operation == "regenerate_report" else _WRITER
            children.append(subprocess.Popen([
                sys.executable, "-c", script, str(vault), proposal.correction_ids[0],
                str(control), str(index), operation, context.source_digest,
            ], **options))
        deadline = time.monotonic() + 20
        while len(list(control.glob("ready-*"))) < 4:
            assert all(child.poll() is None for child in children)
            assert time.monotonic() < deadline
            time.sleep(0.01)
        (control / "start").write_text("start", encoding="ascii")
        results = [child.communicate(timeout=25) for child in children]
        assert all(child.returncode == 0 for child in children), results
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    written = [json.loads(stdout) for stdout, _ in results]
    assert len({row["id"] for row in written}) == 4
    folder = vault / "reports/reviewed_copies/self_portrait"
    assert not list(folder.glob(".pending-*"))
    assert {
        json.loads((folder / row["id"] / "manifest.json").read_bytes())["schema_version"]
        for row in written
    } == {"0.1", "0.2", "0.3", "0.4"}
    recovered = subprocess.run(
        [sys.executable, "-c", _READER, str(vault)], timeout=20, check=True, **options,
    )
    assert sorted(json.loads(recovered.stdout), key=lambda row: row["id"]) == sorted(
        written, key=lambda row: row["id"],
    )
    assert len(service.list_revisions(context.kind)) == 4
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert not (source.parent / "active_selections").exists()
