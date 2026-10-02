"""Manual handoffs must describe the same validated artifacts as connected AI."""

import json
import re
from copy import deepcopy

import pytest
from anti_dating_scam_desktop import agent_handoff
from jsonschema import Draft202012Validator, ValidationError
from test_localized_reports import _criteria, _entries, _portrait
from test_self_portrait_html import SAMPLE

from anti_dating_scam.reports.artifact_bundles import bundle_schema, parse_bundle
from anti_dating_scam.reports.localized_reports import render_localized_reports


def _request(tmp_path, kind):
    (tmp_path / "imports").mkdir(exist_ok=True)
    (tmp_path / "imports" / "notes.txt").write_text(
        "I prefer clear communication. I want time to reflect.", encoding="utf-8"
    )
    builder = (
        agent_handoff.build_self_portrait_request
        if kind == "self_portrait"
        else agent_handoff.build_criteria_interview_request
    )
    return builder(tmp_path)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_manual_contract_matches_runtime_schema_and_renders_valid_bilingual_bundle(tmp_path, kind):
    body = _request(tmp_path, kind)
    schemas = re.findall(r"```json\n(.*?)\n```", body, re.DOTALL)
    assert len(schemas) == 1
    schema = json.loads(schemas[0])
    assert schema == bundle_schema(kind)
    Draft202012Validator.check_schema(schema)
    canonical = _portrait() if kind == "self_portrait" else _criteria()
    if kind == "self_portrait":
        for optional in ("headline", "summary", "generated_at"):
            canonical["report"].pop(optional)
    bundle = {**canonical, "localized_text": _entries(kind, canonical)}
    Draft202012Validator(schema).validate(bundle)
    validated = parse_bundle(
        json.dumps(bundle), kind,
        evidence_text="I prefer clear communication. I want time to reflect.",
    )
    rendered = render_localized_reports(kind, canonical, validated["localized_text"])
    assert "English" in rendered["markdown"]
    assert "中文版" in rendered["markdown"]
    assert f"reports/{kind}_localization.json" in body
    assert "Before writing ANY report file" in body
    assert "写入任何报告文件前" in body
    assert "user_only_original_text" in body
    assert "legacy_archives" in body


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_old_manual_output_shapes_do_not_satisfy_new_manual_contract(tmp_path, kind):
    body = _request(tmp_path, kind)
    schema = json.loads(re.findall(r"```json\n(.*?)\n```", body, re.DOTALL)[0])
    legacy = (
        {"report": deepcopy(SAMPLE), "localized_text": []}
        if kind == "self_portrait"
        else {
            "criteria": {
                "schema_version": "0.1", "report_type": "mate_criteria",
                "stated_criteria": [], "revealed_criteria": [], "caveats": ["Uncertain"],
            },
            "ideal_profiles": {"schema_version": "0.1", "candidates": [], "caveats": ["Uncertain"]},
            "localized_text": [],
        }
    )
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(legacy)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_building_manual_contract_does_not_convert_or_overwrite_old_reports(tmp_path, kind):
    reports = tmp_path / "reports"
    reports.mkdir()
    original = reports / f"{kind}.json"
    content = b'\xef\xbb\xbf{"schema_version":"legacy","unknown":"untouched"}\r\n'
    original.write_bytes(content)
    _request(tmp_path, kind)
    assert original.read_bytes() == content
    assert list(reports.iterdir()) == [original]
