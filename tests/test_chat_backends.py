import json
from pathlib import Path

import pytest

from anti_dating_scam.ai.chat_backends import BackendError, CliAgentBackend
from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.api.routes_local_ai import HOLLOW_MODEL_DETAIL, is_hollow_model


def test_claude_calls_are_isolated_without_tools_or_sessions(tmp_path):
    calls = []

    def runner(args, cwd, timeout, input_text=None):
        calls.append((args, cwd, input_text))
        assert cwd != str(tmp_path)
        assert Path(cwd).is_dir()
        return 0, json.dumps({"result": "reply", "session_id": "unused"}), ""

    backend = CliAgentBackend(
        cli="claude", workdir=str(tmp_path), runner=runner, which=lambda name: "claude"
    )
    for prompt in ("A reviewed summary", "A different reviewed summary"):
        request = build_reviewed_request(
            [{"role": "user", "content": prompt}],
            system="TRUSTED",
            recipient=backend.recipient,
        )
        assert backend.chat(request) == "reply"
    assert calls[0][1] != calls[1][1]
    for argv, cwd, stdin in calls:
        assert "--resume" not in argv and "--add-dir" not in argv
        assert "--bare" in argv and "--no-session-persistence" in argv
        assert argv[argv.index("--tools") + 1] == ""
        assert "reviewed summary" in stdin
        assert all("reviewed summary" not in arg for arg in argv)
        assert not Path(cwd).exists()


def test_claude_unreviewed_call_is_blocked_before_process():
    calls = []
    backend = CliAgentBackend(runner=lambda *args: calls.append(args))
    with pytest.raises(BackendError, match="Local-only"):
        backend.chat([{"role": "user", "content": "private"}])
    assert calls == []


def test_cli_model_flag_and_stdin_preserved():
    calls = []

    def runner(args, cwd, timeout, input_text=None):
        calls.append((args, input_text))
        return 0, json.dumps({"result": "reply"}), ""

    backend = CliAgentBackend(model="test-model", runner=runner, which=lambda name: "claude")
    request = build_reviewed_request(
        [{"role": "user", "content": "x" * 20_000}],
        recipient=backend.recipient,
    )
    backend.chat(request)
    argv, stdin = calls[0]
    assert argv[argv.index("--model") + 1] == "test-model"
    assert "x" * 20_000 in stdin
    assert all(len(arg) < 200 for arg in argv)


@pytest.mark.parametrize("cli", ["codex", "gemini"])
def test_unverified_cli_isolation_fails_closed(cli):
    calls = []
    backend = CliAgentBackend(cli=cli, runner=lambda *args: calls.append(args))
    assert backend.check()[0] is False
    request = build_reviewed_request(
        [{"role": "user", "content": "summary"}],
        recipient=backend.recipient,
    )
    with pytest.raises(BackendError, match="verified data-only"):
        backend.chat(request)
    assert calls == []


def test_is_hollow_model_detects_blank_cards() -> None:
    hollow = {
        "values": [],
        "life_goals": "",
        "communication_style": " ",
        "boundaries": "",
        "uncertainty_notes": "whatever",
    }
    assert is_hollow_model(hollow) is True
    assert is_hollow_model({**hollow, "values": ["honesty"]}) is False
    assert is_hollow_model({**hollow, "life_goals": "a quiet life"}) is False
    assert "nothing was" in HOLLOW_MODEL_DETAIL.lower()


def test_refine_rejects_hollow_model(monkeypatch, tmp_path) -> None:
    from fastapi import HTTPException

    from anti_dating_scam.api import routes_local_ai as mod

    class HollowBackend:
        name = "Fake"
        model = "fake"

        def chat(self, messages, system=None):
            return json.dumps(
                {
                    "values": [],
                    "life_goals": "",
                    "communication_style": "",
                    "boundaries": "",
                    "uncertainty_notes": "",
                }
            )

    # Point every vault path at tmp so the real home is never touched.
    for attr in (
        "VAULT_DIR",
        "SELF_MODEL_PATH",
        "SETTINGS_PATH",
        "NOTES_PATH",
        "PORTRAIT_MD_PATH",
        "PORTRAIT_JSON_PATH",
    ):
        monkeypatch.setattr(mod, attr, tmp_path / attr.lower())
    monkeypatch.setattr(mod, "_backend", HollowBackend())

    with pytest.raises(HTTPException) as excinfo:
        mod.refine(mod.ChatRequest(messages=[{"role": "user", "content": "go"}]))
    assert "empty self-model" in excinfo.value.detail
