"""Offline synthetic transport checks for the opt-in reproducible local smoke."""

import json
import os
import runpy
import sys
from pathlib import Path

import pytest
from test_full_report_regeneration import _paired

from anti_dating_scam.ai.privacy import BackendError
from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.report_revisions import ReportRevisionService


@pytest.fixture
def smoke():
    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_full_report_regeneration.py"
    return runpy.run_path(str(script))


def _reply(kind, payload, *, quote_override=None):
    owner = json.loads(payload["messages"][-1]["content"])["ORIGINAL_EXCERPTS_UNVERIFIED"]
    narrative = "SYNTHETIC_GENERATED_PRIVATE_CONTENT remains a tentative interpretation."
    caveat = "Only the selected fictional notes were considered."
    no_candidates = "No candidate exercise was conducted."
    claim = {
        "topic": "communication",
        "type": "speculation",
        "confidence": "low",
        "claim": narrative,
        "evidence": [{"source": "S001", "quote": quote_override or owner[0]["text"]}],
    }
    canonical = (
        {
            "report": {
                "schema_version": "0.2",
                "report_type": kind,
                "data_coverage": {
                    "sources_read": [item["id"] for item in owner],
                    "covered": [],
                    "not_covered": [],
                },
                "claims": [claim],
                "consistency_findings": [],
                "open_questions": [],
                "caveats": [caveat],
            }
        }
        if kind == "self_portrait"
        else {
            "criteria": {
                "schema_version": "0.1",
                "report_type": kind,
                "stated": [claim],
                "revealed": [],
                "open_questions": [],
                "caveats": [caveat],
            },
            "ideal_profiles": {
                "schema_version": "0.1",
                "candidates": [],
                "caveats": [no_candidates],
            },
        }
    )
    translations = {
        narrative: "合成私密生成内容仍是暂定解释。",
        caveat: "仅考虑了所选虚构笔记。",
        no_candidates: "未开展候选人练习。",
    }
    bundle = {
        **canonical,
        "localized_text": [
            {"path": pointer, "source": value, "en": value, "zh": translations[value]}
            for pointer, value in required_localization_sources(kind, canonical).items()
        ],
    }
    return {"message": {"content": json.dumps(_paired(bundle))}}


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_one_call_full_chain_is_isolated_preserves_existing_selection_and_leaks_no_content(
    smoke,
    tmp_path,
    capsys,
    kind,
):
    output = tmp_path / "result.json"
    output.write_text('{"status":"passed","stale":true}', encoding="utf-8")
    originals = {
        name: os.environ.get(name) for name in ("HOME", "USERPROFILE", "ADS_NO_AUTOCONNECT")
    }
    old_path = sys.path[:]
    calls, temporary_homes = [], []

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        temporary_home = Path(os.environ["HOME"])
        temporary_homes.append(temporary_home)
        assert os.environ["USERPROFILE"] == str(temporary_home)
        assert os.environ["ADS_NO_AUTOCONNECT"] == "1"
        assert temporary_home.is_dir()
        vault = temporary_home / "synthetic-vault"
        assert list((vault / "reports" / "active_selections" / kind).glob("*/selection.json"))
        state = json.loads(output.read_text(encoding="utf-8"))
        assert state["status"] == "running" and state["stage"] == "local_generation"
        assert state["inference_requests"] == 1 and "stale" not in state
        assert 0 < timeout <= 30
        assert url == "http://127.0.0.1:11434/api/chat"
        return _reply(kind, payload)

    assert smoke["run_smoke"](kind, "synthetic-test-model", 30, output, transport=transport) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "passed" and result["stage"] == "complete"
    assert result["originals_unchanged"] and result["active_selection_unchanged"]
    assert result["saved_reopened"] and result["visible_copies"] == 1
    assert result["allow_schema_fallback"] is False
    assert result["inference_requests"] == 1 and len(calls) == 1
    assert result["semantic_review"].startswith("not_performed")
    assert "SYNTHETIC_GENERATED_PRIVATE_CONTENT" not in output.read_text() + capsys.readouterr().out
    assert not any(home.exists() for home in temporary_homes)
    assert {name: os.environ.get(name) for name in originals} == originals
    assert sys.path == old_path


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("failure", ["schema_400", "network", "invalid_json", "invalid_quote"])
def test_provider_failures_are_single_call_sanitized_and_preserve_originals(
    smoke,
    tmp_path,
    capsys,
    kind,
    failure,
):
    output = tmp_path / "result.json"
    output.write_text('{"status":"passed","stale":true}', encoding="utf-8")
    calls, temporary_homes = [], []
    previous_home = os.environ.get("HOME")

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        temporary_homes.append(Path(os.environ["HOME"]))
        if failure == "schema_400":
            raise BackendError("AI provider HTTP error (400).")
        if failure == "network":
            raise TimeoutError("SYNTHETIC_PRIVATE_PROVIDER_ERROR")
        if failure == "invalid_json":
            return {"message": {"content": "SYNTHETIC_PRIVATE_PROVIDER_ERROR"}}
        return _reply(kind, payload, quote_override="SYNTHETIC_PRIVATE_PROVIDER_ERROR")

    assert smoke["run_smoke"](kind, "synthetic-test-model", 30, output, transport=transport) == 1
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "failed" and result["inference_requests"] == 1
    assert len(calls) == 1 and result["visible_copies"] == 0
    assert result["originals_unchanged"] and result["active_selection_unchanged"]
    assert not result["saved_reopened"] and "stale" not in result
    assert "SYNTHETIC_PRIVATE" not in output.read_text() + capsys.readouterr().out
    assert os.environ.get("HOME") == previous_home
    assert not any(home.exists() for home in temporary_homes)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.test",
        "http://127.0.0.1/private",
        "http://secret@localhost:11434",
        "http://localhost:11434?private=1",
    ],
)
def test_unsupported_endpoints_never_reach_transport(smoke, tmp_path, url):
    calls = []
    output = tmp_path / "result.json"
    assert (
        smoke["run_smoke"](
            "self_portrait",
            "synthetic-model",
            30,
            output,
            base_url=url,
            transport=lambda *args: calls.append(args),
        )
        == 1
    )
    assert calls == []
    result = json.loads(output.read_text())
    assert result["status"] == "failed" and result["inference_requests"] == 0
    assert url not in output.read_text()


@pytest.mark.parametrize(
    "kind,model,timeout",
    [
        ("other", "synthetic-model", 30),
        ("self_portrait", "synthetic-cloud", 30),
        ("self_portrait", "synthetic:cloud", 30),
        ("self_portrait", "", 30),
        ("self_portrait", "synthetic-model", 0),
        ("self_portrait", "synthetic-model", 301),
        ("self_portrait", "synthetic-model", float("inf")),
        ("self_portrait", "synthetic-model", float("nan")),
        ("self_portrait", "synthetic-model", True),
    ],
)
def test_invalid_parameters_clear_stale_success_without_provider_call(
    smoke,
    tmp_path,
    kind,
    model,
    timeout,
):
    calls = []
    output = tmp_path / "result.json"
    output.write_text('{"status":"passed","stale":true}', encoding="utf-8")
    assert (
        smoke["run_smoke"](kind, model, timeout, output, transport=lambda *args: calls.append(args))
        == 1
    )
    assert calls == []
    result = json.loads(output.read_text())
    assert result["status"] == "failed" and "stale" not in result
    assert result["inference_requests"] == 0


@pytest.mark.parametrize("when", ["before", "after"])
def test_total_budget_includes_preparation_and_discards_a_late_reply(
    smoke,
    tmp_path,
    monkeypatch,
    when,
):
    run = smoke["run_smoke"]
    clock = {"now": 100.0}
    monkeypatch.setattr(run.__globals__["time"], "monotonic", lambda: clock["now"])
    fixture = run.__globals__["_synthetic_fixture"]
    calls = []

    def slow_fixture(*args):
        value = fixture(*args)
        if when == "before":
            clock["now"] += 31
        return value

    def transport(url, payload, headers, timeout):
        calls.append(payload)
        clock["now"] += 31
        return _reply("self_portrait", payload)

    monkeypatch.setitem(run.__globals__, "_synthetic_fixture", slow_fixture)
    output = tmp_path / "result.json"
    assert run("self_portrait", "synthetic-model", 30, output, transport=transport) == 1
    result = json.loads(output.read_text())
    assert len(calls) == (when == "after")
    assert result["inference_requests"] == len(calls)
    assert result["status"] == "failed" and result["visible_copies"] == 0
    assert result["originals_unchanged"] and result["active_selection_unchanged"]


@pytest.mark.parametrize("failure", ["save", "reopen"])
def test_save_and_reopen_failures_do_not_leave_a_success_record(
    smoke,
    tmp_path,
    monkeypatch,
    capsys,
    failure,
):
    def explode(*args, **kwargs):
        raise ValueError("SYNTHETIC_PRIVATE_SAVING_ERROR")

    monkeypatch.setattr(
        ReportRevisionService,
        "save_full_regeneration" if failure == "save" else "read_verified_bundle",
        explode,
    )
    output = tmp_path / "result.json"
    assert (
        smoke["run_smoke"](
            "self_portrait",
            "synthetic-model",
            30,
            output,
            transport=lambda url, payload, headers, timeout: _reply("self_portrait", payload),
        )
        == 1
    )
    result = json.loads(output.read_text())
    assert result["status"] == "failed" and not result["saved_reopened"]
    assert result["originals_unchanged"] and result["active_selection_unchanged"]
    assert "SYNTHETIC_PRIVATE" not in output.read_text() + capsys.readouterr().out


def test_a_changed_original_is_reported_as_failure_without_rollback_or_false_preservation(
    smoke,
    tmp_path,
):
    def transport(url, payload, headers, timeout):
        source = Path(os.environ["HOME"]) / "synthetic-vault" / "reports" / "self_portrait.json"
        source.write_bytes(source.read_bytes() + b"\n")
        return _reply("self_portrait", payload)

    output = tmp_path / "result.json"
    assert (
        smoke["run_smoke"]("self_portrait", "synthetic-model", 30, output, transport=transport) == 1
    )
    result = json.loads(output.read_text())
    assert result["status"] == "failed" and result["originals_unchanged"] is False
    assert result["active_selection_unchanged"] and result["visible_copies"] == 0


def test_total_budget_also_includes_local_save_and_reopen(smoke, tmp_path, monkeypatch):
    clock = {"now": 100.0}
    monkeypatch.setattr(smoke["run_smoke"].__globals__["time"], "monotonic", lambda: clock["now"])
    original = ReportRevisionService.read_verified_bundle

    def slow_reopen(*args, **kwargs):
        result = original(*args, **kwargs)
        clock["now"] += 31
        return result

    monkeypatch.setattr(ReportRevisionService, "read_verified_bundle", slow_reopen)
    output = tmp_path / "result.json"
    assert (
        smoke["run_smoke"](
            "self_portrait",
            "synthetic-model",
            30,
            output,
            transport=lambda url, payload, headers, timeout: _reply("self_portrait", payload),
        )
        == 1
    )
    result = json.loads(output.read_text())
    assert result["status"] == "failed" and result["error_type"] == "TimeoutError"
    assert result["inference_requests"] == 1 and result["saved_reopened"]
    assert result["originals_unchanged"] and result["active_selection_unchanged"]


def test_core_only_smoke_never_imports_desktop_or_test_fixtures(smoke, tmp_path, monkeypatch):
    import builtins

    original_import = builtins.__import__

    def check_import(name, *args, **kwargs):
        assert not name.startswith(("anti_dating_scam_desktop", "test_full_report"))
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", check_import)
    assert (
        smoke["run_smoke"](
            "mate_criteria",
            "synthetic-model",
            30,
            tmp_path / "result.json",
            transport=lambda url, payload, headers, timeout: _reply("mate_criteria", payload),
        )
        == 0
    )


def test_cli_requires_explicit_kind_model_and_bounded_timeout_before_running(smoke, monkeypatch):
    calls = []
    main = smoke["main"]
    monkeypatch.setitem(
        main.__globals__, "run_smoke", lambda *args, **kwargs: calls.append(args) or 0
    )
    for arguments in [
        [],
        ["--model", "synthetic-model"],
        ["--kind", "self_portrait", "--model", "synthetic-cloud"],
        ["--kind", "self_portrait", "--model", "synthetic", "--timeout", "inf"],
    ]:
        with pytest.raises(SystemExit) as error:
            main(arguments)
        assert error.value.code == 2
    assert calls == []
    assert main(["--kind", "mate_criteria", "--model", "synthetic-model", "--timeout", "30"]) == 0
    assert calls[0][:3] == ("mate_criteria", "synthetic-model", 30)
    assert calls[0][3].name == "full-report-regeneration-smoke.json"
