from typing import Any

from anti_dating_scam.engine.personal_profile_builder import PersonalProfileBuilder


def build_profile_json_from_sources(
    *,
    manual_notes: str = "",
    memory_summary: str = "",
    chatgpt_export_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return PersonalProfileBuilder().build(
        manual_notes=manual_notes,
        memory_summary=memory_summary,
        chatgpt_export_summary=chatgpt_export_summary,
    )
