"""The external boundary must not drift from its Python source of truth."""

import json
from pathlib import Path

from anti_dating_scam.models.work_profile import ShareableSummary


def test_site_uses_generated_python_contract():
    root = Path(__file__).resolve().parents[1]
    expected = ShareableSummary.model_json_schema()
    for path in (
        root / "src/anti_dating_scam/schemas/shareable_profile.schema.json",
        root / "apps/matching_site/lib/shareable-profile.schema.json",
    ):
        assert json.loads(path.read_text(encoding="utf-8")) == expected


def test_hosted_source_has_no_private_profile_or_assessment_tool():
    root = Path(__file__).resolve().parents[1]
    names = (root / "apps/matching_site/lib/tools.mjs").read_text(encoding="utf-8")
    assert "assessment-save" not in names
    assert "profile-read" not in names
    assert "source_vault" not in names
    assert "slowmatch_publish_summary" in names
