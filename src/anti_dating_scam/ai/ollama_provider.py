"""Local-first Ollama adapter.

Recommended default AI path per `docs/10_data_import_and_frontend_plan.md`: self-portrait
and risk-analysis narration should run on the user's own machine against a local model
rather than a cloud API, so imported chat/social data never has to leave the device.

This module only talks to loopback Ollama origins. Overriding `base_url` cannot
change that boundary; remote origins, cloud model names, proxies and redirects fail closed.
No network call happens unless a caller explicitly constructs and uses this client; the
default provider used elsewhere in the app remains `MockAIProvider`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from anti_dating_scam.ai.chat_backends import _default_http
from anti_dating_scam.ai.privacy import BackendError, validate_local_url
from anti_dating_scam.ai.provider import LLMClient

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama server cannot be reached or returns an error.

    Deliberately not swallowed into a fake success response: silently pretending a
    local-model call succeeded when it didn't would hide the model's actual
    availability status from the user, which conflicts with this project's
    uncertainty-aware-by-default design.
    """


@dataclass
class OllamaResult:
    raw_text: str
    parsed_json: dict[str, Any] | None
    model: str


# A transport is any callable that takes (url, payload_dict, timeout_seconds) and
# returns the decoded JSON response body as a dict. Tests inject a fake transport so
# no real network access is required; production code uses `_default_transport`.
Transport = Callable[[str, dict[str, Any], float], dict[str, Any]]


def _default_transport(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    # Share the existing proxy-free, no-redirect, bounded-response transport.
    try:
        return _default_http(url, payload, {}, timeout)
    except BackendError as exc:
        raise OllamaUnavailableError(str(exc)) from None


def _local_origin(value: str) -> str:
    try:
        return validate_local_url(value)
    except BackendError as exc:
        raise OllamaUnavailableError(str(exc)) from None


class OllamaClient:
    """Thin wrapper around Ollama's `/api/generate` endpoint.

    Kept deliberately dependency-free (stdlib `urllib` only) so adding local-model
    support does not pull in a new third-party HTTP dependency.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout: float = 60.0,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = _local_origin(base_url)
        self.model = model
        self.timeout = timeout
        self._transport = transport or _default_transport

    def generate(self, prompt: str, *, json_mode: bool = True) -> OllamaResult:
        url = _local_origin(self.base_url)
        if not isinstance(self.model, str) or not self.model.strip():
            raise OllamaUnavailableError("Select an installed local Ollama model.")
        if "-cloud" in self.model.lower() or ":cloud" in self.model.lower():
            raise OllamaUnavailableError(
                "Cloud-routed Ollama models are disabled in local-only mode."
            )
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        try:
            response = self._transport(f"{url}/api/generate", payload, self.timeout)
        except OllamaUnavailableError:
            raise
        except Exception:
            raise OllamaUnavailableError(
                "Local Ollama request failed; check the local model and connection settings."
            ) from None
        if not isinstance(response, dict) or not isinstance(response.get("response"), str):
            raise OllamaUnavailableError("Local Ollama returned an invalid response object.")
        raw_text = response.get("response", "")
        parsed: dict[str, Any] | None = None
        if json_mode and raw_text:
            try:
                parsed = json.loads(raw_text)
                if not isinstance(parsed, dict):
                    parsed = None
            except json.JSONDecodeError:
                parsed = None
        return OllamaResult(raw_text=raw_text, parsed_json=parsed, model=self.model)


class OllamaAIProvider(LLMClient):
    """`LLMClient` adapter so services (e.g. `ScamRiskAnalyzer`) can use Ollama exactly
    like they use `MockAIProvider`, with no service-layer code changes required.
    """

    name = "Ollama"

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    def generate_structured(self, prompt: str, schema_name: str) -> dict[str, Any]:
        result = self.client.generate(prompt, json_mode=True)
        return {
            "schema_name": schema_name,
            "provider": "ollama",
            "model": self.client.model,
            "summary": (
                result.parsed_json.get("summary")
                if isinstance(result.parsed_json, dict) and "summary" in result.parsed_json
                else "Local Ollama provider output. Review before relying on it."
            ),
            "structured_output": result.parsed_json,
            "raw_text": result.raw_text,
            "prompt_preview": prompt[:160],
        }
