import json
from pathlib import Path
from typing import Any


class ProfileStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.home() / ".ai_slowmatch"
        self.markdown_path = self.base_dir / "profile.mpm.md"
        self.json_path = self.base_dir / "profile.json"
        self.reports_dir = self.base_dir / "reports"
        self.imports_dir = self.base_dir / "imports"

    def create_default_directories(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.imports_dir.mkdir(parents=True, exist_ok=True)

    def detect_existing_profile(self) -> bool:
        return self.markdown_path.exists() or self.json_path.exists()

    def load_markdown_profile(self, path: Path | None = None) -> str:
        return (path or self.markdown_path).read_text(encoding="utf-8")

    def load_json_profile(self, path: Path | None = None) -> dict[str, Any]:
        return json.loads((path or self.json_path).read_text(encoding="utf-8"))

    def save_markdown_profile(self, markdown: str, path: Path | None = None) -> Path:
        self.create_default_directories()
        output_path = path or self.markdown_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return output_path

    def save_json_profile(self, profile: dict[str, Any], path: Path | None = None) -> Path:
        self.create_default_directories()
        output_path = path or self.json_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        return output_path

    def get_reports_dir(self) -> Path:
        self.create_default_directories()
        return self.reports_dir

    def get_imports_dir(self) -> Path:
        self.create_default_directories()
        return self.imports_dir
