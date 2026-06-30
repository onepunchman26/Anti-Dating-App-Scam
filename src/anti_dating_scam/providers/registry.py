from anti_dating_scam.providers.base import AIProvider
from anti_dating_scam.providers.mock_provider import MockProvider
from anti_dating_scam.providers.ollama_provider import OllamaAIProviderAdapter
from anti_dating_scam.providers.placeholders import PlaceholderProvider

# Cloud providers stay placeholders until a real adapter is wired up: each one needs
# its own opt-in API key handling and explicit consent (see AGENTS.md privacy rules).
_PLACEHOLDER_PROVIDER_NAMES = ("OpenAI", "Anthropic", "Gemini")


def provider_names() -> list[str]:
    return ["Mock", *_PLACEHOLDER_PROVIDER_NAMES, "Ollama"]


def get_provider(name: str) -> AIProvider:
    normalized = name.strip().lower()
    if normalized == "mock":
        return MockProvider()
    if normalized == "ollama":
        return OllamaAIProviderAdapter()
    for provider_name in _PLACEHOLDER_PROVIDER_NAMES:
        if normalized == provider_name.lower():
            return PlaceholderProvider(provider_name)
    return MockProvider()
