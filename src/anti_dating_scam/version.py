"""Product version from pyproject metadata; frozen build details are generated."""

from __future__ import annotations

import json
import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def build_info() -> dict:
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "anti_dating_scam" / "build_info.json"
        return json.loads(path.read_text(encoding="utf-8"))
    project = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if project.is_file():
        value = tomllib.loads(project.read_text(encoding="utf-8"))["project"]["version"]
    else:
        try:
            value = version("anti-dating-scam")
        except PackageNotFoundError:
            value = "unknown"
    return {"version": value, "build_id": "source", "git_commit": "", "dirty": True}
