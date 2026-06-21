from typing import Any


class MockProvider:
    name = "Mock"

    def analyze(self, prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "provider": self.name,
            "model": "local-rule-based-mvp",
            "output": {
                "summary": "Mock provider only. No remote API call was made.",
                "prompt_preview": prompt[:240],
                "schema_supplied": schema is not None,
            },
        }
