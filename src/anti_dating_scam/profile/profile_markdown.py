from anti_dating_scam.profile.mpmd_profile import MPMDProfile


def profile_to_mpmd_markdown(profile: MPMDProfile) -> str:
    sections: list[str] = [
        "# AI-SlowMatch Local Personal Profile",
        "",
        "> This document is user-owned and locally stored.",
        "> It is a self-reflection aid, not a psychological diagnosis.",
        "",
        "## Source Summary",
        "",
        f"- Created at: {profile.created_at}",
        f"- Updated at: {profile.updated_at}",
        "- Sources used:",
    ]
    sections.extend(_bullet_items(profile.sources_used or ["No sources recorded yet."]))
    sections.append("- Uncertainty notes:")
    sections.extend(_bullet_items(profile.uncertainty_notes))

    for title, items in [
        ("Relationship Values", profile.relationship_values),
        ("Communication Preferences", profile.communication_preferences),
        ("Boundary Preferences", profile.boundary_preferences),
        ("Risk Tolerance Notes", profile.risk_tolerance_notes),
        ("Trust Ladder Preferences", profile.trust_ladder_preferences),
        ("Social Connection Notes", profile.social_connection_notes),
        ("Self-Reflection Notes", profile.self_reflection_notes),
        ("Things to Verify Later", profile.things_to_verify_later),
    ]:
        sections.extend(["", f"## {title}", ""])
        sections.extend(_bullet_items(items))

    sections.extend(["", "## User Editable Notes", "", profile.user_editable_notes])
    return "\n".join(sections).strip() + "\n"


def _bullet_items(items: list[str]) -> list[str]:
    if not items:
        return ["- Not specified yet."]
    return [f"- {item}" for item in items]
