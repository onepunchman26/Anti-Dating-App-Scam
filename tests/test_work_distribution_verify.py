"""Verifier privacy/measurement tests; no packaged EXE is executed here."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import work_distribution_verify as verifier


def test_recorder_counts_actual_utf8_and_characters_but_retains_no_private_body(
    tmp_path, monkeypatch
):
    captured = []
    body = {"private": "SYNTHETIC_PRIVATE_MARKER：资料"}
    response = json.dumps({"ok": True, "result": body}, ensure_ascii=False).encode()

    def synthetic_process(command, **kwargs):
        captured.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=response, stderr=b"")

    monkeypatch.setattr(verifier.subprocess, "run", synthetic_process)
    recorder = verifier.Recorder(tmp_path / "portable", {"PATH": "synthetic-system-only"})
    result = recorder.call("synthetic_operation", Path("unused.exe"), ["schema"], body)
    assert result["result"] == body
    step = recorder.steps[0]
    assert step["output_utf8_bytes"] == len(response)
    assert step["output_unicode_characters"] == len(response.decode("utf-8"))
    assert step["output_utf8_bytes"] > step["output_unicode_characters"]
    assert "SYNTHETIC_PRIVATE" not in json.dumps(recorder.steps)
    assert captured[0][1]["env"] == {"PATH": "synthetic-system-only"}
    assert captured[0][1]["input"] == verifier.runtime.encoded(body)
    assert "shell" not in captured[0][1]


def test_expected_refusal_and_unexpected_private_error_are_not_quoted(tmp_path, monkeypatch):
    response = {
        "ok": False,
        "error": {"code": "owner_binding_mismatch", "private_extra": "DO_NOT_LOG"},
    }
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(
            returncode=1,
            stdout=json.dumps(response).encode(),
            stderr=b"SYNTHETIC_PRIVATE_STDERR",
        ),
    )
    recorder = verifier.Recorder(tmp_path / "portable", {})
    recorder.call("refused", Path("unused.exe"), [], expected_error="owner_binding_mismatch")
    assert recorder.steps[0]["passed"] is True
    assert recorder.steps[0]["expected_refusal"] is True
    with pytest.raises(verifier.VerificationError, match="unexpected_child_result") as error:
        recorder.call("unexpected", Path("unused.exe"), [])
    assert "DO_NOT_LOG" not in str(error.value)
    assert "SYNTHETIC_PRIVATE_STDERR" not in json.dumps(recorder.steps)


def test_invalid_child_json_and_large_output_fail_without_echo(tmp_path, monkeypatch):
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(
            returncode=1,
            stdout=b"PRIVATE_NOT_JSON",
            stderr=b"",
        ),
    )
    recorder = verifier.Recorder(tmp_path / "portable", {})
    with pytest.raises(verifier.VerificationError, match="invalid_child_result"):
        recorder.call("bad_result", Path("unused.exe"), [])
    assert recorder.last_step == "bad_result"
    assert recorder.steps == []


@pytest.mark.skipif(os.name != "nt", reason="Windows environment contract")
def test_restricted_child_environment_excludes_user_secrets_and_developer_paths(monkeypatch):
    monkeypatch.setenv("SYNTHETIC_SECRET", "never-pass-to-child")
    monkeypatch.setenv("PYTHONPATH", "developer-source")
    monkeypatch.setenv("VIRTUAL_ENV", "developer-environment")
    monkeypatch.setenv("PATH", "developer-python;developer-node;developer-git")
    queries = []
    monkeypatch.setattr(verifier.shutil, "which", lambda name, path: queries.append((name, path)))
    environment = verifier.clean_environment()
    assert "SYNTHETIC_SECRET" not in environment
    assert "PYTHONPATH" not in environment
    assert "VIRTUAL_ENV" not in environment
    assert "developer" not in environment["PATH"]
    assert len(queries) == 5
    assert all(path == environment["PATH"] for _, path in queries)


def test_main_redacts_unexpected_exception_and_argument_paths(monkeypatch, capsys):
    def refused(*_):
        raise OSError("PRIVATE_FULL_PATH_AND_BODY")

    monkeypatch.setattr(verifier, "verify", refused)
    assert verifier.main(["--package", "synthetic-package"]) == 1
    result = capsys.readouterr().out
    assert "PRIVATE_FULL_PATH_AND_BODY" not in result
    assert json.loads(result)["error"]["code"] == "verification_precondition_failed"
    assert verifier.main(["--package", "synthetic-package", "--private-argument"]) == 1
    result = capsys.readouterr().out
    assert "private-argument" not in result


def test_synthetic_request_has_explicit_source_and_confirmation():
    request = verifier.private_claim("values", verifier.TEXT_VALUES)
    assert request["claim"]["confirmation"] == "confirmed"
    assert request["claim"]["source"]["reference"] == "synthetic-package-verification"
    corrected = verifier.private_claim("values", verifier.TEXT_CORRECTED, "a" * 32)
    assert corrected["claim"]["confirmation"] == "corrected"
    assert corrected["claim"]["id"] == "a" * 32
