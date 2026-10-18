"""Register the existing Python core for the local Work plugin; never reads profiles."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


def configure(root: Path, destination: Path | None = None) -> dict:
    root = root.resolve(strict=True)
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if project["name"] != "anti-dating-scam":
        raise ValueError("This is not the AI-SlowMatch source project.")
    if not (root / "src/anti_dating_scam/work_cli.py").is_file():
        raise ValueError("The Work core CLI is not installed in this source project.")
    if destination is None:
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise ValueError("LOCALAPPDATA is required for this Windows plugin launcher.")
        destination = Path(local) / "AI-SlowMatch/work-runtime.json"
    destination = destination.absolute()
    resolved = destination.resolve()
    if resolved.is_relative_to(root) or any(
        p.lower().startswith("onedrive") for p in resolved.parts
    ):
        raise ValueError("Runtime configuration must stay outside source and OneDrive.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
        raise ValueError("Linked runtime configuration paths are not supported.")
    runtime = {
        "schema_version": 1,
        "source_root": str(root),
        "python": str(Path(sys.executable).resolve()),
        "project_version": project["version"],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp"
    ) as stream:
        temporary = Path(stream.name)
        json.dump(runtime, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {"configured": True, "version": project["version"], "private_data_read": False}


def install(root: Path) -> dict:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    manifest_path = root / "plugins/slowmatch/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["version"] != project["version"]:
        raise ValueError("Plugin and project versions differ; update the package before install.")
    cli = shutil.which("codex")
    if not cli:
        raise ValueError("The supported Codex plugin installer was not found.")
    for arguments in (
        ["plugin", "marketplace", "add", str(root), "--json"],
        ["plugin", "add", "slowmatch@slowmatch-local", "--json"],
    ):
        result = subprocess.run(
            [cli, *arguments], cwd=root, capture_output=True, text=True, timeout=60, check=False
        )
        if result.returncode:
            raise ValueError("The supported plugin installer failed; no success is claimed.")
    return {"installed": True, "desktop_chat_loading_verified": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["configure", "install"])
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        result = configure(root)
        if args.command == "install":
            result.update(install(root))
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError):
        print(json.dumps({"ok": False, "error": "plugin_setup_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
