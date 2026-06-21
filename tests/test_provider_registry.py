from anti_dating_scam.providers.registry import get_provider, provider_names


def test_mock_provider_output_is_structured() -> None:
    provider = get_provider("Mock")
    result = provider.analyze("Analyze this safely.", schema={"type": "object"})

    assert result["provider"] == "Mock"
    assert result["model"]
    assert isinstance(result["output"], dict)


def test_provider_registry_lists_placeholders() -> None:
    names = provider_names()

    assert "Mock" in names
    assert "OpenAI" in names
    assert "Ollama" in names
