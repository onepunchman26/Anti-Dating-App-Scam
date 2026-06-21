from datetime import UTC, datetime
from pathlib import Path


class DownloadWatcher:
    """Small helper for local download folders.

    It does not inspect browser internals or network responses.
    """

    def __init__(self, folder: str | Path) -> None:
        self.folder = Path(folder)

    def snapshot(self) -> set[Path]:
        if not self.folder.exists():
            return set()
        return {path for path in self.folder.iterdir() if path.is_file()}

    def new_files_since(self, previous: set[Path]) -> list[Path]:
        return sorted(self.snapshot() - previous)

    def timestamped_session_log_path(self) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return self.folder / f"export_session_{timestamp}.json"
