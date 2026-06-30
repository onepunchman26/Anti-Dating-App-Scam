"""Local-first Ollama adapter.

Recommended default AI path per `docs/10_data_import_and_frontend_plan.md`: self-portrait
and risk-analysis narration should run on the user's own machine against a local model
rather than a cloud API, so imported chat/social data never has to leave the device.

This module only talks to `http://localhost:11434` (Ollama's default bind, local-only)
unless the caller explicitly overrides `base_url` — never default to a non-local host.
No network call happens unless a caller explicitly constructs and uses this client; the
default provider used elsewhere in the app remains `MockAIProvider`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise OllamaUnavailableError(
            "Could not reach the local Ollama server at "
            f"{url}. Make sure Ollama is installed and running (`ollama serve`), "
            "or switch to a different provider in Settings."
        ) from exc
    except json.JSONDecodeError as exc:
        raise OllamaUnavailableError(
            "Ollama returned a response that was not valid JSON."
        ) from exc


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
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._transport = transport or _default_transport

    def generate(self, prompt: str, *, json_mode: bool = True) -> OllamaResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        response = self._transport(f"{self.base_url}/api/generate", payload, self.timeout)
        raw_text = response.get("response", "")
        parsed: dict[str, Any] | None = None
        if json_mode and raw_text:
            try:
                parsed = json.loads(raw_text)
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
