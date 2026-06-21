from anti_dating_scam.ai.provider import LLMClient


class MockAIProvider(LLMClient):
    """Deterministic provider used for tests and local prototype behavior."""

    def generate_structured(self, prompt: str, schema_name: str) -> dict:
        return {
            "schema_name": schema_name,
            "provider": "mock",
            "summary": (
                "Mock provider output. The production system should use a configured "
                "provider through the LLMClient interface."
            ),
            "prompt_preview": prompt[:160],
        }
