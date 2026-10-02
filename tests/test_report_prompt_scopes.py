"""Kind-specific report instructions and retained rejection of observed malformed replies."""

import copy
import json

import pytest
from test_full_report_regeneration import _bundle, _fixture, _paired

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.reports.artifact_bundles import bundle_prompt, bundle_schema, parse_bundle
from anti_dating_scam.reports.local_artifacts import ArtifactValidationError
from anti_dating_scam.reports.paired_bundles import paired_bundle_schema
from anti_dating_scam.services.report_full_regeneration import FullReportRegenerationError


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_shared_prompt_uses_only_requested_kind_paths_and_schema(kind):
    prompt = bundle_prompt(kind)
    marker = "Validation schema (instructions only, NEVER repeat this schema as your answer):\n"
    instruction, schema_and_tail = prompt.split(marker)
    encoded_schema, tail = schema_and_tail.split("\nNow produce a DOCUMENT INSTANCE", 1)
    assert json.loads(encoded_schema) == bundle_schema(kind)
    assert "source and en must both equal the canonical claim sentence" in instruction
    assert "NOT its evidence quote" in instruction
    assert "Each array item needs its own entry at its own index" in instruction
    assert "Never join several caveats or fields into one localization entry" in instruction
    assert "only USER-role input" in instruction
    assert "A preference or wish is not a requirement or prohibition" in instruction
    assert "no scores or diagnoses" in instruction
    if kind == "self_portrait":
        assert "/report/claims/0/claim" in instruction
        assert "consistency_findings is []" in instruction
        assert "ideal_profiles" not in prompt and "/criteria/" not in prompt
        assert "candidate" not in instruction and "choice_reason" not in instruction
        assert "exactly report, localized_text" in tail
    else:
        assert "/criteria/stated/0/claim" in instruction
        assert "/criteria/revealed/0/claim" in instruction
        assert "/ideal_profiles/caveats/0" in instruction
        assert "Never nest ideal_profiles inside criteria" in instruction
        assert "/report/" not in prompt
        assert "consistency_findings" not in prompt
        assert "data_coverage" not in prompt
        assert "exactly criteria, ideal_profiles, localized_text" in tail


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_full_request_scope_preserves_data_roles_modality_and_one_call_policy(tmp_path, kind):
    _, prepared, _, _, records = _fixture(tmp_path, kind)
    system = prepared.request.system
    assert "preference or wish is not a requirement, dealbreaker or" in system
    assert 'Do not turn "want" or "prefer" into "require" or "must"' in system
    assert "single episode cannot establish" in system
    assert "Use low confidence" in system
    assert "EXACT CONTIGUOUS substring" in system
    assert "never evidence or facts" in system
    assert "S001" in system and "S002" in system
    assert prepared.request.allow_schema_fallback is False
    assert prepared.request.privacy_mode == "local_only"
    assert prepared.request.response_schema == paired_bundle_schema(kind)
    assert "localized_text" not in prepared.request.response_schema["properties"]
    assert all(record.correction_text not in system for record in records)
    assert [message.role for message in prepared.request.messages] == ["assistant", "user"]
    if kind == "self_portrait":
        assert "report.data_coverage.sources_read" in system
        assert "ALL and ONLY submitted source IDs" in system
        assert "ideal_profiles" not in system and "/criteria/" not in system
        assert "candidate" not in system
    else:
        assert "ideal_profiles.candidates MUST be []" in system
        assert "no fictional-candidate" in system
        assert "consistency_findings" not in system and "sources_read" not in system


def _observed_defect(defect):
    """Isolate three defects observed together in a synthetic local portrait response."""
    bundle = _bundle("self_portrait")
    if defect in {"nested_candidates", "combined"}:
        bundle["report"]["ideal_profiles"] = {
            "candidates": [],
            "caveats": ["This workflow includes no candidate exercise."],
        }
    if defect in {"quote_as_localization_source", "combined"}:
        claim = bundle["report"]["claims"][0]
        entry = next(
            item for item in bundle["localized_text"] if item["path"] == "/report/claims/0/claim"
        )
        entry["source"] = claim["evidence"][0]["quote"]
        assert entry["source"] != claim["claim"]
    if defect in {"merged_caveats", "combined"}:
        bundle["report"]["caveats"].append("No external material was reviewed.")
        entry = next(
            item for item in bundle["localized_text"] if item["path"] == "/report/caveats/0"
        )
        entry["source"] = entry["en"] = "\n".join(bundle["report"]["caveats"])
        # The model incorrectly merged two canonical values into one /caveats/0 entry.
    return bundle


@pytest.mark.parametrize(
    "defect",
    [
        "nested_candidates",
        "quote_as_localization_source",
        "merged_caveats",
        "combined",
    ],
)
def test_observed_malformed_shapes_still_reject_without_repair_retry_or_writes(tmp_path, defect):
    service, prepared, _, source, _ = _fixture(tmp_path)
    original = {
        path: path.read_bytes() for path in source.parent.parent.rglob("*") if path.is_file()
    }
    bad_bundle = _observed_defect(defect)
    with pytest.raises(ArtifactValidationError):
        parse_bundle(json.dumps(bad_bundle), "self_portrait")
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append(copy.deepcopy(payload))
        return {"message": {"content": json.dumps(bad_bundle)}}

    backend = OllamaChatBackend(model="synthetic-invalid-replay", transport=transport)
    with pytest.raises(FullReportRegenerationError):
        service.generate(prepared, backend, confirmed=True)
    assert len(calls) == 1
    assert all(path.read_bytes() == raw for path, raw in original.items())
    assert not (source.parent / "reviewed_copies").exists()


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_valid_bundles_remain_accepted_with_exact_localization_and_low_confidence(tmp_path, kind):
    service, prepared, _, source, _ = _fixture(tmp_path, kind)
    bundle = _bundle(kind)
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        return {"message": {"content": json.dumps(_paired(bundle))}}

    result = service.generate(
        prepared,
        OllamaChatBackend(
            model="synthetic-valid-replay",
            transport=transport,
        ),
        confirmed=True,
    )
    assert len(calls) == 1
    report = result.bundle["report" if kind == "self_portrait" else "criteria"]
    assert report["claims" if kind == "self_portrait" else "stated"][0]["confidence"] == "low"
    assert {item["path"]: item for item in result.bundle["localized_text"]} == {
        item["path"]: item for item in bundle["localized_text"]
    }
    assert not (source.parent / "reviewed_copies").exists()
