import json
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ChatGPTExportSummary:
    source_path: str
    conversations_count: int = 0
    messages_count: int = 0
    date_range: dict[str, str | None] = field(default_factory=lambda: {"start": None, "end": None})
    limited_text_snippets: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "conversations_count": self.conversations_count,
            "messages_count": self.messages_count,
            "date_range": self.date_range,
            "limited_text_snippets": self.limited_text_snippets,
            "warnings": self.warnings,
            "errors": self.errors,
        }


class ChatGPTExportParser:
    """Parse local ChatGPT exports without uploading or displaying full raw text."""

    def parse(self, path: str | Path, *, snippet_limit: int = 20) -> ChatGPTExportSummary:
        source = Path(path)
        summary = ChatGPTExportSummary(source_path=str(source))
        if not source.exists():
            summary.errors.append("File does not exist.")
            return summary

        try:
            if source.suffix.lower() == ".zip":
                payload = self._load_from_zip(source, summary)
            elif source.suffix.lower() == ".json":
                payload = json.loads(source.read_text(encoding="utf-8"))
            else:
                summary.errors.append("Unsupported file type. Use .zip or .json.")
                return summary
        except (OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            summary.errors.append(f"Could not parse export: {exc}")
            return summary

        if payload is None:
            return summary

        self._summarize_payload(payload, summary, snippet_limit=snippet_limit)
        if summary.conversations_count == 0 and summary.messages_count == 0:
            summary.warnings.append(
                "No recognizable ChatGPT conversations were found. Export structure may be unknown."
            )
        return summary

    def _load_from_zip(self, source: Path, summary: ChatGPTExportSummary) -> Any | None:
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            candidates = [
                name
                for name in names
                if name.lower().endswith("conversations.json")
                or name.lower().endswith("conversation.json")
            ]
            if not candidates:
                summary.errors.append("No conversations.json file found in the ZIP export.")
                return None
            with archive.open(candidates[0]) as file_handle:
                return json.loads(file_handle.read().decode("utf-8"))

    def _summarize_payload(
        self,
        payload: Any,
        summary: ChatGPTExportSummary,
        *,
        snippet_limit: int,
    ) -> None:
        if isinstance(payload, list):
            conversations = payload
        elif isinstance(payload, dict) and isinstance(payload.get("conversations"), list):
            conversations = payload["conversations"]
        else:
            summary.warnings.append("JSON did not match known ChatGPT export structures.")
            return

        summary.conversations_count = len(conversations)
        timestamps: list[datetime] = []
        snippets: list[str] = []
        for conversation in conversations:
            messages = self._extract_messages(conversation)
            summary.messages_count += len(messages)
            for message in messages:
                timestamp = self._message_time(message)
                if timestamp:
                    timestamps.append(timestamp)
                text = self._message_text(message)
                if text and len(snippets) < snippet_limit:
                    snippets.append(text[:500])

        summary.limited_text_snippets = snippets
        if timestamps:
            timestamps.sort()
            summary.date_range = {
                "start": timestamps[0].isoformat(),
                "end": timestamps[-1].isoformat(),
            }

    def _extract_messages(self, conversation: dict[str, Any]) -> list[dict[str, Any]]:
        mapping = conversation.get("mapping")
        if isinstance(mapping, dict):
            messages = []
            for node in mapping.values():
                if isinstance(node, dict) and isinstance(node.get("message"), dict):
                    messages.append(node["message"])
            return messages

        messages = conversation.get("messages")
        if isinstance(messages, list):
            return [message for message in messages if isinstance(message, dict)]
        return []

    def _message_text(self, message: dict[str, Any]) -> str:
        content = message.get("content")
        if isinstance(content, dict):
            parts = content.get("parts")
            if isinstance(parts, list):
                return "\n".join(str(part) for part in parts if isinstance(part, str)).strip()
            text = content.get("text")
            if isinstance(text, str):
                return text.strip()
        if isinstance(message.get("text"), str):
            return message["text"].strip()
        return ""

    def _message_time(self, message: dict[str, Any]) -> datetime | None:
        value = message.get("create_time") or message.get("update_time")
        if isinstance(value, int | float):
            return datetime.fromtimestamp(value, tz=UTC)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
