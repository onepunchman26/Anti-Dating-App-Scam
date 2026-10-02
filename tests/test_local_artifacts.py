import copy

import pytest

from anti_dating_scam.reports.local_artifacts import (
    ArtifactValidationError,
    artifact_schema_prompt,
    validate_local_artifact,
)

SELF_MODEL = {
    "values": ["patience"], "life_goals": "Explore shared daily routines.",
    "communication_style": "Ask one direct question.", "boundaries": "Decline money requests.",
    "uncertainty_notes": "This is a limited synthetic sample, not a prediction.",
    "evidence_notes": "The fictional source describes preferring more time.",
}
CLAIM = {
    "topic": "communication", "claim": "The source describes asking for more time.",
    "evidence": [{"quote": "I prefer more time.", "source": "synthetic/notes.md"}],
    "type": "observation", "confidence": "low",
}
PORTRAIT = {
    "schema_version": "0.2", "data_coverage": {
        "sources_read": ["synthetic/notes.md"], "covered": ["communication"],
        "not_covered": ["behavior in a relationship"],
    }, "claims": [CLAIM], "consistency_findings": [], "open_questions": [],
    "caveats": ["One fictional note cannot establish a stable preference."],
}


def test_contracts_preserve_evidence_and_uncertainty():
    assert validate_local_artifact(PORTRAIT, "social_self_portrait") == PORTRAIT
    assert validate_local_artifact(SELF_MODEL, "self_model") == SELF_MODEL
    card = {
        "schema_version": "0.1", "tier2_summary": SELF_MODEL,
        "source": "self_model_from_ai_analysis_of_own_data",
    }
    assert validate_local_artifact(card, "compatibility_card") == card
    assert "additionalProperties" in artifact_schema_prompt("self_portrait")
    assert "evidence" in artifact_schema_prompt("mate_criteria")


@pytest.mark.parametrize("field,value", [
    ("evidence", []), ("type", "fact"), ("confidence", 0.9), ("confidence", "certain"),
    ("claim", "  "), ("score", 90), ("diagnosis", "synthetic prohibited field"),
])
def test_portrait_claims_fail_closed(field, value):
    payload = copy.deepcopy(PORTRAIT)
    payload["claims"][0][field] = value
    with pytest.raises(ArtifactValidationError):
        validate_local_artifact(payload, "social_self_portrait")


@pytest.mark.parametrize("kind", ["self_portrait", "social_self_portrait", "mate_criteria"])
def test_empty_arbitrary_objects_are_not_report_contracts(kind):
    with pytest.raises(ArtifactValidationError):
        validate_local_artifact({"report_type": kind}, kind)


def test_thin_evidence_can_produce_no_claims_with_caveats():
    payload = PORTRAIT | {"claims": []}
    assert validate_local_artifact(payload, "social_self_portrait")["claims"] == []
    with pytest.raises(ArtifactValidationError):
        validate_local_artifact(payload | {"caveats": []}, "social_self_portrait")


def test_incomplete_self_model_or_card_cannot_drop_uncertainty():
    for missing in ("uncertainty_notes", "evidence_notes"):
        payload = {key: value for key, value in SELF_MODEL.items() if key != missing}
        with pytest.raises(ArtifactValidationError):
            validate_local_artifact(payload, "self_model")
        with pytest.raises(ArtifactValidationError):
            validate_local_artifact({
                "schema_version": "0.1", "tier2_summary": payload,
                "source": "self_model_from_ai_analysis_of_own_data",
            }, "compatibility_card")


@pytest.mark.parametrize("patch", [
    {"age": 17}, {"age": "30"}, {"fictional": 1}, {"fictional": False},
    {"choice_reason": "Invented preference without interview evidence"},
    {"uncertainty_notes": ""}, {"social_score": 100},
])
def test_fictional_candidate_contract_rejects_underage_and_fabricated_choice(patch):
    candidate = {
        "synthetic_id": "adult-example-a", "age": 30, "fictional": True,
        "description": "Fictional adult who likes quiet evenings.", "choice_reason": None,
        "evidence": [], "uncertainty_notes": "A scenario, not a real person.",
    }
    payload = {"schema_version": "0.1", "candidates": [candidate | patch],
               "caveats": ["Fictional scenarios cannot predict real compatibility."]}
    with pytest.raises(ArtifactValidationError):
        validate_local_artifact(payload, "ideal_profiles")


def test_plan_needs_cautions_and_uncertainty():
    plan = {"stages": [{
        "name": "Conversation", "goal": "Ask about a shared interest.",
        "actions": ["Ask once and respect a refusal."], "example_lines": [],
        "cautions": ["Do not send money."], "ready_when": "Both choose to continue.",
    }], "uncertainty_notes": "A rehearsal cannot predict another person's response."}
    assert validate_local_artifact(plan, "relationship_plan") == plan
    plan["stages"][0]["cautions"] = []
    with pytest.raises(ArtifactValidationError):
        validate_local_artifact(plan, "relationship_plan")


def test_invalid_artifact_error_does_not_echo_submitted_content():
    secret = "synthetic-private-marker"
    with pytest.raises(ArtifactValidationError) as error:
        validate_local_artifact({"private_field": secret}, "self_model")
    assert secret not in str(error.value)
    assert "private_field" not in str(error.value)


def test_nonfinite_or_oversized_objects_are_rejected():
    for payload in ({"score": float("nan")}, {"data": "x" * 512001}):
        with pytest.raises(ArtifactValidationError):
            validate_local_artifact(payload, "self_model")
