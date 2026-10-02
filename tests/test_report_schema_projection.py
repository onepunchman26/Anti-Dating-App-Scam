"""Conservative generation bounds must not weaken or shrink artifact acceptance."""

import copy
import json
from pathlib import Path

import pytest
from test_full_report_regeneration import _EXCERPT, _bundle, _fixture, _localize, _paired

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.reports.artifact_bundles import (
    CriteriaBundle,
    PortraitBundle,
    bundle_schema,
    parse_bundle,
)
from anti_dating_scam.reports.local_artifacts import ArtifactValidationError
from anti_dating_scam.reports.paired_bundles import paired_bundle_schema
from anti_dating_scam.services.report_full_regeneration import FullReportRegenerationError
from anti_dating_scam.services.report_review import _encode, _hash
from anti_dating_scam.services.report_revisions import ReportRevisionService


def _compare_contract(projected, original, definitions, counts):
    if isinstance(original, dict):
        if "$ref" in original:
            original = definitions[original["$ref"].rsplit("/", 1)[-1]]
        expected_keys = set(original) - {"$defs"}
        if original.get("pattern") == r"\S":
            expected_keys.remove("pattern")  # Existing grammar projection, still parsed strictly.
        assert set(projected) == expected_keys
        for key in expected_keys:
            if key == "maxLength" and original.get("type") == "string":
                assert 0 < projected[key] <= original[key]
                assert projected[key] <= 1000  # Safely below older 2000-repetition boundaries.
                if original[key] > 1000:
                    counts.append(original[key])
            else:
                _compare_contract(projected[key], original[key], definitions, counts)
    elif isinstance(original, list):
        assert len(projected) == len(original)
        for value, source in zip(projected, original, strict=True):
            _compare_contract(value, source, definitions, counts)
    else:
        assert projected == original


@pytest.mark.parametrize(
    "kind,model",
    [
        ("self_portrait", PortraitBundle),
        ("mate_criteria", CriteriaBundle),
    ],
)
def test_only_generation_string_maxima_tighten_and_full_schema_stays_unchanged(kind, model):
    original = model.model_json_schema()
    before = copy.deepcopy(original)
    counts = []
    _compare_contract(bundle_schema(kind), original, original.get("$defs", {}), counts)
    assert counts and set(counts) == {8000}
    assert original == before and model.model_json_schema() == before


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_valid_longer_reply_still_parses_saves_and_reopens_without_truncation(tmp_path, kind):
    service, prepared, _, source, _ = _fixture(tmp_path, kind)
    bundle = _bundle(kind)
    canonical = {key: value for key, value in bundle.items() if key != "localized_text"}
    root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "stated")
    long_text = "A provisional interpretation with limited evidence. " * 65
    assert 2000 < len(long_text) < 8000
    canonical[root][group][0]["claim"] = long_text
    bundle = _localize(kind, canonical)
    assert parse_bundle(json.dumps(bundle), kind)[root][group][0]["claim"] == long_text
    originals = {path: path.read_bytes() for path in source.parent.rglob("*") if path.is_file()}
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        # An injected runtime may ignore the tighter generation projection.
        # Original acceptance and evidence limits still apply to its full reply.
        return {"message": {"content": json.dumps(_paired(bundle))}}

    proposal = service.generate(
        prepared,
        OllamaChatBackend(
            model="synthetic-long-reply",
            transport=transport,
        ),
        confirmed=True,
    )
    assert len(calls) == 1 and prepared.excerpts[0].text == _EXCERPT
    assert proposal.bundle[root][group][0]["claim"] == long_text
    revisions = ReportRevisionService(source.parent.parent)
    preview = revisions.preview_full_regeneration(
        kind,
        proposal,
        expected_digest=prepared.source_digest,
    )
    saved = revisions.save_full_regeneration(preview, confirmed=True)
    snapshot = {
        path: path.read_bytes() for path in Path(saved.directory_path).iterdir() if path.is_file()
    }
    restarted = ReportRevisionService(source.parent.parent)
    restored = restarted.read_revision(kind, saved.id)
    assert restored == preview
    assert restored.proposal.bundle[root][group][0]["claim"] == long_text
    assert all(path.read_bytes() == raw for path, raw in snapshot.items())
    assert all(path.read_bytes() == raw for path, raw in originals.items())


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_original_acceptance_limit_and_nonblank_checks_are_not_removed(kind):
    for claim_text in ("a" * 8001, " " * 20):
        bundle = _bundle(kind)
        root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "stated")
        # Copy the supplied localization directly: invalid canonical text should
        # fail its original type/length/nonblank checks before mapping acceptance.
        bundle[root][group][0]["claim"] = claim_text
        with pytest.raises(ArtifactValidationError):
            parse_bundle(json.dumps(bundle), kind)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_projection_is_exactly_reviewed_and_old_bounds_cannot_reuse_approval(tmp_path, kind):
    service, prepared, _, _, _ = _fixture(tmp_path, kind)
    schema = prepared.request.response_schema
    assert schema == paired_bundle_schema(kind)
    assert prepared.request.allow_schema_fallback is False
    assert prepared.request_digest == _hash(_encode(prepared.request.model_dump(warnings=False)))
    old_request = prepared.request.model_copy(deep=True)
    root, group = ("report", "claims") if kind == "self_portrait" else ("criteria", "stated")
    old_request.response_schema["properties"][root]["properties"][group]["items"]["properties"][
        "claim"
    ]["properties"]["en"]["maxLength"] = 8000
    changed = prepared.model_copy(update={"request": old_request})
    assert changed.request_digest != prepared.request_digest
    calls = []

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        return {"message": {"content": json.dumps(_paired(_bundle(kind)))}}

    with pytest.raises(FullReportRegenerationError):
        service.generate(
            changed,
            OllamaChatBackend(
                model="synthetic-stale-schema",
                transport=transport,
            ),
            confirmed=True,
        )
    assert not calls
