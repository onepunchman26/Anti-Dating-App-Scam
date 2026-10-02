"""Strict synthetic bilingual wire projections; no model, network or file access."""

import copy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError

from anti_dating_scam.reports.artifact_bundles import parse_bundle
from anti_dating_scam.reports.local_artifacts import (
    ArtifactValidationError,
    validate_local_artifact,
)
from anti_dating_scam.reports.localized_reports import (
    required_localization_sources,
    validate_localization,
)
from anti_dating_scam.reports.paired_bundles import (
    paired_bundle_prompt,
    paired_bundle_schema,
    project_paired_bundle,
)

_KINDS = ["self_portrait", "mate_criteria"]


def _pair(text):
    return {"en": text, "zh": f"合成译文：{text}。"}


def _claim(text="One episode only."):
    return {
        "topic": "communication", "type": "speculation", "confidence": "low",
        "claim": _pair(text),
        "evidence": [{"quote": "  Synthetic original.\r\n", "source": "S001"}],
    }


def _wire(kind):
    if kind == "mate_criteria":
        return {
            "criteria": {
                "schema_version": "0.1", "report_type": kind,
                "stated": [_claim("A stated wish.")],
                "revealed": [_claim("A tentative preference.")],
                "open_questions": [_pair("What remains unclear?")],
                "caveats": [_pair("A limited account."), _pair("No broad pattern established.")],
            },
            "ideal_profiles": {
                "schema_version": "0.1", "candidates": [],
                "caveats": [_pair("No candidate exercise."), _pair("No choices inferred.")],
            },
        }
    return {
        "report": {
            "schema_version": "0.2", "report_type": kind,
            "data_coverage": {
                "sources_read": ["S001", "S002"],
                "covered": [_pair("Two synthetic accounts.")],
                "not_covered": [_pair("Other occasions."), _pair("Source authenticity.")],
            },
            "claims": [_claim()],
            "consistency_findings": [{
                "kind": "temporal_drift", "confidence": "low",
                "stated": _pair("An earlier statement."),
                "contradicting": _pair("A later difference."),
                "quotes": [
                    {"quote": "Earlier synthetic wording.", "source": "S001"},
                    {"quote": "Later synthetic wording.", "source": "S002"},
                ],
                "framing": _pair("A possible difference to clarify."),
                "clarifying_question": _pair("Did the circumstances change?"),
                "alt_benign_explanation": _pair("Context might differ."),
            }],
            "open_questions": [_pair("What remains unclear?")],
            "caveats": [_pair("A limited account."), _pair("No broad pattern established.")],
        },
    }


def _body(wire, kind):
    return wire["report" if kind == "self_portrait" else "criteria"]


def _first_claim(wire, kind):
    return _body(wire, kind)["claims" if kind == "self_portrait" else "stated"][0]


@pytest.mark.parametrize("kind", _KINDS)
def test_projection_is_complete_exact_deterministic_and_does_not_mutate(kind):
    wire = _wire(kind)
    before = copy.deepcopy(wire)
    projected = project_paired_bundle(kind, wire)
    assert wire == before
    reordered = json.loads(json.dumps(wire, sort_keys=True))
    assert project_paired_bundle(kind, reordered) == projected
    assert project_paired_bundle(kind, wire) == projected
    canonical = {key: value for key, value in projected.items() if key != "localized_text"}
    if kind == "self_portrait":
        expected = {
            "/report/data_coverage/covered/0": "Two synthetic accounts.",
            "/report/data_coverage/not_covered/0": "Other occasions.",
            "/report/data_coverage/not_covered/1": "Source authenticity.",
            "/report/claims/0/claim": "One episode only.",
            "/report/consistency_findings/0/stated": "An earlier statement.",
            "/report/consistency_findings/0/contradicting": "A later difference.",
            "/report/consistency_findings/0/framing": "A possible difference to clarify.",
            "/report/consistency_findings/0/clarifying_question": "Did the circumstances change?",
            "/report/consistency_findings/0/alt_benign_explanation": "Context might differ.",
            "/report/open_questions/0": "What remains unclear?",
            "/report/caveats/0": "A limited account.",
            "/report/caveats/1": "No broad pattern established.",
        }
        assert projected["report"]["consistency_findings"][0]["quotes"] == (
            wire["report"]["consistency_findings"][0]["quotes"]
        )
        assert projected["report"]["data_coverage"]["sources_read"] == ["S001", "S002"]
    else:
        expected = {
            "/criteria/stated/0/claim": "A stated wish.",
            "/criteria/revealed/0/claim": "A tentative preference.",
            "/criteria/open_questions/0": "What remains unclear?",
            "/criteria/caveats/0": "A limited account.",
            "/criteria/caveats/1": "No broad pattern established.",
            "/ideal_profiles/caveats/0": "No candidate exercise.",
            "/ideal_profiles/caveats/1": "No choices inferred.",
        }
        assert projected["ideal_profiles"]["candidates"] == []
    assert projected["localized_text"] == [
        {"path": path, "source": text, **_pair(text)} for path, text in expected.items()
    ]
    assert required_localization_sources(kind, canonical) == expected
    assert len(validate_localization(kind, canonical, projected["localized_text"])) == len(expected)
    assert parse_bundle(json.dumps(projected), kind) == projected
    claim = _first_claim(projected, kind)
    assert claim["evidence"] == _first_claim(wire, kind)["evidence"]
    assert (claim["type"], claim["confidence"]) == ("speculation", "low")


@pytest.mark.parametrize("kind", _KINDS)
def test_pairs_and_evidence_are_copied_without_trimming_or_interpreting_json_strings(kind):
    wire = _wire(kind)
    claim = _first_claim(wire, kind)
    claim["claim"] = {"en": "  Limited claim.\r\n", "zh": "  有限陈述。\r\n"}
    claim["evidence"] = [{"quote": '{"en":"quoted", "zh":"原文"}', "source": '{"en":"ID"}'}]
    result = project_paired_bundle(kind, wire)
    assert _first_claim(result, kind)["claim"] == claim["claim"]["en"]
    assert _first_claim(result, kind)["evidence"] == claim["evidence"]
    entry = next(item for item in result["localized_text"] if item["path"].endswith("/claim"))
    assert entry["en"] == claim["claim"]["en"]
    assert entry["zh"] == claim["claim"]["zh"]
    assert not any("/evidence/" in item["path"] for item in result["localized_text"])


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("invalid", [
    None, "flat legacy text", [], ["a", "b"], 1, True, {},
    {"en": "English only"}, {"zh": "只有中文"},
    {"en": "English", "zh": "中文", "source": "invented"},
    {"en": ["English"], "zh": "中文"}, {"en": "English", "zh": ["中文"]},
    {"en": " \n\t", "zh": "中文"}, {"en": "English", "zh": " \r\n"},
    {"en": 123, "zh": "中文"}, {"en": "English", "zh": False},
    {"en": "a" * 8001, "zh": "中文"}, {"en": "English", "zh": "中" * 8001},
])
def test_malformed_pairs_are_rejected_without_repair_or_echo(kind, invalid):
    wire = _wire(kind)
    _first_claim(wire, kind)["claim"] = invalid
    with pytest.raises(ArtifactValidationError) as error:
        project_paired_bundle(kind, wire)
    assert "invented" not in str(error.value)
    assert "input_value" not in str(error.value)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("pair", [
    {"en": "English", "zh": "English"},
    {"en": "123", "zh": "中文"},
    {"en": "English", "zh": "中"},
    {"en": "English中文", "zh": "中文翻译"},
])
def test_historical_language_checks_remain_final_authority(kind, pair):
    wire = _wire(kind)
    _first_claim(wire, kind)["claim"] = pair
    with pytest.raises(ArtifactValidationError, match="localization"):
        project_paired_bundle(kind, wire)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("where", ["bundle", "report", "claim", "pair", "evidence"])
def test_unknown_fields_at_each_shared_depth_are_rejected(kind, where):
    wire = _wire(kind)
    claim = _first_claim(wire, kind)
    target = {
        "bundle": wire, "report": _body(wire, kind), "claim": claim,
        "pair": claim["claim"], "evidence": claim["evidence"][0],
    }[where]
    target["PRIVATE_SENTINEL_EXTRA"] = "DO_NOT_ECHO"
    with pytest.raises(ArtifactValidationError) as error:
        project_paired_bundle(kind, wire)
    assert "PRIVATE_SENTINEL_EXTRA" not in str(error.value)
    assert "DO_NOT_ECHO" not in str(error.value)


@pytest.mark.parametrize("field", ["headline", "summary", "generated_at"])
def test_unsupported_portrait_channels_are_rejected_even_null(field):
    wire = _wire("self_portrait")
    wire["report"][field] = None
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle("self_portrait", wire)


@pytest.mark.parametrize("where", ["coverage", "finding", "ideal_profiles"])
def test_unknown_kind_specific_nested_fields_are_rejected(where):
    kind = "mate_criteria" if where == "ideal_profiles" else "self_portrait"
    wire = _wire(kind)
    target = (
        wire["ideal_profiles"] if where == "ideal_profiles"
        else wire["report"]["data_coverage"] if where == "coverage"
        else wire["report"]["consistency_findings"][0]
    )
    target["extra"] = "unsupported"
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, wire)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("field,value", [
    ("quote", {"en": "English", "zh": "中文"}), ("quote", []), ("quote", 1),
    ("quote", " "), ("quote", "q" * 8001),
    ("source", {"en": "S001", "zh": "来源"}), ("source", ["S001"]),
    ("source", None), ("source", 1), ("source", "s" * 1001),
])
def test_quotes_and_source_ids_must_retain_their_original_string_contract(kind, field, value):
    wire = _wire(kind)
    _first_claim(wire, kind)["evidence"][0][field] = value
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, wire)


@pytest.mark.parametrize("field,value", [("topic", "score"), ("type", "fact"),
                                         ("confidence", 1), ("confidence", "certain")])
def test_unknown_enums_are_rejected(field, value):
    wire = _wire("self_portrait")
    _first_claim(wire, "self_portrait")[field] = value
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle("self_portrait", wire)


@pytest.mark.parametrize("kind", _KINDS)
def test_legacy_flat_bundle_and_wrong_kind_are_not_fallback_formats(kind):
    canonical = project_paired_bundle(kind, _wire(kind))
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, canonical)
    del canonical["localized_text"]
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, canonical)
    other = "mate_criteria" if kind == "self_portrait" else "self_portrait"
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, _wire(other))


@pytest.mark.parametrize("candidate", [None, {}, {"description": _pair("Invented candidate.")}])
def test_candidate_array_is_strictly_empty(candidate):
    wire = _wire("mate_criteria")
    wire["ideal_profiles"]["candidates"] = [candidate]
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle("mate_criteria", wire)


@pytest.mark.parametrize("kind", _KINDS)
def test_empty_claims_remain_empty_and_metadata_omission_is_preserved(kind):
    wire = _wire(kind)
    body = _body(wire, kind)
    del body["report_type"]
    for field in (["claims", "consistency_findings"] if kind == "self_portrait"
                  else ["stated", "revealed"]):
        body[field] = []
    result = project_paired_bundle(kind, wire)
    assert "report_type" not in _body(result, kind)
    assert not any(item["path"].endswith("/claim") for item in result["localized_text"])


@pytest.mark.parametrize("kind,field,count", [
    ("self_portrait", "claims", 6), ("mate_criteria", "stated", 4),
    ("mate_criteria", "revealed", 4), ("self_portrait", "open_questions", 51),
    ("mate_criteria", "open_questions", 51), ("self_portrait", "caveats", 31),
    ("mate_criteria", "caveats", 31), ("self_portrait", "consistency_findings", 41),
])
def test_array_bounds_are_not_silently_truncated(kind, field, count):
    wire = _wire(kind)
    body = _body(wire, kind)
    body[field] = body[field] * count
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, wire)


@pytest.mark.parametrize("field,value", [
    ("sources_read", ["S001"] * 101), ("sources_read", [_pair("S001")]),
    ("covered", [_pair("Covered.")] * 51), ("not_covered", [_pair("Unknown.")] * 51),
])
def test_coverage_bounds_and_source_types_are_retained(field, value):
    wire = _wire("self_portrait")
    wire["report"]["data_coverage"][field] = value
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle("self_portrait", wire)


@pytest.mark.parametrize("target,count", [("evidence", 0), ("evidence", 21),
                                          ("quotes", 1), ("quotes", 21)])
def test_evidence_and_finding_quotation_count_bounds(target, count):
    wire = _wire("self_portrait")
    item = (_first_claim(wire, "self_portrait") if target == "evidence"
            else wire["report"]["consistency_findings"][0])
    item[target] = item[target][:1] * count
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle("self_portrait", wire)


@pytest.mark.parametrize("kind", _KINDS)
def test_generation_schema_is_tight_while_original_long_artifacts_still_validate(kind):
    wire = _wire(kind)
    schema = paired_bundle_schema(kind)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(wire)
    encoded = json.dumps(schema)
    assert "$ref" not in encoded and "$defs" not in encoded and "\\\\S" not in encoded
    assert "8000" not in encoded
    # Strings longer than the generation request remain fully accepted by the
    # established artifact contract. Neither projection nor parsing truncates.
    pair = {"en": "English " + "a" * 7992, "zh": "中文" + "中" * 7998}
    _first_claim(wire, kind)["claim"] = pair
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(wire)
    result = project_paired_bundle(kind, wire)
    assert _first_claim(result, kind)["claim"] == pair["en"]
    result_json = json.dumps(result, ensure_ascii=False)
    assert parse_bundle(result_json, kind) == result
    body = _body(result, kind)
    assert validate_local_artifact(body, kind) == body
    assert len(_first_claim(result, kind)["claim"]) == 8000


def test_schema_has_no_candidate_fields_and_cannot_generate_any_candidates():
    schema = paired_bundle_schema("mate_criteria")
    candidates = schema["properties"]["ideal_profiles"]["properties"]["candidates"]
    assert candidates["type"] == "array"
    assert candidates["maxItems"] == 0
    assert candidates["items"] == {"type": "null"}
    assert "synthetic_id" not in json.dumps(schema)
    for value in ([None], [{}], None, {}):
        wire = _wire("mate_criteria")
        wire["ideal_profiles"]["candidates"] = value
        with pytest.raises(ValidationError):
            Draft202012Validator(schema).validate(wire)


@pytest.mark.parametrize("kind", _KINDS)
def test_generation_nonblank_pattern_removal_does_not_weaken_validation(kind):
    wire = _wire(kind)
    _first_claim(wire, kind)["claim"] = {"en": " ", "zh": " "}
    Draft202012Validator(paired_bundle_schema(kind)).validate(wire)
    with pytest.raises(ArtifactValidationError):
        project_paired_bundle(kind, wire)


def test_wire_and_expanded_canonical_byte_budgets_are_both_enforced():
    wire = _wire("self_portrait")
    wire["report"]["open_questions"] = [{"en": "E" * 7000, "zh": "中文"}] * 25
    assert len(json.dumps(wire, ensure_ascii=False).encode()) < 512_000
    with pytest.raises(ArtifactValidationError, match="bundle"):
        project_paired_bundle("self_portrait", wire)
    wire["report"]["open_questions"] = [{"en": "E" * 7000, "zh": "中" * 7000}] * 25
    assert len(json.dumps(wire, ensure_ascii=False).encode()) > 512_000
    with pytest.raises(ArtifactValidationError, match="bilingual"):
        project_paired_bundle("self_portrait", wire)


def test_too_many_complete_localizations_rejected_instead_of_dropping_fields():
    wire = _wire("self_portrait")
    report = wire["report"]
    report["data_coverage"]["covered"] *= 50
    report["data_coverage"]["not_covered"] = [_pair("Unknown.")] * 50
    report["consistency_findings"] *= 40
    with pytest.raises(ArtifactValidationError, match="bundle"):
        project_paired_bundle("self_portrait", wire)


@pytest.mark.parametrize("invalid", [None, [], "text", 1, float("nan"), {"report": "\ud800"}])
def test_nonobject_nonfinite_and_non_utf8_input_errors_are_sanitized(invalid):
    with pytest.raises(ArtifactValidationError) as error:
        project_paired_bundle("self_portrait", invalid)
    assert "input_value" not in str(error.value)
    assert "surrogates" not in str(error.value)


def test_recursive_input_errors_are_sanitized():
    invalid = {}
    invalid["report"] = invalid
    with pytest.raises(ArtifactValidationError, match="bilingual"):
        project_paired_bundle("self_portrait", invalid)


@pytest.mark.parametrize("kind", ["unsupported", "social_self_portrait", None, []])
def test_unsupported_kind_is_rejected_by_all_public_entry_points(kind):
    for operation in (paired_bundle_schema, paired_bundle_prompt):
        with pytest.raises(ArtifactValidationError, match="Unsupported"):
            operation(kind)
    with pytest.raises(ArtifactValidationError, match="Unsupported"):
        project_paired_bundle(kind, {})


@pytest.mark.parametrize("kind", _KINDS)
def test_prompt_is_kind_scoped_and_preserves_safety_and_fidelity_limits(kind):
    prompt = paired_bundle_prompt(kind)
    assert json.dumps(paired_bundle_schema(kind), ensure_ascii=False) in prompt
    assert "exactly two string fields: en" in prompt
    assert "not a requirement or prohibition" in prompt
    assert "Prior generated reports, corrections" in prompt
    assert "No scores, rankings, diagnoses" in prompt
    assert "Do not output localized_text" in prompt
    assert "/report/" not in prompt and "/criteria/" not in prompt
    if kind == "self_portrait":
        assert "ideal_profiles" not in prompt and "candidates" not in prompt
        assert "TWO genuinely conflicting direct quotes" in prompt
    else:
        assert "consistency_findings" not in prompt
        assert "ideal_profiles.candidates MUST be []" in prompt
