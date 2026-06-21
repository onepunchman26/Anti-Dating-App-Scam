import pytest

from anti_dating_scam.browser_export.errors import BrowserExportSafetyError
from anti_dating_scam.browser_export.export_models import BrowserExportConfig
from anti_dating_scam.browser_export.safety_guard import BrowserExportSafetyGuard


def test_safety_guard_blocks_missing_consent() -> None:
    config = BrowserExportConfig(consent_confirmed=False)

    result = BrowserExportSafetyGuard().check(config)

    assert not result.allowed
    assert any("Consent" in error for error in result.errors)


def test_safety_guard_blocks_headless_real_export() -> None:
    config = BrowserExportConfig(consent_confirmed=True, headless=True)

    with pytest.raises(BrowserExportSafetyError):
        BrowserExportSafetyGuard().ensure_allowed(config)


def test_safety_guard_blocks_unlimited_max_chats() -> None:
    config = BrowserExportConfig(consent_confirmed=True, max_chats_per_run=None)

    result = BrowserExportSafetyGuard().check(config)

    assert not result.allowed
    assert any("max_chats_per_run" in error for error in result.errors)


def test_safety_guard_blocks_token_extraction_selector() -> None:
    config = BrowserExportConfig(
        consent_confirmed=True,
        export_button_selector="[data-token-value]",
    )

    result = BrowserExportSafetyGuard().check(config)

    assert not result.allowed
    assert any("Suspicious selector" in error for error in result.errors)
