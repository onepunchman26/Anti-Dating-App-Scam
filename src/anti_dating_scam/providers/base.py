from typing import Protocol


class AIProvider(Protocol):
    name: str

    def analyze(self, prompt: str, schema: dict | None = None) -> dict:
        """Return structured dict-like output."""
