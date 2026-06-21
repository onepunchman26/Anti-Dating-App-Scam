from datetime import UTC, datetime
from typing import Any


class PersonalProfileBuilder:
    """Build a local personal relationship profile document with heuristic extraction."""

    def build(
        self,
        *,
        manual_notes: str = "",
        memory_summary: str = "",
        chatgpt_export_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        snippets = []
        if chatgpt_export_summary:
            snippets = chatgpt_export_summary.get("limited_text_snippets", [])[:10]

        combined_text = "\n".join([manual_notes, memory_summary, *snippets])
        return {
            "schema_version": "0.1",
            "created_at": now,
            "updated_at": now,
            "owner_label": "local_user",
            "source_summary": {
                "manual_notes_used": bool(manual_notes.strip()),
                "chatgpt_export_used": bool(chatgpt_export_summary),
                "memory_summary_used": bool(memory_summary.strip()),
            },
            "relationship_values": self._extract_values(combined_text),
            "boundary_preferences": self._extract_boundaries(combined_text),
            "communication_preferences": self._extract_communication(combined_text),
            "risk_tolerance_notes": self._extract_risk_tolerance(combined_text),
            "trust_ladder_preferences": self._extract_trust_ladder(combined_text),
            "self_reflection_notes": self._extract_reflections(manual_notes, memory_summary),
            "uncertainty_notes": [
                "This profile is generated from user-provided local text and may be incomplete.",
                (
                    "ChatGPT Memory Summary may be incomplete and is not an "
                    "authoritative full self-profile."
                ),
                "This profile is not a diagnosis, score, or prediction of relationship success.",
            ],
        }

    def _extract_values(self, text: str) -> list[str]:
        lowered = text.lower()
        values: list[str] = []
        keyword_map = {
            "honesty": "Honesty and transparency matter.",
            "trust": "Trust should grow slowly through repeated behavior.",
            "kind": "Kindness and emotional steadiness are valued.",
            "family": "Family or close community context may matter.",
            "long-term": "Long-term relationship intention may matter.",
            "serious": "Serious relationship intention may matter.",
        }
        for keyword, note in keyword_map.items():
            if keyword in lowered and note not in values:
                values.append(note)
        return values or [
            "Relationship values were not clearly extractable from the provided text."
        ]

    def _extract_boundaries(self, text: str) -> list[str]:
        lowered = text.lower()
        boundaries: list[str] = []
        if "money" in lowered or "gift card" in lowered or "crypto" in lowered:
            boundaries.append(
                "Do not send money, gift cards, crypto, or bank details to online-only contacts."
            )
        if "privacy" in lowered or "private" in lowered:
            boundaries.append(
                "Protect private images, identity documents, and sensitive information."
            )
        if "pressure" in lowered or "boundary" in lowered:
            boundaries.append("Slow down or step back when boundaries are pressured.")
        if "slow" in lowered:
            boundaries.append("Prefer slow trust building over rapid escalation.")
        return boundaries or ["Boundary preferences should be clarified by the user."]

    def _extract_communication(self, text: str) -> list[str]:
        lowered = text.lower()
        preferences: list[str] = []
        if "calm" in lowered:
            preferences.append("Prefer calm disagreement and repair attempts.")
        if "direct" in lowered or "honest" in lowered:
            preferences.append("Prefer direct and honest communication.")
        if "video" in lowered or "call" in lowered:
            preferences.append(
                "Use consent-based calls or video verification when trust needs more context."
            )
        return preferences or ["Communication preferences were not clearly extractable."]

    def _extract_risk_tolerance(self, text: str) -> list[str]:
        lowered = text.lower()
        notes: list[str] = []
        if any(term in lowered for term in ["scam", "risk", "fraud", "money", "crypto"]):
            notes.append("Treat financial requests and investment pitches as high-risk signals.")
        if "verify" in lowered or "identity" in lowered:
            notes.append("Prefer safe, consent-based identity verification before deeper trust.")
        return notes or ["Risk tolerance notes should be reviewed and completed by the user."]

    def _extract_trust_ladder(self, text: str) -> list[str]:
        lowered = text.lower()
        preferences = ["Do not recommend rapid escalation."]
        if "public" in lowered or "meet" in lowered:
            preferences.append("Use a public-place safety checklist before offline meetings.")
        if "slow" in lowered or "verify" in lowered:
            preferences.append(
                "Stay at lower trust stages until consistency and boundaries are visible."
            )
        return preferences

    def _extract_reflections(self, manual_notes: str, memory_summary: str) -> list[str]:
        reflections: list[str] = []
        for label, text in [
            ("Manual notes", manual_notes),
            ("Memory summary", memory_summary),
        ]:
            cleaned = " ".join(line.strip() for line in text.splitlines() if line.strip())
            if cleaned:
                reflections.append(
                    f"{label} provided by user, "
                    f"{min(len(cleaned), 500)} characters summarized locally."
                )
        return reflections or ["No self-reflection notes were provided."]


def profile_to_markdown(profile: dict[str, Any]) -> str:
    sections = [
        "# Local Personal Relationship Profile",
        "",
        f"- Owner label: `{profile.get('owner_label', 'local_user')}`",
        f"- Created at: `{profile.get('created_at', 'unknown')}`",
        "",
    ]
    for key, title in [
        ("relationship_values", "Relationship Values"),
        ("boundary_preferences", "Boundary Preferences"),
        ("communication_preferences", "Communication Preferences"),
        ("risk_tolerance_notes", "Risk Tolerance Notes"),
        ("trust_ladder_preferences", "Trust Ladder Preferences"),
        ("self_reflection_notes", "Self-Reflection Notes"),
        ("uncertainty_notes", "Uncertainty Notes"),
    ]:
        sections.append(f"## {title}")
        for item in profile.get(key, []):
            sections.append(f"- {item}")
        sections.append("")
    return "\n".join(sections).strip() + "\n"
