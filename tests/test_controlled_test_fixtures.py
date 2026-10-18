"""Release synthetic inputs use the real contracts, and require explicit test consent."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from anti_dating_scam.models.work_profile import ProfileUpdate, SummaryDraftRequest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/controlled_test_fixtures.ps1"
SHELL = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(not SHELL, reason="PowerShell fixture generator")


@pytest.mark.parametrize("role", ["A", "B"])
def test_explicit_fixtures_match_contract_and_do_not_publish(tmp_path, role):
    result = subprocess.run(
        [SHELL, "-NoProfile", "-File", str(SCRIPT), "-Role", role,
         "-Scope", "test:preview", "-ConfirmedAdultSyntheticTest"],
        env={**os.environ, "LOCALAPPDATA": str(tmp_path)}, capture_output=True,
        text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    reply = json.loads(result.stdout)
    assert reply["network_calls"] == reply["model_calls"] == 0
    assert not reply["published"]
    assert str(tmp_path) not in result.stdout
    root = tmp_path / reply["relative_localappdata_directory"]
    profile = ProfileUpdate.model_validate_json((root / "private-profile-update.json").read_bytes())
    assert f"SYNTHETIC_PRIVATE_{role}" in profile.changes[0].claim.text
    for mode in ["dating", "friendship"]:
        raw = (root / f"{mode}-draft-input.json").read_bytes()
        draft = SummaryDraftRequest.model_validate_json(raw)
        assert draft.summary.mode == mode
        assert draft.summary.alias == f"Synthetic {role}"
        assert "SYNTHETIC_PRIVATE" not in raw.decode()
        if mode == "friendship":
            assert "relationship_goal" not in raw.decode()


def test_fixture_generation_without_consent_does_not_create_files(tmp_path):
    result = subprocess.run(
        [SHELL, "-NoProfile", "-File", str(SCRIPT), "-Role", "A", "-Scope", "test:preview"],
        env={**os.environ, "LOCALAPPDATA": str(tmp_path)}, capture_output=True,
        text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["code"] == "explicit_adult_synthetic_test_consent_required"
    assert not (tmp_path / "AI-SlowMatch").exists()
