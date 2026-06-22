from anti_dating_scam.profile.mpmd_profile import MPMDProfile
from anti_dating_scam.profile.profile_json import build_profile_json_from_sources
from anti_dating_scam.profile.profile_markdown import profile_to_mpmd_markdown


def test_mpmd_profile_converter_creates_valid_markdown() -> None:
    profile_json = build_profile_json_from_sources(
        manual_notes="I value honesty, privacy, calm communication, and slow trust.",
        memory_summary="The user avoids money pressure and prefers verification.",
    )
    markdown = profile_to_mpmd_markdown(MPMDProfile.from_profile_json(profile_json))

    assert "# AI-SlowMatch Local Personal Profile" in markdown
    assert "Markdown" not in markdown.splitlines()[0]
    assert "## Relationship Values" in markdown
    assert "## User Editable Notes" in markdown
    assert "not a psychological diagnosis" in markdown
