import json
from datetime import UTC, datetime
from pathlib import Path

from anti_dating_scam.browser_export.export_models import ExportMode, ExportSessionRecord


class ExportSessionLog:
    """Session log that records metadata only, not full chat contents."""

    def __init__(self, mode: ExportMode) -> None:
        self.record = ExportSessionRecord(mode=mode)

    def add_file(self, path: str | Path, *, status: str = "exported") -> None:
        self.record.export_count += 1
        self.record.files.append(
            {
                "path": str(path),
                "status": status,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def add_warning(self, warning: str) -> None:
        self.record.warnings.append(warning)

    def add_error(self, error: str) -> None:
        self.record.errors.append(error)

    def finish(self) -> None:
        self.record.finish()

    def to_dict(self) -> dict:
        return self.record.to_dict()

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_path
