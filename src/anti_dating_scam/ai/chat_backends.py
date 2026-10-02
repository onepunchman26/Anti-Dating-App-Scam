"""Shared connected-AI adapters; local-first and explicit reviewed disclosure."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from anti_dating_scam.ai.privacy import (
    BackendError,
    ChatRequest,
    coerce_request,
    outbound_messages,
    validate_local_url,
    validate_remote_url,
)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
HttpTransport = Callable[[str, dict[str, Any] | None, dict[str, str], float], dict[str, Any]]
CliRunner = Callable[..., tuple[int, str, str]]
CLI_ARG_SAFE_CHARS = 28_000


class ChatBackend(Protocol):
    name: str
    recipient: str

    def check(self) -> tuple[bool, str]: ...

    def chat(
        self, messages: ChatRequest | list[dict[str, str]], system: str | None = None
    ) -> str: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BackendError("AI endpoint redirects are blocked; verify the configured endpoint.")


def _default_http(
    url: str, payload: dict[str, Any] | None, headers: dict[str, str], timeout: float
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST" if payload is not None else "GET",
    )
    # Never disclose through a system proxy or a redirected destination.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise BackendError("AI provider response exceeded the size limit.")
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise BackendError("AI provider returned an invalid response object.")
            return data
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise BackendError(f"AI provider HTTP error ({status}).") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise BackendError("Could not reach the AI provider; check connection settings.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise BackendError("AI provider returned invalid JSON.") from None


def _default_cli(
    argv: list[str], cwd: str | None, timeout: float, input_text: str | None = None
) -> tuple[int, str, str]:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    completed = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        input=input_text,
        creationflags=creationflags,
    )
    return completed.returncode, completed.stdout or "", completed.stderr or ""


class OllamaChatBackend:
    name = "Ollama (local)"
    local = True

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: float = 300.0,
        transport: HttpTransport | None = None,
    ) -> None:
        self.base_url = validate_local_url(base_url)
        self.model, self.timeout = model, timeout
        self._http = transport or _default_http

    @property
    def recipient(self) -> str:
        return f"{validate_local_url(self.base_url)}/api/chat#{self.model}"

    def check(self) -> tuple[bool, str]:
        try:
            url = validate_local_url(self.base_url)
            data = self._http(f"{url}/api/tags", None, {}, 10.0)
            models = [entry.get("name", "") for entry in data.get("models", [])]
            if not models:
                return False, "Ollama is running but has no models. Run: ollama pull " + self.model
            if self.model not in models and f"{self.model}:latest" not in models:
                return False, "Ollama is running, but the selected model is not installed."
            return True, "Connected to Ollama; the selected local model is available."
        except BackendError as exc:
            return False, str(exc)
        except Exception:
            return False, "Could not inspect the local AI provider."

    def list_models(self) -> list[str]:
        try:
            url = validate_local_url(self.base_url)
            data = self._http(f"{url}/api/tags", None, {}, 10.0)
            return [entry["name"] for entry in data.get("models", []) if entry.get("name")]
        except Exception:
            return []

    def installed_chat_models(self) -> list[str]:
        """Prefer the smallest installed chat model; never auto-select embeddings/cloud."""
        try:
            url = validate_local_url(self.base_url)
            data = self._http(f"{url}/api/tags", None, {}, 10.0)
            suitable = []
            for entry in data.get("models", []):
                name = entry.get("name", "")
                family = (entry.get("details") or {}).get("family", "")
                combined = f"{name} {family}".lower()
                if not name or any(
                    word in combined
                    for word in (
                        "embed",
                        "bert",
                        "minilm",
                        "-cloud",
                        ":cloud",
                    )
                ):
                    continue
                size = entry.get("size", 0)
                suitable.append((size if isinstance(size, int) and size > 0 else 2**63, name))
            return [name for _size, name in sorted(suitable)]
        except Exception:
            return []

    def chat(self, messages: ChatRequest | list[dict[str, str]], system: str | None = None) -> str:
        request = coerce_request(messages, system)
        if "-cloud" in self.model.lower() or ":cloud" in self.model.lower():
            raise BackendError("Cloud-routed Ollama models are disabled in local-only mode.")
        url = validate_local_url(self.base_url)
        payload_messages = outbound_messages(request, recipient=self.recipient, local=True)
        if request.system:
            payload_messages.insert(0, {"role": "system", "content": request.system})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "stream": False,
            "options": {"num_ctx": 32768, "num_predict": 4096},
        }
        # These installed families support disabling separate thinking. Keep
        # delimiters and interview replies in content, never a thinking-only result.
        if self.model.lower().startswith(("qwen3", "deepseek-r1", "gemma4")):
            payload["think"] = False
        if request.response_schema is not None:
            payload["format"] = request.response_schema
            payload["think"] = False
            payload["options"]["temperature"] = 0
        try:
            try:
                data = self._http(f"{url}/api/chat", payload, {}, self.timeout)
            except BackendError as exc:
                if (
                    not request.allow_schema_fallback
                    or request.response_schema is None
                    or str(exc) != "AI provider HTTP error (400)."
                ):
                    raise
                # Some local runtimes reject otherwise valid JSON Schemas in
                # their grammar compiler. JSON syntax mode is a generation
                # fallback only: the original full application schema and
                # evidence validator remain mandatory before saving reports.
                payload = {**payload, "format": "json"}
                data = self._http(f"{url}/api/chat", payload, {}, self.timeout)
            content = (data.get("message") or {}).get("content", "")
        except BackendError:
            raise
        except Exception:
            raise BackendError("Local AI request failed; check provider settings.") from None
        if not isinstance(content, str) or not content.strip():
            raise BackendError("Ollama returned an empty or invalid reply.")
        return content


class AnthropicChatBackend:
    name = "Anthropic API"
    local = False

    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-sonnet-5",
        timeout: float = 300.0,
        transport: HttpTransport | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model, self.timeout = model, timeout
        self._http = transport or _default_http

    @property
    def recipient(self) -> str:
        return f"{ANTHROPIC_API_URL}#{self.model}"

    def check(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "No API key. Paste one (kept in memory only) or set ANTHROPIC_API_KEY."
        return True, "Key present; external calls require a reviewed minimal disclosure."

    def chat(self, messages: ChatRequest | list[dict[str, str]], system: str | None = None) -> str:
        request = coerce_request(messages, system)
        selected = outbound_messages(request, recipient=self.recipient, local=False)
        if not self.api_key:
            raise BackendError("No Anthropic API key configured.")
        payload: dict[str, Any] = {"model": self.model, "max_tokens": 4096, "messages": selected}
        if request.system:
            payload["system"] = request.system
        try:
            data = self._http(
                ANTHROPIC_API_URL,
                payload,
                {"x-api-key": self.api_key, "anthropic-version": ANTHROPIC_VERSION},
                self.timeout,
            )
            content = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            )
        except BackendError:
            raise
        except Exception:
            raise BackendError("External AI request failed; check provider settings.") from None
        if not content.strip():
            raise BackendError("Anthropic API returned no text content.")
        return content


class OpenAICompatChatBackend:
    name = "OpenAI-compatible API"
    local = False

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        model: str = "",
        timeout: float = 300.0,
        transport: HttpTransport | None = None,
    ) -> None:
        self.base_url = validate_remote_url(base_url)
        self.api_key, self.model, self.timeout = api_key, model, timeout
        self._http = transport or _default_http

    @property
    def recipient(self) -> str:
        return f"{validate_remote_url(self.base_url)}/chat/completions#{self.model}"

    def check(self) -> tuple[bool, str]:
        try:
            validate_remote_url(self.base_url)
        except BackendError as exc:
            return False, str(exc)
        if not self.api_key:
            return False, "No API key. Paste one (kept in memory only)."
        if not self.model:
            return False, "A model id is required."
        return True, "Key present; external calls require a reviewed minimal disclosure."

    def chat(self, messages: ChatRequest | list[dict[str, str]], system: str | None = None) -> str:
        request = coerce_request(messages, system)
        selected = outbound_messages(request, recipient=self.recipient, local=False)
        ok, detail = self.check()
        if not ok:
            raise BackendError(detail)
        if request.system:
            selected.insert(0, {"role": "system", "content": request.system})
        try:
            data = self._http(
                f"{self.base_url}/chat/completions",
                {"model": self.model, "messages": selected},
                {"Authorization": f"Bearer {self.api_key}"},
                self.timeout,
            )
            choices = data.get("choices") or []
            content = (choices[0].get("message") or {}).get("content", "") if choices else ""
        except BackendError:
            raise
        except Exception:
            raise BackendError("External AI request failed; check provider settings.") from None
        if not isinstance(content, str) or not content.strip():
            raise BackendError("The API returned no text content.")
        return content


class CliAgentBackend:
    """Data-only CLI calls; no vault mounts or persisted/resumed sessions.

    Claude's documented bare/tools flags disable discovery and agent tools.
    Other adapters fail closed until equivalent controls have been verified.
    """

    PRESETS = {
        "claude": "Claude Code (reviewed summary)",
        "codex": "Codex CLI (restricted)",
        "gemini": "Gemini CLI (restricted)",
    }
    local = False

    def __init__(
        self,
        cli: str = "claude",
        workdir: str | None = None,
        timeout: float = 600.0,
        runner: CliRunner | None = None,
        which: Callable[[str], str | None] | None = None,
        model: str = "",
    ) -> None:
        if cli not in self.PRESETS:
            raise BackendError("Unknown agent CLI.")
        self.cli, self.name = cli, self.PRESETS[cli]
        self.model_arg = (model or "").strip()
        if self.model_arg and not re.fullmatch(r"[A-Za-z0-9._:/-]{1,200}", self.model_arg):
            raise BackendError("CLI model name contains unsupported characters.")
        self.model = self.model_arg or cli
        # Compatibility metadata only. Never used as the child process cwd.
        self.workdir, self.timeout = workdir, timeout
        self.extra_dirs: list[str] = []
        self._run, self._which = runner or _default_cli, which or shutil.which

    @property
    def recipient(self) -> str:
        return f"cli:{self.cli}#{self.model}"

    def _exe(self) -> str:
        exe = self._which(self.cli)
        if not exe:
            raise BackendError("Agent CLI not found on PATH; select a local model or configure it.")
        return exe

    def _argv(self, rest: list[str]) -> list[str]:
        exe = self._exe()
        if exe.lower().endswith((".cmd", ".bat")):
            if any(character in exe for character in '&|<>^%!\r\n"'):
                raise BackendError(
                    "Use a native CLI executable or a path without shell characters."
                )
            return ["cmd", "/d", "/c", exe, *rest]
        return [exe, *rest]

    def check(self) -> tuple[bool, str]:
        if self.cli != "claude":
            return (
                False,
                "This CLI lacks verified data-only isolation; use a local or reviewed API.",
            )
        try:
            code, _out, _err = self._run(self._argv(["--version"]), None, 30.0)
        except BackendError as exc:
            return False, str(exc)
        except Exception:
            return False, "Agent CLI failed to start."
        if code != 0:
            return False, "Agent CLI version check failed."
        return True, "CLI installed; no model call made. Each call needs reviewed disclosure."

    def chat(self, messages: ChatRequest | list[dict[str, str]], system: str | None = None) -> str:
        request = coerce_request(messages, system)
        selected = outbound_messages(request, recipient=self.recipient, local=False)
        if self.cli != "claude":
            raise BackendError("This CLI lacks verified data-only isolation; use a reviewed API.")
        if self.extra_dirs:
            raise BackendError("External CLI directory access is disabled.")
        prompt = json.dumps({"conversation_data": selected}, ensure_ascii=False)
        flags = [
            "--print",
            "--output-format",
            "json",
            "--bare",
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--no-session-persistence",
            "--setting-sources",
            "",
            "--system-prompt-file",
            "instructions.txt",
        ]
        if self.model_arg:
            flags += ["--model", self.model_arg]
        try:
            argv = self._argv(flags)
            with tempfile.TemporaryDirectory(prefix="slowmatch-ai-") as isolated:
                Path(isolated, "instructions.txt").write_text(
                    request.system or "Reply to the user's reviewed conversation data.",
                    encoding="utf-8",
                )
                code, out, _err = self._run(argv, isolated, self.timeout, prompt)
            if code != 0:
                raise BackendError("Agent CLI request failed; check its installation and sign-in.")
            data = json.loads(out)
            result = data.get("result", "")
            if data.get("is_error") or not isinstance(result, str) or not result.strip():
                raise BackendError("Agent CLI returned an empty or invalid result.")
            return result
        except BackendError:
            raise
        except Exception:
            raise BackendError(
                "Agent CLI request failed; no provider diagnostics were disclosed."
            ) from None
