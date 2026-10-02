"""The opt-in smoke must never leave a stale success after a failed run."""

import json
import os
import runpy
from pathlib import Path

import pytest
from anti_dating_scam_desktop import ai_backend


@pytest.mark.parametrize(
    ("failure", "expected_stage"),
    [
        ("portrait", "portrait_generation_and_validation"),
        ("interview", "interview_turn"),
        ("criteria", "criteria_generation_and_validation"),
        (None, "complete"),
    ],
)
def test_smoke_replaces_stale_result_and_excludes_report_contents(
    monkeypatch, tmp_path, capsys, failure, expected_stage
):
    smoke = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts" / "smoke_desktop_ai.py")
    )
    output = tmp_path / "journey.json"
    output.write_text('{"status":"passed","stale":true}', encoding="utf-8")
    previous_home = os.environ.get("HOME")
    private_marker = "SYNTHETIC_PRIVATE_REPORT_CONTENT"

    def portrait(backend, store):
        current = json.loads(output.read_text(encoding="utf-8"))
        assert current["status"] == "running"
        assert "stale" not in current
        if failure == "portrait":
            raise ValueError(private_marker)
        artifact = tmp_path / "portrait.md"
        artifact.write_text(private_marker, encoding="utf-8")
        return artifact

    class FakeBackend:
        def __init__(self, **kwargs):
            pass

        def chat(self, *args, **kwargs):
            if failure == "interview":
                raise ValueError(private_marker)
            return "Which boundary matters most?"

    def criteria(backend, store, history, system):
        if failure == "criteria":
            raise ValueError(private_marker)
        store.ideal_profiles_json_path.parent.mkdir(parents=True, exist_ok=True)
        store.ideal_profiles_json_path.write_text("{}", encoding="utf-8")
        artifact = tmp_path / "criteria.md"
        artifact.write_text(private_marker, encoding="utf-8")
        return artifact

    monkeypatch.setattr(ai_backend, "OllamaChatBackend", FakeBackend)
    monkeypatch.setattr(ai_backend, "run_self_portrait", portrait)
    monkeypatch.setattr(ai_backend, "run_criteria_synthesis", criteria)
    exit_code = smoke["run_chain"]("synthetic-model", 10, output)
    recorded = output.read_text(encoding="utf-8")
    result = json.loads(recorded)
    assert exit_code == (1 if failure else 0)
    assert result["status"] == ("failed" if failure else "passed")
    assert result["stage"] == expected_stage
    assert private_marker not in recorded + capsys.readouterr().out
    assert os.environ.get("HOME") == previous_home
    assert "stale" not in result


def test_smoke_limits_timeout_before_calling_provider():
    smoke = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts" / "smoke_desktop_ai.py")
    )
    with pytest.raises(SystemExit) as exc:
        smoke["main"](["--model", "synthetic-model", "--timeout", "601"])
    assert exc.value.code == 2
