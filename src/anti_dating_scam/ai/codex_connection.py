"""Isolated official Codex app-server connection for a local desktop application.

No existing Codex home, tokens, sessions, skills or workspace are opened. Only the
audited executable version is supported. Tools and context discovery are disabled.
Managed OAuth belongs to this application's separate home and Windows keyring.
"""

from __future__ import annotations

import atexit
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import webbrowser
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from anti_dating_scam.ai.chatgpt_auth import (
    ChatGPTConnectionDiagnostic,
    ChatGPTConnectionStatus,
    ChatGPTModelChoice,
)
from anti_dating_scam.ai.privacy import BackendError, coerce_request, outbound_messages
from anti_dating_scam.ai.results import AIProvenance, ChatResult

AUDITED_VERSION = "codex-cli 0.163.0-alpha.10.2"
AUDITED_VERSIONS = {AUDITED_VERSION, "codex-cli 0.162.0-alpha.17.2"}
DISABLED_FEATURES = tuple(
    "shell_tool apply_patch_freeform unified_exec view_image apps plugins collab "
    "multi_agent multi_agent_v2 code_mode js_repl memories shell_snapshot remote_models "
    "tool_search skill_search image_generation computer_use browser_use hooks codex_hooks "
    "plugin_hooks goals request_permissions_tool responses_websockets responses_websockets_v2 "
    "enable_request_compression connectors search_tool standalone_web_search tool_suggest "
    "external_agent_memory_import external_migration network_proxy worktrees".split()
)
MAX_LINE_BYTES = 2_000_000


def isolated_config() -> dict:
    return {
        "cli_auth_credentials_store": "keyring",
        "web_search": "disabled",
        "agents.enabled": False,
        "analytics.enabled": False,
        "feedback.enabled": False,
        "history.persistence": "none",
        "features.skip_host_skill_discovery": True,
        "include_environment_context": False,
        "include_apps_instructions": False,
        "include_collaboration_mode_instructions": False,
        "include_permissions_instructions": False,
        "skills.bundled.enabled": False,
        "skills.include_instructions": False,
        "project_doc_max_bytes": 0,
        **{f"features.{name}": False for name in DISABLED_FEATURES},
    }


def isolated_environment(home: Path) -> dict[str, str]:
    allowed = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP", "COMSPEC"}
    result = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    result.update(
        {k: str(home) for k in ("CODEX_HOME", "USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA")}
    )
    return result


def find_codex() -> Path:
    # Executables only; never search/read another application's auth or settings.
    roots = {
        Path(os.environ.get("LOCALAPPDATA", Path.home())) / "OpenAI/Codex/bin",
        Path.home() / "AppData/Local/OpenAI/Codex/bin",
    }
    for root in sorted(roots):
        for candidate in sorted(root.glob("*/codex.exe"), reverse=True):
            if candidate.is_file() and not candidate.is_symlink():
                return candidate
    # The official installer also exposes its executable on PATH. This keeps
    # discovery working when the desktop app uses an isolated profile directory.
    installed = shutil.which("codex.exe")
    if installed and not Path(installed).is_symlink():
        return Path(installed)
    raise BackendError(
        "The compatible local Codex runtime was not found. / 未找到兼容的本机 Codex 程序。",
        category="runtime_missing",
    )


class CodexRPC:
    """One private stdio process. A serialized caller owns all responses/events."""

    def __init__(self, home: Path, work: Path, *, executable: Path | None = None, config=None):
        self.work = work
        executable = executable or find_codex()
        environment = isolated_environment(home)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        version = subprocess.run(
            [str(executable), "--version"],
            env=environment,
            cwd=work,
            capture_output=True,
            timeout=10,
            creationflags=flags,
            check=False,
        )
        if (
            version.returncode
            or version.stdout.decode("utf-8", "replace").strip() not in AUDITED_VERSIONS
        ):
            raise BackendError(
                "This Codex version needs a compatibility check before use. / "
                "此 Codex 版本需要完成兼容检查后才能使用。",
                category="runtime_version",
            )
        args = [str(executable), "app-server", "--stdio"]
        for key, value in (config or isolated_config()).items():
            args.extend(["-c", key + "=" + json.dumps(value)])
        self.process = subprocess.Popen(
            args,
            cwd=work,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        self._queue = queue.Queue(maxsize=1000)
        self._pending = deque(maxlen=1000)
        self._sequence = 0
        self._closed = threading.Event()

        def reader():
            try:
                while not self._closed.is_set():
                    line = self.process.stdout.readline(MAX_LINE_BYTES + 1)
                    if not line or len(line) > MAX_LINE_BYTES:
                        break
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        break
                    self._queue.put(value, timeout=1)
            except (OSError, ValueError, queue.Full):
                pass
            finally:
                try:
                    self._queue.put(None, timeout=1)
                except queue.Full:
                    pass

        self._reader = threading.Thread(target=reader, daemon=True)
        self._reader.start()
        try:
            self.call(
                "initialize",
                {
                    "clientInfo": {
                        "name": "slowmatch_local_chat",
                        "title": "AI-SlowMatch",
                        "version": "1",
                    }
                },
            )
            self.send({"method": "initialized"})
        except Exception:
            self.close()
            raise

    def send(self, message):
        try:
            self.process.stdin.write((json.dumps(message, ensure_ascii=False) + "\n").encode())
            self.process.stdin.flush()
        except (OSError, ValueError):
            raise BackendError(
                "Reconnect the local connection. / 请重新连接。", category="auth"
            ) from None

    def receive(self, deadline, cancel=None):
        while time.monotonic() < deadline:
            if cancel is not None and cancel.is_set():
                raise BackendError("Request stopped. / 请求已停止。", category="cancelled")
            try:
                item = self._queue.get(timeout=min(0.1, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                continue
            if item is None:
                raise BackendError("Local connection ended. / 本地连接已结束。", category="network")
            if "method" in item and "id" in item:
                # No command, permission, tool or external elicitation is ever accepted.
                self.send(
                    {
                        "id": item["id"],
                        "error": {
                            "code": -32601,
                            "message": "External operations are unavailable.",
                        },
                    }
                )
                self.close()
                raise BackendError("Unexpected tool request was blocked. / 已阻止意外工具请求。")
            return item
        raise BackendError("Local connection timed out. / 本地连接超时。", category="timeout")

    def call(self, method, params, *, timeout=30, cancel=None):
        self._sequence += 1
        ident = self._sequence
        self.send({"id": ident, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            item = self.receive(deadline, cancel)
            if item.get("id") == ident:
                if "error" in item or not isinstance(item.get("result"), dict):
                    raise BackendError("Local ChatGPT request failed. / 本地 ChatGPT 请求失败。")
                return item["result"]
            if len(self._pending) >= self._pending.maxlen:
                self.close()
                raise BackendError("Too many connection events. / 连接事件超出限制。")
            self._pending.append(item)

    def event(self, deadline, cancel=None):
        if cancel is not None and cancel.is_set():
            raise BackendError("Request stopped. / 请求已停止。", category="cancelled")
        if time.monotonic() >= deadline:
            raise BackendError("Request timed out. / 请求超时。", category="timeout")
        return self._pending.popleft() if self._pending else self.receive(deadline, cancel)

    def close(self):
        self._closed.set()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()


class CodexConnectionService:
    """Same UI contract as sign-in, with explicit separate Codex plan consent."""

    provider_id = "codex_chatgpt"
    compatibility = True
    preference_key = "codex-local-connection"

    def __init__(self, *, directory=None, rpc_factory=CodexRPC, browser_open=webbrowser.open):
        self.directory = directory or (
            Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AI-SlowMatch/codex-chat"
        )
        self._factory, self._browser = rpc_factory, browser_open
        self._rpc = None
        self._temporary = None
        self._lock = threading.RLock()
        self._binding = ""
        self._diagnostic = ChatGPTConnectionDiagnostic()
        atexit.register(self.close)

    def diagnostic(self):
        return self._diagnostic

    def status(self):
        process = getattr(self._rpc, "process", None)
        alive = process is None or process.poll() is None
        connected = bool(self._binding and self._rpc and alive)
        return ChatGPTConnectionStatus(
            connected=connected,
            sharing=connected,
            client_id=self._binding,
            label="ChatGPT via local Codex" if connected else "",
        )

    def _start(self):
        if self._rpc is not None:
            process = getattr(self._rpc, "process", None)
            if process is None or process.poll() is None:
                return self._rpc
            self.close()
        self.directory.mkdir(parents=True, exist_ok=True)
        home = self.directory / "home"
        home.mkdir(exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(prefix="session-", dir=self.directory)
        work = Path(self._temporary.name)
        try:
            self._rpc = self._factory(home, work)
        except Exception:
            self._temporary.cleanup()
            self._temporary = None
            raise
        return self._rpc

    def connect(self, *, cancel_event=None):
        with self._lock:
            try:
                rpc = self._start()
                account = rpc.call("account/read", {"refreshToken": False}).get("account")
                if account is None:
                    login = rpc.call("account/login/start", {"type": "chatgpt"})
                    url = login.get("authUrl", "")
                    parsed = urlsplit(url)
                    if (
                        parsed.scheme != "https"
                        or parsed.hostname != "auth.openai.com"
                        or parsed.username
                        or parsed.password
                        or parsed.port not in {None, 443}
                    ):
                        raise BackendError("Invalid official login destination. / 登录地址无效。")
                    self._diagnostic = ChatGPTConnectionDiagnostic(phase="waiting_callback")
                    if not self._browser(url):
                        raise BackendError("Open the browser to sign in. / 无法打开浏览器登录。")
                    deadline = time.monotonic() + 300
                    while True:
                        event = rpc.event(deadline, cancel_event)
                        if event.get("method") != "account/login/completed":
                            continue
                        result = event.get("params", {})
                        if result.get("loginId") != login.get("loginId"):
                            continue
                        if result.get("success") is not True:
                            raise BackendError(
                                "Sign-in did not complete. / 登录未完成。", category="auth"
                            )
                        break
                    account = rpc.call("account/read", {"refreshToken": False}).get("account")
                if not isinstance(account, dict) or account.get("type") != "chatgpt":
                    raise BackendError(
                        "Use a ChatGPT plan login. / 请用 ChatGPT 套餐登录。", category="auth"
                    )
                self._binding = "codex-" + uuid4().hex
                self._diagnostic = ChatGPTConnectionDiagnostic(phase="connected")
                return self.status()
            except Exception as error:
                self.close()
                self._diagnostic = ChatGPTConnectionDiagnostic(
                    phase="failed",
                    code=(
                        error.category if isinstance(error, BackendError) else "connection_failed"
                    ),
                )
                raise

    def list_models(self):
        with self._lock:
            if not self.status().connected:
                raise BackendError("Connect first. / 请先连接。", category="auth")
            self._diagnostic = ChatGPTConnectionDiagnostic(phase="loading_models")
            try:
                result = self._rpc.call("model/list", {"includeHidden": False, "limit": 100})
            except BackendError:
                self._diagnostic = ChatGPTConnectionDiagnostic(
                    phase="failed", code="catalog_request_failed"
                )
                raise
            rows = result.get("data")
            if (
                not isinstance(rows, list)
                or len(rows) > 500
                or result.get("nextCursor")
                or any(not isinstance(row, dict) for row in rows)
            ):
                raise BackendError("Unsupported model catalog. / 模型列表不受支持。")
            models = tuple(
                ChatGPTModelChoice(slug=row["model"], display_name=row["displayName"])
                for row in rows
                if row.get("hidden") is False
            )
            if len({m.slug for m in models}) != len(models):
                raise BackendError("Ambiguous model catalog. / 模型列表重复。")
            self._diagnostic = ChatGPTConnectionDiagnostic(phase="models_ready")
            return models

    def create_backend(self, model, *, included_plan_confirmed=False):
        return CodexChatBackend(self, model, included_plan_confirmed=included_plan_confirmed)

    def disconnect(self):
        with self._lock:
            try:
                # Logout must also clear this app's persisted login after restart.
                self._start().call("account/logout", {})
            finally:
                self.close()
            return True

    def close(self):
        with self._lock:
            self._binding = ""
            if self._rpc:
                self._rpc.close()
                self._rpc = None
            if self._temporary:
                self._temporary.cleanup()
                self._temporary = None


class CodexChatBackend:
    local = False
    name = "ChatGPT via local Codex"
    provider_id = "codex_chatgpt"

    def __init__(self, connection, model, *, included_plan_confirmed=False, timeout=180):
        ChatGPTModelChoice(slug=model, display_name=model)
        if type(included_plan_confirmed) is not bool:
            raise BackendError("Explicit plan confirmation is required. / 请明确确认套餐设置。")
        self.connection, self.model = connection, model
        self._confirmed, self.timeout = included_plan_confirmed, timeout
        self._binding = connection.status().client_id
        self._cancel = None

    @property
    def recipient(self):
        return "codex-app-server://chatgpt/" + self.model

    def set_cancel_event(self, event):
        self._cancel = event

    def chat(self, messages, system=None):
        return self.chat_result(messages, system).text

    def chat_result(self, messages, system=None):
        request = coerce_request(messages, system)
        selected = outbound_messages(request, recipient=self.recipient, local=False)
        if self._confirmed is not True:
            raise BackendError(
                "Confirm Codex extra credits are off. / 请确认 Codex 额外积分已关闭。"
            )
        cancel = self._cancel
        with self.connection._lock:
            if not self._binding or self.connection.status().client_id != self._binding:
                raise BackendError(
                    "Reconnect the selected account. / 请重新连接。", category="auth"
                )
            if cancel is not None and cancel.is_set():
                raise BackendError("Request stopped. / 请求已停止。", category="cancelled")
            if self.model not in {m.slug for m in self.connection.list_models()}:
                raise BackendError(
                    "Choose an available model. / 请选择可用模型。", category="model"
                )
            rpc = self.connection._rpc
            limits = rpc.call("account/rateLimits/read", {}, cancel=cancel)
            if limits.get("ordinaryUsageAllowed") is not True:
                raise BackendError(
                    "Included plan usage is unavailable. / 套餐额度不可用。", category="usage"
                )
            thread = rpc.call(
                "thread/start",
                {
                    "model": self.model,
                    "cwd": str(rpc.work),
                    "ephemeral": True,
                    "baseInstructions": request.system,
                    "developerInstructions": "",
                    "sandbox": "read-only",
                    "approvalPolicy": "never",
                    "config": {"include_environment_context": False, "project_doc_max_bytes": 0},
                },
                cancel=cancel,
            )
            if thread.get("instructionSources") or thread.get("model") != self.model:
                self.connection.close()
                raise BackendError(
                    "Unexpected model or file context blocked. / 已阻止意外模型或文件上下文。"
                )
            thread_id = thread["thread"]["id"]
            try:
                params = {
                    "threadId": thread_id,
                    "input": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"reviewed_messages": selected},
                                ensure_ascii=False,
                            ),
                        }
                    ],
                    "effort": "low",
                    "serviceTierForTurn": "default",
                }
                if request.response_schema is not None:
                    params["outputSchema"] = request.response_schema
                turn = rpc.call("turn/start", params, cancel=cancel)
                turn_id = turn["turn"]["id"]
                deadline = time.monotonic() + self.timeout
                replies = []
                while True:
                    event = rpc.event(deadline, cancel)
                    data = event.get("params", {})
                    if data.get("threadId") != thread_id:
                        continue
                    if event.get("method") == "item/completed" and data.get("turnId") == turn_id:
                        item = data["item"]
                        if item.get("type") not in {"userMessage", "agentMessage", "reasoning"}:
                            self.connection.close()
                            raise BackendError(
                                "Unexpected tool activity blocked. / 已阻止意外工具活动。"
                            )
                        if item.get("type") == "agentMessage" and item.get("phase") in {
                            None,
                            "final_answer",
                        }:
                            text = item.get("text")
                            if not isinstance(text, str):
                                raise BackendError("Invalid chat reply. / 聊天回复无效。")
                            replies.append(text)
                            if sum(map(len, replies)) > 256_000:
                                raise BackendError("Chat reply is too large. / 聊天回复超出限制。")
                    if (
                        event.get("method") == "turn/completed"
                        and data.get("turn", {}).get("id") == turn_id
                    ):
                        completed = data["turn"]
                        if completed.get("status") != "completed" or completed.get("error"):
                            raise BackendError(
                                "ChatGPT did not complete the answer. / ChatGPT 未完成回复。"
                            )
                        if not "".join(replies).strip():
                            raise BackendError("ChatGPT returned no answer. / ChatGPT 未返回回答。")
                        return ChatResult(
                            text="".join(replies),
                            provenance=AIProvenance(
                                provider=self.provider_id,
                                requested_model=self.model,
                                # app-server does not report the upstream response model ID here.
                                reported_model=None,
                            ),
                        )
            except BackendError as error:
                if error.category in {"cancelled", "timeout"}:
                    self.connection.close()
                raise
            except Exception:
                raise BackendError(
                    "ChatGPT reply could not be read. / 无法读取 ChatGPT 回复。"
                ) from None
            finally:
                if self.connection._rpc is rpc:
                    try:
                        rpc.call("thread/unsubscribe", {"threadId": thread_id}, timeout=5)
                    except BackendError:
                        # Cleanup must never turn an already completed reply into a failure.
                        self.connection.close()
