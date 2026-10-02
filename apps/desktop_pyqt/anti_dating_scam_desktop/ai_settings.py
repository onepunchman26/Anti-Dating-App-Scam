"""Persisted AI-connection settings (never secrets).

Privacy rule (apex `privacy-and-secrets.md`): this file lives under the user's
home which may be OneDrive-synced, so **API keys are never written here** — they
stay in process memory only, optionally read from an environment variable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_PATH = Path.home() / ".ai_slowmatch" / "ai.json"

MODE_MANUAL = "manual"
MODE_AGENT = "agent"
MODE_OLLAMA = "ollama"
MODE_ANTHROPIC = "anthropic"

ALL_MODES = (MODE_MANUAL, MODE_AGENT, MODE_OLLAMA, MODE_ANTHROPIC)


@dataclass
class AISettings:
    mode: str = MODE_MANUAL
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    anthropic_model: str = "claude-sonnet-5"
    # True only when the user picked the mode explicitly in the Connect screen.
    # Auto-detected fallbacks must NOT jump the probe queue on later launches,
    # otherwise a temporary fallback (e.g. Ollama while Claude was logged out)
    # would permanently shadow the preferred agent mode.
    chosen_by_user: bool = False

    def sanitized(self) -> AISettings:
        if self.mode not in ALL_MODES:
            return AISettings()
        return self


def load_settings(path: Path | None = None) -> AISettings:
    settings_path = path or SETTINGS_PATH
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AISettings()
    known = {key: value for key, value in data.items() if key in AISettings().__dict__}
    return AISettings(**known).sanitized()


def save_settings(settings: AISettings, path: Path | None = None) -> None:
    settings_path = path or SETTINGS_PATH
    payload = asdict(settings.sanitized())
    # Defense in depth: refuse to persist anything that smells like a secret.
    assert not any("key" in name or "token" in name for name in payload), payload
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
