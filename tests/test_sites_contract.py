"""The external boundary must not drift from its Python source of truth."""

import json
from pathlib import Path

from anti_dating_scam.models.work_planning import (
    MeetingPlan,
    SharedPlanningPreferences,
    planning_schema,
)
from anti_dating_scam.models.work_profile import shareable_summary_schema


def test_site_uses_generated_python_contract():
    root = Path(__file__).resolve().parents[1]
    expected = shareable_summary_schema()
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


def test_planning_contracts_match_the_python_allowlist():
    root = Path(__file__).resolve().parents[1]
    for model, local, remote in (
        (SharedPlanningPreferences, "shared_planning_preferences", "shared-planning-preferences"),
        (MeetingPlan, "meeting_plan", "meeting-plan"),
    ):
        for path in (
            root / f"src/anti_dating_scam/schemas/{local}.schema.json",
            root / f"apps/matching_site/lib/{remote}.schema.json",
        ):
            assert json.loads(path.read_text(encoding="utf-8")) == planning_schema(model)
