"""Remember only the model slug for an app registration, never login or consent."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from anti_dating_scam.ai.chatgpt_auth import ChatGPTModelChoice


class ModelPreferences:
    def __init__(self, directory: Path | None = None):
        self.directory = (
            directory
            or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AI-SlowMatch" / "model-choices"
        )

    def _path(self, client_id: str) -> Path:
        if not client_id or len(client_id) > 500:
            raise ValueError("A connected app registration is required.")
        return self.directory / (hashlib.sha256(client_id.encode()).hexdigest() + ".json")

    def load(self, client_id: str) -> str | None:
        try:
            path = self._path(client_id)
            if path.is_symlink() or path.stat().st_size > 2000:
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            return ChatGPTModelChoice(slug=data["model"], display_name=data["model"]).slug
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save(self, client_id: str, model: str) -> None:
        ChatGPTModelChoice(slug=model, display_name=model)
        path = self._path(client_id)
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = self.directory / (uuid4().hex + ".tmp")
        try:
            temporary.write_text(json.dumps({"version": 1, "model": model}), encoding="utf-8")
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
