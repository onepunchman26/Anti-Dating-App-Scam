"""Per-application local state with immutable destinations for in-flight work.

No UI dependencies and no provider calls. A slow operation keeps the vault and
backend it began with even if another browser tab changes the active selection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


class LocalSelectionChanged(RuntimeError):
    pass


@dataclass(frozen=True)
class VaultPaths:
    root: Path
    pointer: Path

    def path(self, name: str) -> Path:
        suffixes = {
            "SELF_MODEL_PATH": "self_model.json",
            "SETTINGS_PATH": "client_settings.json",
            "NOTES_PATH": "imports/notes.md",
            "PORTRAIT_MD_PATH": "reports/social_self_portrait.md",
            "PORTRAIT_JSON_PATH": "reports/social_self_portrait.json",
            "PORTRAIT_EN_PATH": "reports/social_self_portrait.en.md",
            "PORTRAIT_ZH_PATH": "reports/social_self_portrait.zh.md",
            "PLAN_MD_PATH": "reports/relationship_plan.md",
            "PLAN_JSON_PATH": "reports/relationship_plan.json",
        }
        if name == "VAULT_DIR":
            return self.root
        if name == "APP_POINTER_PATH":
            return self.pointer
        return self.root / suffixes[name]


@dataclass(frozen=True)
class LocalClientSnapshot:
    paths: VaultPaths
    backend: Any | None
    generation: int

    @property
    def vault_id(self) -> str:
        return hashlib.sha256(str(self.paths.root).encode("utf-8")).hexdigest()[:24]


class LocalClientState:
    def __init__(self, vault: Path, pointer: Path, backend: Any | None = None) -> None:
        self._lock = RLock()
        self._paths = VaultPaths(vault.expanduser().resolve(), pointer.expanduser().resolve())
        self._backend = backend
        self._generation = 0

    def snapshot(self) -> LocalClientSnapshot:
        with self._lock:
            return LocalClientSnapshot(self._paths, self._backend, self._generation)

    def _require_current(self, expected_generation: int) -> None:
        if self._generation != expected_generation:
            raise LocalSelectionChanged(
                "The active vault or AI selection changed during this operation. Retry from "
                "the current selection. / 操作期间档案库或 AI 选择发生变化，请在当前选择下重试。"
            )

    def set_backend(self, backend: Any, expected_generation: int) -> LocalClientSnapshot:
        with self._lock:
            self._require_current(expected_generation)
            self._backend = backend
            self._generation += 1
            return self.snapshot()

    def switch_vault(self, root: Path, expected_generation: int) -> LocalClientSnapshot:
        with self._lock:
            self._require_current(expected_generation)
            resolved = root.expanduser().resolve()
            if not resolved.is_dir():
                raise ValueError("Choose an existing local vault directory.")
            self._paths.pointer.parent.mkdir(parents=True, exist_ok=True)
            self._paths.pointer.write_text(
                json.dumps({"vault_dir": str(resolved)}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._paths = VaultPaths(resolved, self._paths.pointer)
            self._backend = None
            self._generation += 1
            return self.snapshot()
