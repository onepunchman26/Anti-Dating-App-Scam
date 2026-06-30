from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppState:
    consent_accepted: bool = False
    profile_exists: bool = False
    vault_path: Path | None = None
    profile_path: Path | None = None
    profile_json_path: Path | None = None
    analysis_mode: str | None = None
    import_sources: list[Path] = field(default_factory=list)
    current_profile_markdown: str | None = None
    current_profile_json: dict | None = None
    manual_notes: str = ""
    memory_summary: str = ""
    chatgpt_export_summary: dict | None = None
    risk_report: dict | None = None
    signed_report: dict | None = None
    provider_name: str = "Mock"
    model_name: str = "local-rule-based-mvp"

    def as_legacy_dict(self) -> dict:
        """Compatibility bridge for existing MVP widgets that still expect a dict."""

        return {
            "consent_confirmed": self.consent_accepted,
            "manual_notes": self.manual_notes,
            "memory_summary": self.memory_summary,
            "chatgpt_export_summary": self.chatgpt_export_summary,
            "profile": self.current_profile_json,
            "risk_report": self.risk_report,
            "signed_report": self.signed_report,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
        }

    def sync_from_legacy_dict(self, values: dict) -> None:
        """Pull legacy-widget state back into AppState.

        Rough-edge fix: this method is invoked from `_go_home`, which is shared by
        screens that mutate `legacy_state` (risk/trust/report/settings screens) AND
        screens that write directly to AppState and never touch `legacy_state`
        (profile detection/generation). For the latter, every key in `values` is
        still present but unset (e.g. `values["profile"] is None`), so a plain
        `dict.get(key, default)` would return that explicit `None` and silently
        wipe out a profile the user just loaded or created. Only overwrite a field
        when the legacy dict actually carries a non-empty value; otherwise keep
        whatever AppState already holds.
        """

        def _present(value, current):
            return value if value not in (None, "") else current

        self.consent_accepted = bool(values.get("consent_confirmed", self.consent_accepted))
        self.manual_notes = _present(values.get("manual_notes"), self.manual_notes)
        self.memory_summary = _present(values.get("memory_summary"), self.memory_summary)
        self.chatgpt_export_summary = _present(
            values.get("chatgpt_export_summary"), self.chatgpt_export_summary
        )
        self.current_profile_json = _present(values.get("profile"), self.current_profile_json)
        self.risk_report = _present(values.get("risk_report"), self.risk_report)
        self.signed_report = _present(values.get("signed_report"), self.signed_report)
        self.provider_name = _present(values.get("provider_name"), self.provider_name)
        self.model_name = _present(values.get("model_name"), self.model_name)
