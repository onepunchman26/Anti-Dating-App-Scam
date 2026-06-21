from pathlib import Path
from typing import Any

from anti_dating_scam.browser_export.errors import BrowserAutomationUnavailableError
from anti_dating_scam.browser_export.export_models import BrowserExportConfig
from anti_dating_scam.browser_export.safety_guard import BrowserExportSafetyGuard


class PlaywrightBrowserRunner:
    """Visible Playwright runner for local user-assisted export.

    This module imports Playwright lazily so normal app use does not require the
    optional browser dependency.
    """

    def __init__(self, safety_guard: BrowserExportSafetyGuard | None = None) -> None:
        self.safety_guard = safety_guard or BrowserExportSafetyGuard()

    def build_launch_plan(self, config: BrowserExportConfig) -> dict[str, Any]:
        result = self.safety_guard.ensure_allowed(config)
        args = []
        if config.extension_path:
            extension = str(Path(config.extension_path).resolve())
            args.extend(
                [
                    f"--disable-extensions-except={extension}",
                    f"--load-extension={extension}",
                ]
            )
        return {
            "headless": False,
            "user_data_dir": str(config.user_data_dir),
            "downloads_path": str(config.export_folder),
            "args": args,
            "warnings": result.warnings,
        }

    def launch_visible_context(self, config: BrowserExportConfig):
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:
            raise BrowserAutomationUnavailableError(
                'Playwright is required. Install dependencies with: pip install -e ".[browser]"'
            ) from exc

        launch_plan = self.build_launch_plan(config)
        config.user_data_dir.mkdir(parents=True, exist_ok=True)
        config.export_folder.mkdir(parents=True, exist_ok=True)
        playwright = sync_playwright().start()
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(config.user_data_dir),
            headless=False,
            accept_downloads=True,
            downloads_path=str(config.export_folder),
            args=launch_plan["args"],
        )
        return playwright, context
