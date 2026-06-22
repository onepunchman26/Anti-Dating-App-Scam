from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class MPMDProfile:
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    sources_used: list[str] = field(default_factory=list)
    uncertainty_notes: list[str] = field(default_factory=list)
    relationship_values: list[str] = field(default_factory=list)
    communication_preferences: list[str] = field(default_factory=list)
    boundary_preferences: list[str] = field(default_factory=list)
    risk_tolerance_notes: list[str] = field(default_factory=list)
    trust_ladder_preferences: list[str] = field(default_factory=list)
    social_connection_notes: list[str] = field(default_factory=list)
    self_reflection_notes: list[str] = field(default_factory=list)
    things_to_verify_later: list[str] = field(default_factory=list)
    user_editable_notes: str = ""

    @classmethod
    def from_profile_json(cls, profile: dict[str, Any]) -> "MPMDProfile":
        source_summary = profile.get("source_summary", {})
        sources_used = [
            label
            for key, label in [
                ("manual_notes_used", "Manual Markdown / Notes"),
                ("chatgpt_export_used", "ChatGPT or AI chat export"),
                ("memory_summary_used", "ChatGPT Memory Summary"),
            ]
            if source_summary.get(key)
        ]
        return cls(
            created_at=profile.get("created_at", datetime.now(UTC).isoformat()),
            updated_at=profile.get("updated_at", datetime.now(UTC).isoformat()),
            sources_used=sources_used,
            uncertainty_notes=profile.get("uncertainty_notes", []),
            relationship_values=profile.get("relationship_values", []),
            communication_preferences=profile.get("communication_preferences", []),
            boundary_preferences=profile.get("boundary_preferences", []),
            risk_tolerance_notes=profile.get("risk_tolerance_notes", []),
            trust_ladder_preferences=profile.get("trust_ladder_preferences", []),
            self_reflection_notes=profile.get("self_reflection_notes", []),
            things_to_verify_later=[
                "Review whether this profile reflects your current boundaries.",
                "Remove sensitive details before sharing any profile excerpt.",
            ],
        )
