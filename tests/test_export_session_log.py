from anti_dating_scam.browser_export.export_models import ExportMode
from anti_dating_scam.browser_export.export_session_log import ExportSessionLog


def test_export_session_log_records_files_without_chat_text(tmp_path) -> None:
    log = ExportSessionLog(ExportMode.VISIBLE_PAGE_EXPORT)
    log.add_file(tmp_path / "export.json")
    log.add_warning("Visible-page export may be incomplete.")
    log.finish()
    payload = log.to_dict()

    assert payload["export_count"] == 1
    assert payload["files"][0]["path"].endswith("export.json")
    assert "chat text" not in str(payload).lower()
    assert payload["mode"] == "visible_page_export"
