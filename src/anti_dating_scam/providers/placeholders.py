class PlaceholderProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    def analyze(self, prompt: str, schema: dict | None = None) -> dict:
        return {
            "provider": self.name,
            "model": "placeholder",
            "output": {
                "summary": (
                    f"{self.name} provider is a placeholder in this MVP. "
                    "No remote API call was made."
                ),
                "prompt_preview": prompt[:240],
                "schema_supplied": schema is not None,
            },
        }
