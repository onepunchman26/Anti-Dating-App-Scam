"""Run the real browser card gate with Node; no browser/network/personal data."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HTML = Path(__file__).resolve().parents[1] / "apps" / "rendezvous_web" / "index.html"


def _node():
    executable = shutil.which("node")
    if executable is None:
        pytest.skip("Node is unavailable for the standalone browser-script gate.")
    return executable


def test_browser_script_syntax():
    script = HTML.read_text(encoding="utf-8").split("<script>", 1)[1].split("</script>", 1)[0]
    result = subprocess.run(
        [_node(), "--check", "-"], input=script, capture_output=True,
        text=True, encoding="utf-8", timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_browser_card_gate_matches_evidence_uncertainty_and_extra_field_contract():
    html = HTML.read_text(encoding="utf-8")
    script = html.split("function validateCompatibilityCard(card)", 1)[1]
    validator = "function validateCompatibilityCard(card)" + script.split(
        "/* End compatibility-card structure. */", 1
    )[0]
    card = {
        "schema_version": "0.1", "source": "self_model_from_ai_analysis_of_own_data",
        "tier2_summary": {
            "values": ["patience", "合成值"], "life_goals": "A shared routine.",
            "communication_style": "Ask clearly.", "boundaries": "No money requests.",
            "uncertainty_notes": "A limited fictional sample.",
            "evidence_notes": "Synthetic notes only.",
        },
    }
    exercise = """
const assert = require('node:assert/strict');
assert.equal(validateCompatibilityCard(card), card);
for (const value of [null, [], {}, {...card, score: 100}]) {
  assert.throws(() => validateCompatibilityCard(value));
}
for (const key of ['evidence_notes', 'uncertainty_notes', 'boundaries']) {
  const value = structuredClone(card); delete value.tier2_summary[key];
  assert.throws(() => validateCompatibilityCard(value));
}
for (const values of [[], [3], [' '], ['x'.repeat(1001)]]) {
  const value = structuredClone(card); value.tier2_summary.values = values;
  assert.throws(() => validateCompatibilityCard(value));
}
const invalid = structuredClone(card); invalid.tier2_summary.evidence_notes = '\\ud800';
assert.throws(() => validateCompatibilityCard(invalid));
"""
    result = subprocess.run(
        [_node(), "-"], input=validator + "\nconst card = " + json.dumps(card) + ";\n" + exercise,
        capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    assert result.returncode == 0, result.stderr
