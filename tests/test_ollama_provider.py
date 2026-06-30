import json

import pytest

from anti_dating_scam.ai.ollama_provider import (
    OllamaAIProvider,
    OllamaClient,
    OllamaUnavailableError,
)
from anti_dating_scam.providers.ollama_provider import OllamaAIProviderAdapter
from anti_dating_scam.providers.registry import get_provider, provider_names


def _fake_transport_returning(model_output: dict):
    def transport(url, payload, timeout):
        assert url.endswith("/api/generate")
        assert payload["model"]
        assert payload["format"] == "json"
        return {"response": json.dumps(model_output)}

    return transport


def _fake_transport_raising_connection_error():
    def transport(url, payload, timeout):
        raise OllamaUnavailableError("simulated: Ollama is not running")

    return transport


def test_ollama_client_parses_json_response_via_injected_transport() -> None:
    client = OllamaClient(
        transport=_fake_transport_returning({"summary": "All clear, low risk signals."})
    )

    result = client.generate("Analyze this conversation for risk signals.")

    assert result.parsed_json == {"summary": "All clear, low risk signals."}
    assert result.model == "llama3.2"


def test_ollama_client_falls_back_to_none_parsed_json_on_non_json_text() -> None:
    def transport(url, payload, timeout):
        return {"response": "not valid json"}

    client = OllamaClient(transport=transport)

    result = client.generate("prompt")

    assert result.parsed_json is None
    assert result.raw_text == "not valid json"


def test_ollama_ai_provider_generate_structured_uses_parsed_summary() -> None:
    provider = OllamaAIProvider(
        client=OllamaClient(
            transport=_fake_transport_returning({"summary": "Two medium-severity signals."})
        )
    )

    output = provider.generate_structured("some prompt", schema_name="risk_analysis_v1")

    assert output["schema_name"] == "risk_analysis_v1"
    assert output["provider"] == "ollama"
    assert output["summary"] == "Two medium-severity signals."


def test_ollama_provider_unavailable_raises_clear_error_not_silent_fallback() -> None:
    client = OllamaClient(transport=_fake_transport_raising_connection_error())

    with pytest.raises(OllamaUnavailableError):
        client.generate("prompt")


def test_registry_lists_ollama_and_returns_real_adapter() -> None:
    assert "Ollama" in provider_names()
    provider = get_provider("Ollama")

    assert isinstance(provider, OllamaAIProviderAdapter)
    assert provider.name == "Ollama"


def test_registry_ollama_adapter_reports_unavailable_gracefully_via_analyze() -> None:
    # `.analyze` must never raise: the desktop Settings screen calls providers
    # synchronously, so an unreachable local Ollama server should surface as a
    # readable error message in the output, not crash the UI.
    adapter = OllamaAIProviderAdapter(
        client=OllamaClient(transport=_fake_transport_raising_connection_error())
    )

    result = adapter.analyze("Analyze this safely.")

    assert result["provider"] == "Ollama"
    assert result["output"]["error"] == "ollama_unavailable"
    assert "Ollama" in result["output"]["summary"]
