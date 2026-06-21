from anti_dating_scam.providers.base import AIProvider
from anti_dating_scam.providers.mock_provider import MockProvider
from anti_dating_scam.providers.placeholders import PlaceholderProvider


def provider_names() -> list[str]:
    return ["Mock", "OpenAI", "Anthropic", "Gemini", "Ollama"]


def get_provider(name: str) -> AIProvider:
    normalized = name.strip().lower()
    if normalized == "mock":
        return MockProvider()
    for provider_name in provider_names()[1:]:
        if normalized == provider_name.lower():
            return PlaceholderProvider(provider_name)
    return MockProvider()
