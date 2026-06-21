from dataclasses import dataclass
from typing import Any

from anti_dating_scam.browser_export.errors import BrowserExportSafetyError
from anti_dating_scam.browser_export.export_models import BrowserExportConfig, ExportMode
from anti_dating_scam.browser_export.safety_guard import BrowserExportSafetyGuard


@dataclass
class Chat2FilePlan:
    mode: str
    experimental: bool
    max_chats_per_run: int
    delay_between_exports_seconds: float
    steps: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "experimental": self.experimental,
            "max_chats_per_run": self.max_chats_per_run,
            "delay_between_exports_seconds": self.delay_between_exports_seconds,
            "steps": self.steps,
            "warnings": self.warnings,
        }


class Chat2FileAssistant:
    """Experimental planning helper for user-installed Chat2file export clicks."""

    def __init__(self, safety_guard: BrowserExportSafetyGuard | None = None) -> None:
        self.safety_guard = safety_guard or BrowserExportSafetyGuard()
        self.paused = False
        self.stopped = False

    def build_plan(self, config: BrowserExportConfig) -> Chat2FilePlan:
        if config.mode != ExportMode.CHAT2FILE_ASSISTED:
            config = BrowserExportConfig(
                **{
                    **config.__dict__,
                    "mode": ExportMode.CHAT2FILE_ASSISTED,
                }
            )
        result = self.safety_guard.ensure_allowed(config)
        warnings = [
            *result.warnings,
            (
                "Chat2file-assisted mode is experimental and may break when extension "
                "or page UI changes."
            ),
            "If extension popup automation is unreliable, use native visible-page export instead.",
        ]
        if not config.extension_path:
            warnings.append(
                "No unpacked extension path configured; extension automation may be unavailable."
            )
        if not config.export_button_selector:
            warnings.append(
                "No export button selector configured; manual intervention may be required."
            )

        steps = [
            (
                "Launch a visible persistent browser context with a dedicated local "
                "user data directory."
            ),
            "Wait for the user to manually log in and confirm readiness.",
            "Iterate only through visible chat list items up to max_chats_per_run.",
            (
                "For each visible chat, click the configured visible export button or "
                "pause for manual action."
            ),
            "Wait delay_between_exports_seconds between actions.",
            "Record exported file paths and statuses in the session log without storing chat text.",
            "Pause on errors instead of forcing actions.",
        ]
        return Chat2FilePlan(
            mode=ExportMode.CHAT2FILE_ASSISTED.value,
            experimental=True,
            max_chats_per_run=config.max_chats_per_run or 0,
            delay_between_exports_seconds=config.delay_between_exports_seconds,
            steps=steps,
            warnings=warnings,
        )

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def stop(self) -> None:
        self.stopped = True

    def run(self, config: BrowserExportConfig) -> dict[str, Any]:
        if not config.consent_confirmed:
            raise BrowserExportSafetyError("Consent is required before Chat2file-assisted export.")
        plan = self.build_plan(config)
        return {
            "status": "planned_not_executed",
            "reason": "The MVP creates a safe plan but does not force extension automation.",
            "plan": plan.to_dict(),
        }
