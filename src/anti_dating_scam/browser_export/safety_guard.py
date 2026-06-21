from dataclasses import dataclass, field
from pathlib import Path

from anti_dating_scam.browser_export.errors import BrowserExportSafetyError
from anti_dating_scam.browser_export.export_models import BrowserExportConfig


@dataclass(frozen=True)
class SafetyCheckResult:
    allowed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BrowserExportSafetyGuard:
    """Validate assisted browser export settings before any automation runs."""

    SUSPICIOUS_SELECTOR_TERMS = (
        "cookie",
        "token",
        "password",
        "passwd",
        "localstorage",
        "sessionstorage",
        "authorization",
        "bearer",
        "secret",
    )

    def check(
        self,
        config: BrowserExportConfig,
        *,
        real_user_export: bool = True,
    ) -> SafetyCheckResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not config.consent_confirmed:
            errors.append("Consent is required before assisted browser export.")
        if real_user_export and config.headless:
            errors.append("Headless mode is blocked for real user export.")
        if config.requested_browser_storage_access:
            errors.append(
                "Access to cookies, localStorage, sessionStorage, or browser secrets is blocked."
            )
        if config.max_chats_per_run is None or config.max_chats_per_run <= 0:
            errors.append("A positive max_chats_per_run limit is required.")
        elif config.max_chats_per_run > 100:
            errors.append("max_chats_per_run is too high for a user-assisted export run.")
        if config.upload_url:
            errors.append("Uploading exported chats to a server is blocked.")
        if config.allow_normal_browser_profile:
            warnings.append(
                
                    "Using a normal browser profile is discouraged. Prefer a dedicated "
                    "local app profile."
                
            )

        selector_errors = self._suspicious_selector_errors(config)
        errors.extend(selector_errors)

        if not self._is_local_path(config.export_folder):
            errors.append("Export folder must be a local filesystem path.")
        if not self._is_local_path(config.user_data_dir):
            errors.append("User data directory must be a local filesystem path.")

        return SafetyCheckResult(allowed=not errors, errors=errors, warnings=warnings)

    def ensure_allowed(
        self,
        config: BrowserExportConfig,
        *,
        real_user_export: bool = True,
    ) -> SafetyCheckResult:
        result = self.check(config, real_user_export=real_user_export)
        if not result.allowed:
            raise BrowserExportSafetyError("; ".join(result.errors))
        return result

    def _suspicious_selector_errors(self, config: BrowserExportConfig) -> list[str]:
        errors: list[str] = []
        selectors = [
            config.chat_list_selector,
            config.chat_title_selector,
            config.export_button_selector,
            config.extension_id,
        ]
        for selector in selectors:
            normalized = (selector or "").lower()
            if any(term in normalized for term in self.SUSPICIOUS_SELECTOR_TERMS):
                errors.append(
                    "Suspicious selector/config detected. Token, cookie, password, "
                    "or browser storage extraction is not allowed."
                )
                break
        return errors

    def _is_local_path(self, path: Path) -> bool:
        value = str(path)
        return not value.lower().startswith(("http://", "https://", "ftp://"))
