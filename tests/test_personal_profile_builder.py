from anti_dating_scam.engine.personal_profile_builder import PersonalProfileBuilder
from anti_dating_scam.reports.schema_validator import validate_document


def test_personal_profile_builder_creates_valid_profile_json() -> None:
    profile = PersonalProfileBuilder().build(
        manual_notes="I value honesty, calm communication, privacy, and slow trust.",
        memory_summary="The user avoids money pressure and prefers identity verification.",
        chatgpt_export_summary={
            "limited_text_snippets": ["Public meetings and clear boundaries matter."]
        },
    )

    validate_document(profile, "personal_profile.schema.json")
    assert profile["owner_label"] == "local_user"
    assert profile["source_summary"]["manual_notes_used"] is True
    assert profile["source_summary"]["memory_summary_used"] is True
    assert profile["source_summary"]["chatgpt_export_used"] is True
    assert profile["uncertainty_notes"]
