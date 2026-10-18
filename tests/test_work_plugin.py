"""Plugin setup and the installed launcher exercise the same Python core."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "work_plugin_setup", ROOT / "scripts/work_plugin_setup.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def fake_source(tmp_path):
    root = tmp_path / "source"
    (root / "src/anti_dating_scam").mkdir(parents=True)
    (root / "src/anti_dating_scam/work_cli.py").write_text("", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname="anti-dating-scam"\nversion="0.6.0"\n', encoding="utf-8"
    )
    return root


def test_setup_atomic_registration_preserves_unrelated_files(tmp_path):
    root = fake_source(tmp_path)
    destination = tmp_path / "runtime/work-runtime.json"
    destination.parent.mkdir()
    other = destination.parent / "unrelated.txt"
    other.write_text("keep", encoding="utf-8")
    receipt = setup.configure(root, destination)
    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert receipt == {"configured": True, "version": "0.6.0", "private_data_read": False}
    assert saved["source_root"] == str(root.resolve())
    assert saved["python"] == str(Path(sys.executable).resolve())
    assert other.read_text() == "keep"
    assert not list(destination.parent.glob("*.tmp"))


def test_setup_rejects_source_and_onedrive_config(tmp_path):
    root = fake_source(tmp_path)
    for destination in (root / "runtime.json", tmp_path / "OneDrive/runtime.json"):
        with pytest.raises(ValueError):
            setup.configure(root, destination)
        assert not destination.exists()


def test_setup_requires_original_core(tmp_path):
    root = fake_source(tmp_path)
    (root / "src/anti_dating_scam/work_cli.py").unlink()
    with pytest.raises(ValueError):
        setup.configure(root, tmp_path / "runtime.json")


@pytest.mark.skipif(os.name != "nt", reason="Windows launcher")
def test_developer_launcher_explicitly_uses_registered_core_in_another_process(tmp_path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell
    appdata = tmp_path / "appdata"
    setup.configure(ROOT, appdata / "AI-SlowMatch/work-runtime.json")
    result = subprocess.run(
        [
            shell,
            "-NoProfile",
            "-File",
            str(ROOT / "plugins/slowmatch/scripts/work.ps1"),
            "--developer-source",
            "profile-read",
            "--data-dir",
            str(tmp_path / "private"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env={**os.environ, "LOCALAPPDATA": str(appdata)},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    reply = json.loads(result.stdout)
    assert reply["ok"] is True
    assert reply["result"]["revision"] == 0
    assert reply["result"]["claims"] == []
