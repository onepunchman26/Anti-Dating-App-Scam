from typing import Protocol


class LLMClient(Protocol):
    """Provider-neutral interface for future LLM-backed components."""

    def generate_structured(self, prompt: str, schema_name: str) -> dict:
        """Return structured data that conforms to an application-level schema."""
