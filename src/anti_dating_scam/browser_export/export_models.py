from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


class ExportMode(StrEnum):
    VISIBLE_PAGE_EXPORT = "visible_page_export"
    CHAT2FILE_ASSISTED = "chat2file_assisted"


@dataclass(frozen=True)
class BrowserExportConfig:
    consent_confirmed: bool
    mode: ExportMode = ExportMode.VISIBLE_PAGE_EXPORT
    export_folder: Path = Path("local_exports/browser_exports")
    headless: bool = False
    max_chats_per_run: int | None = 10
    delay_between_exports_seconds: float = 2.0
    user_data_dir: Path = Path("local_exports/browser_profile")
    extension_path: Path | None = None
    extension_id: str | None = None
    chat_list_selector: str | None = None
    chat_title_selector: str | None = None
    export_button_selector: str | None = None
    upload_url: str | None = None
    requested_browser_storage_access: bool = False
    allow_normal_browser_profile: bool = False


@dataclass(frozen=True)
class ExportChunk:
    role: str
    text: str
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "order": self.order,
        }


@dataclass(frozen=True)
class VisiblePageExport:
    source_url: str
    page_title: str
    chunks: list[ExportChunk]
    captured_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    schema_version: str = "0.1"
    source: str = "visible_page_export"
    export_method: str = "manual_visible_capture"
    warnings: list[str] = field(
        default_factory=lambda: [
            "This export contains only visible page text and may be incomplete."
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source": self.source,
            "source_url": self.source_url,
            "page_title": self.page_title,
            "captured_at": self.captured_at,
            "export_method": self.export_method,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "warnings": self.warnings,
        }


@dataclass
class ExportSessionRecord:
    mode: ExportMode
    session_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at: str | None = None
    export_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files: list[dict[str, str]] = field(default_factory=list)

    def finish(self) -> None:
        self.ended_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "mode": self.mode.value,
            "export_count": self.export_count,
            "errors": self.errors,
            "warnings": self.warnings,
            "files": self.files,
        }
