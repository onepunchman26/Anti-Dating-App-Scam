"""`AIProvider` adapter for the local Ollama client.

Separate from `anti_dating_scam.ai.ollama_provider.OllamaAIProvider`: that one
implements the `LLMClient` protocol (`generate_structured`) used by services like
`ScamRiskAnalyzer`. This one implements the `AIProvider` protocol (`.analyze`) used by
`providers/registry.py` and the desktop Settings screen's provider picker. Both wrap
the same underlying `OllamaClient` so there is a single real HTTP-call implementation.
"""

from __future__ import annotations

from typing import Any

from anti_dating_scam.ai.ollama_provider import (
    OllamaClient,
    OllamaUnavailableError,
)


class OllamaAIProviderAdapter:
    name = "Ollama"

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    def analyze(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            result = self.client.generate(prompt, json_mode=True)
        except OllamaUnavailableError as exc:
            return {
                "provider": self.name,
                "model": self.client.model,
                "output": {
                    "summary": str(exc),
                    "prompt_preview": prompt[:240],
                    "schema_supplied": schema is not None,
                    "error": "ollama_unavailable",
                },
            }

        return {
            "provider": self.name,
            "model": self.client.model,
            "output": {
                "summary": (
                    result.parsed_json.get("summary")
                    if isinstance(result.parsed_json, dict) and "summary" in result.parsed_json
                    else "Local Ollama provider response. Review before relying on it."
                ),
                "structured_output": result.parsed_json,
                "raw_text": result.raw_text,
                "prompt_preview": prompt[:240],
                "schema_supplied": schema is not None,
            },
        }
