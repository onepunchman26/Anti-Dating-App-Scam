"""Synthetic isolation, consent and completed-turn boundaries; no account access."""

import json
import queue
import threading
import time
from types import SimpleNamespace

import pytest

from anti_dating_scam.ai.codex_connection import (
    CodexConnectionService,
    CodexRPC,
    isolated_config,
    isolated_environment,
)
from anti_dating_scam.ai.privacy import BackendError, build_reviewed_request


class RPC:
    def __init__(self, home, work):
        self.home, self.work = home, work
        self.calls = []
        self.events = []
        self.closed = False
        self.account = {"type": "chatgpt"}
        self.allowed = True
        self.instruction_sources = []
        self.actual_model = "synthetic-luna"
        self.cleanup_fails = False
        self.terminal = "completed"
        self.item = {"type": "agentMessage", "phase": "final_answer", "text": "Synthetic reply"}

    def call(self, method, params, **kwargs):
        self.calls.append((method, params))
        if method == "account/read":
            return {"account": self.account}
        if method == "account/login/start":
            self.events.append(
                {
                    "method": "account/login/completed",
                    "params": {
                        "loginId": "synthetic",
                        "success": True,
                    },
                }
            )
            self.account = {"type": "chatgpt"}
            return {"loginId": "synthetic", "authUrl": "https://auth.openai.com/authorize"}
        if method == "model/list":
            return {
                "data": [
                    {"model": "synthetic-luna", "displayName": "Synthetic Luna", "hidden": False}
                ]
            }
        if method == "account/rateLimits/read":
            return {"ordinaryUsageAllowed": self.allowed}
        if method == "thread/start":
            return {
                "thread": {"id": "thread"},
                "model": self.actual_model,
                "instructionSources": self.instruction_sources,
            }
        if method == "turn/start":
            self.events.extend(
                [
                    {
                        "method": "item/completed",
                        "params": {"threadId": "thread", "turnId": "turn", "item": self.item},
                    },
                    {
                        "method": "turn/completed",
                        "params": {
                            "threadId": "thread",
                            "turn": {"id": "turn", "status": self.terminal},
                        },
                    },
                ]
            )
            return {"turn": {"id": "turn"}}
        if method == "thread/unsubscribe" and self.cleanup_fails:
            raise BackendError("Synthetic cleanup failure")
        return {}

    def event(self, deadline, cancel=None):
        if cancel and cancel.is_set():
            raise BackendError("Stopped", category="cancelled")
        return self.events.pop(0)

    def close(self):
        self.closed = True


@pytest.fixture
def connected(tmp_path):
    service = CodexConnectionService(directory=tmp_path, rpc_factory=RPC)
    service.connect()
    yield service
    service.close()


def reviewed(backend):
    return build_reviewed_request(
        [{"role": "user", "content": "Synthetic relationship reflection."}],
        system="Use only this supplied text.",
        recipient=backend.recipient,
    )


def test_completed_answer_survives_cleanup_failure(connected):
    rpc = connected._rpc
    rpc.cleanup_fails = True
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    answer = backend.chat_result(reviewed(backend))
    assert answer.text == "Synthetic reply"
    assert answer.provenance.reported_model is None
    assert answer.provenance.completion == "completed"
    assert not connected.status().connected
    assert rpc.closed
    assert "thread/unload" not in [method for method, _ in rpc.calls]


def test_reviewed_data_only_ephemeral_request(connected):
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    request = reviewed(backend)
    backend.chat_result(request)
    calls = dict(connected._rpc.calls)
    assert calls["thread/start"]["ephemeral"] is True
    assert calls["thread/start"]["baseInstructions"] == request.system
    assert calls["thread/start"]["approvalPolicy"] == "never"
    assert json.loads(calls["turn/start"]["input"][0]["text"]) == {
        "reviewed_messages": [{"role": "user", "content": "Synthetic relationship reflection."}],
    }
    assert "thread/unsubscribe" in calls
    assert not any(method in calls for method in ("thread/resume", "thread/fork", "fs/readFile"))


@pytest.mark.parametrize("allowed", [False, None, 1, "true"])
def test_unknown_or_exhausted_allowance_never_infers(connected, allowed):
    connected._rpc.allowed = allowed
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    with pytest.raises(BackendError, match="Included plan"):
        backend.chat_result(reviewed(backend))
    assert "turn/start" not in dict(connected._rpc.calls)


def test_separate_plan_consent_and_exact_disclosure_required(connected):
    backend = connected.create_backend("synthetic-luna")
    with pytest.raises(BackendError, match="credits"):
        backend.chat_result(reviewed(backend))
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    with pytest.raises(BackendError, match="Local-only"):
        backend.chat([{"role": "user", "content": "Synthetic"}])
    wrong = reviewed(backend)
    wrong = wrong.model_copy(
        update={
            "disclosure": wrong.disclosure.model_copy(update={"recipient": "another-provider"}),
        }
    )
    with pytest.raises(BackendError, match="Disclosure changed"):
        backend.chat_result(wrong)
    assert "turn/start" not in dict(connected._rpc.calls)


def test_account_change_and_model_mismatch_block(connected):
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    connected.connect()
    with pytest.raises(BackendError, match="Reconnect"):
        backend.chat_result(reviewed(backend))
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    connected._rpc.actual_model = "another-model"
    rpc = connected._rpc
    with pytest.raises(BackendError, match="Unexpected model"):
        backend.chat_result(reviewed(backend))
    assert "turn/start" not in dict(rpc.calls)
    assert rpc.closed


def test_external_instruction_files_block_before_inference(connected):
    connected._rpc.instruction_sources = ["synthetic-unapproved-AGENTS.md"]
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    rpc = connected._rpc
    with pytest.raises(BackendError, match="file context"):
        backend.chat_result(reviewed(backend))
    assert "turn/start" not in dict(rpc.calls)


@pytest.mark.parametrize(
    "terminal,text", [("failed", "reply"), ("interrupted", "reply"), ("completed", " ")]
)
def test_failed_interrupted_and_empty_turns_are_not_success(connected, terminal, text):
    connected._rpc.terminal = terminal
    connected._rpc.item["text"] = text
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    with pytest.raises(BackendError):
        backend.chat_result(reviewed(backend))


def test_cancelled_request_never_starts_turn(connected):
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    cancel = threading.Event()
    cancel.set()
    backend.set_cancel_event(cancel)
    with pytest.raises(BackendError) as failure:
        backend.chat_result(reviewed(backend))
    assert failure.value.category == "cancelled"
    assert "turn/start" not in dict(connected._rpc.calls)


def test_unexpected_tool_item_closes_connection(connected):
    rpc = connected._rpc
    rpc.item = {"type": "commandExecution"}
    backend = connected.create_backend("synthetic-luna", included_plan_confirmed=True)
    with pytest.raises(BackendError, match="tool activity"):
        backend.chat_result(reviewed(backend))
    assert rpc.closed


def test_server_tool_requests_are_denied_and_closed():
    rpc = CodexRPC.__new__(CodexRPC)
    rpc._queue = queue.Queue()
    rpc._queue.put({"id": 1, "method": "item/commandExecution/requestApproval", "params": {}})
    sent, closed = [], []
    rpc.send = sent.append
    rpc.close = lambda: closed.append(True)
    with pytest.raises(BackendError, match="tool request"):
        rpc.receive(time.monotonic() + 1)
    assert sent[0]["error"]["code"] == -32601
    assert closed == [True]


def test_no_inherited_secrets_or_discovery(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-secret")
    monkeypatch.setenv("CODEX_HOME", "unapproved-home")
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    environment = isolated_environment(tmp_path)
    assert environment["CODEX_HOME"] == str(tmp_path)
    assert "OPENAI_API_KEY" not in environment and "GITHUB_TOKEN" not in environment
    settings = isolated_config()
    assert settings["cli_auth_credentials_store"] == "keyring"
    assert settings["features.shell_tool"] is False
    assert settings["features.view_image"] is False
    assert settings["features.skip_host_skill_discovery"] is True
    assert settings["skills.bundled.enabled"] is False
    assert settings["web_search"] == "disabled"


def test_dead_child_reconnects_in_one_attempt(connected):
    old = connected._rpc
    old.process = SimpleNamespace(poll=lambda: 1)
    assert not connected.status().connected
    connected.connect()
    assert connected.status().connected and old.closed
    assert connected._rpc is not old


def test_disconnect_after_restart_removes_owned_persisted_login(tmp_path):
    made = []

    def factory(home, work):
        rpc = RPC(home, work)
        made.append(rpc)
        return rpc

    connection = CodexConnectionService(directory=tmp_path, rpc_factory=factory)
    assert connection.disconnect() is True
    assert "account/logout" in dict(made[0].calls)
    assert made[0].closed


@pytest.mark.parametrize("code", ["runtime_missing", "runtime_version"])
def test_runtime_diagnostic_is_specific_and_contains_no_raw_error(tmp_path, code):
    def factory(*args):
        raise BackendError("synthetic untrusted detail", category=code)

    connection = CodexConnectionService(directory=tmp_path, rpc_factory=factory)
    with pytest.raises(BackendError):
        connection.connect()
    assert connection.diagnostic().code == code
    assert "untrusted" not in str(connection.diagnostic())


@pytest.mark.parametrize("language", ["en", "zh"])
def test_ui_route_switch_clears_consent_and_active_provider(connected, monkeypatch, language):
    from anti_dating_scam_desktop import ai_backend
    from anti_dating_scam_desktop.i18n import current_language, set_language
    from anti_dating_scam_desktop.screens.chatgpt_connect_screen import ChatGPTConnectScreen
    from PySide6.QtWidgets import QApplication

    from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionStatus

    app = QApplication.instance() or QApplication([])
    previous = current_language()
    set_language(language)
    direct = SimpleNamespace(status=lambda: ChatGPTConnectionStatus())
    screen = ChatGPTConnectScreen(None, None, lambda: None, lambda: None, connection=direct)
    # Avoid starting real workers; connection already has synthetic status.
    screen._compat_connection = connected
    screen._load_models = lambda: None
    try:
        screen.plan_consent.setChecked(True)
        ai_backend.set_active(object())
        screen._switch_connection()
        assert screen.connection is connected
        assert not screen.plan_consent.isChecked()
        assert ai_backend.get_active() is None
        assert "Codex" in screen.plan_consent.text()
        screen._switch_connection()
        assert screen.connection is direct
        assert not screen.plan_consent.isChecked()
    finally:
        screen.close()
        set_language(previous)
        app.processEvents()
