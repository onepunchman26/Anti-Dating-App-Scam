import pytest

from anti_dating_scam.browser_export.chat2file_assistant import Chat2FileAssistant
from anti_dating_scam.browser_export.errors import BrowserExportSafetyError
from anti_dating_scam.browser_export.export_models import BrowserExportConfig, ExportMode


def test_chat2file_assistant_builds_safe_plan() -> None:
    config = BrowserExportConfig(
        consent_confirmed=True,
        mode=ExportMode.CHAT2FILE_ASSISTED,
        max_chats_per_run=5,
        export_button_selector="button.export",
    )

    plan = Chat2FileAssistant().build_plan(config).to_dict()

    assert plan["experimental"] is True
    assert plan["max_chats_per_run"] == 5
    assert any("visible" in step.lower() for step in plan["steps"])


def test_chat2file_assistant_does_not_run_without_consent() -> None:
    config = BrowserExportConfig(
        consent_confirmed=False,
        mode=ExportMode.CHAT2FILE_ASSISTED,
    )

    with pytest.raises(BrowserExportSafetyError):
        Chat2FileAssistant().run(config)
