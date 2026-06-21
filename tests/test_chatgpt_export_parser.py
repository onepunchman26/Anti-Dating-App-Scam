import json
from pathlib import Path

from anti_dating_scam.engine.chatgpt_export_parser import ChatGPTExportParser


def test_chatgpt_export_parser_handles_missing_file_gracefully(tmp_path: Path) -> None:
    result = ChatGPTExportParser().parse(tmp_path / "missing.zip")

    assert result.conversations_count == 0
    assert result.messages_count == 0
    assert result.errors


def test_chatgpt_export_parser_reads_minimal_json(tmp_path: Path) -> None:
    export = [
        {
            "mapping": {
                "node": {
                    "message": {
                        "create_time": 1735689600,
                        "content": {"parts": ["I prefer slow trust and clear boundaries."]},
                    }
                }
            }
        }
    ]
    path = tmp_path / "conversations.json"
    path.write_text(json.dumps(export), encoding="utf-8")

    result = ChatGPTExportParser().parse(path)

    assert result.conversations_count == 1
    assert result.messages_count == 1
    assert result.limited_text_snippets
