import json
from pathlib import Path
from typing import Any

# Where we remember which vault the user chose, so the app reopens it next launch.
# This is a tiny pointer file only; the actual profile data lives in the vault.
CONFIG_DIR = Path.home() / ".ai_slowmatch"
CONFIG_PATH = CONFIG_DIR / "config.json"

# Fallback vault used before the user has browsed/created their own.
DEFAULT_VAULT_DIR = Path.home() / ".ai_slowmatch"
DEFAULT_VAULT_NAME = "AI-SlowMatch-Vault"

# Instruction file dropped into every vault so a desktop coding/AI agent
# (Claude Code, Cowork, Codex, ...) knows what the folder is and how to help.
# Agent-facing, so primarily English with a short Chinese summary up top.
AGENT_INSTRUCTIONS = """# AI-SlowMatch Vault - Agent Instructions

> 中文摘要：这是 AI-SlowMatch 的本地个人档案库（vault）。请仅在本地协助用户反思与完善
> 档案；不要上传任何内容，不要做社交评分或「安全/危险」判定，不要建议向网恋对象转账或
> 发送身份证件、私密照片等敏感信息。

## What this vault is

This folder is a personal, local-first **vault** created by the AI-SlowMatch desktop
app. It holds one person's self-reflection profile plus the source material it was
built from. A desktop agent (Claude Code, Cowork, Codex, etc.) can open this folder
to help the user read, reflect on, and improve the profile - using only the files in
this vault.

## Structure

- `profile/profile.mpm.md` - human-readable Markdown personal profile (MPMD). Primary,
  user-editable. Treat this as the source of truth.
- `profile/profile.json` - structured companion for programmatic use. Keep it
  consistent with the Markdown whenever you edit either one.
- `imports/` - raw source material the user explicitly provided (notes, exported
  chats). Private. Do not copy elsewhere.
- `reports/` - generated risk / trust-ladder reports.
- `AGENTS.md` / `CLAUDE.md` - this file.

## How to help

- Read `profile/profile.mpm.md` and help the user clarify their relationship values,
  communication and boundary preferences, and risk tolerance.
- When you edit, keep the Markdown plain and readable, and keep `profile.json`
  in sync with it.
- Only use files the user has placed in this vault. Ask before bringing in anything else.

## Safety boundaries (do not cross)

- Do not create social scores, personality rankings, or good/bad-person labels.
- Do not advise spying, doxxing, hacking, impersonation, harassment, or revenge.
- Do not encourage sending money, private images, identity documents, or other
  sensitive information to online-only romantic contacts.
- Do not frame risk as a property of one gender.
- Privacy-first: never upload or transmit vault contents. Keep everything local
  unless the user explicitly chooses to export.

## What this profile is NOT

Not a diagnosis, not a social score, not proof of personality, not proof of safety
or danger, and not training data for a personal model.
"""


class ProfileStore:
    """Local profile storage rooted at a user-chosen *vault* folder.

    The vault has a structured layout::

        <vault>/
            profile/
                profile.mpm.md
                profile.json
            imports/
            reports/
            AGENTS.md
            CLAUDE.md

    The historical flat API (``markdown_path``, ``json_path``,
    ``save_markdown_profile``, ...) is preserved; those paths now point inside
    ``profile/``.
    """

    def __init__(self, base_dir: Path | None = None, config_path: Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        if base_dir is None:
            base_dir = self._load_remembered_vault() or DEFAULT_VAULT_DIR
        self.set_base_dir(base_dir)

    # ------------------------------------------------------------------ layout
    def set_base_dir(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.profile_dir = self.base_dir / "profile"
        self.imports_dir = self.base_dir / "imports"
        self.reports_dir = self.base_dir / "reports"
        self.markdown_path = self.profile_dir / "profile.mpm.md"
        self.json_path = self.profile_dir / "profile.json"
        self.agents_md_path = self.base_dir / "AGENTS.md"
        self.claude_md_path = self.base_dir / "CLAUDE.md"

    def create_default_directories(self) -> None:
        for directory in (self.base_dir, self.profile_dir, self.reports_dir, self.imports_dir):
            directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ vaults
    def create_vault(self, parent_dir: Path, name: str = DEFAULT_VAULT_NAME) -> Path:
        """Create a new vault folder under ``parent_dir`` and switch to it."""
        vault = Path(parent_dir) / name
        self.set_base_dir(vault)
        self.create_default_directories()
        self.write_agent_instructions()
        self.remember_vault()
        return vault

    def use_existing_vault(self, vault_dir: Path) -> None:
        """Point the store at an existing vault folder and remember it."""
        self.set_base_dir(vault_dir)
        self.create_default_directories()
        self.remember_vault()

    def write_agent_instructions(self) -> Path:
        """Write the agent instruction file (AGENTS.md + CLAUDE.md) into the vault."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.agents_md_path.write_text(AGENT_INSTRUCTIONS, encoding="utf-8")
        self.claude_md_path.write_text(AGENT_INSTRUCTIONS, encoding="utf-8")
        return self.agents_md_path

    # --------------------------------------------------------- config (pointer)
    def _load_remembered_vault(self) -> Path | None:
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        vault = data.get("vault_path")
        return Path(vault) if vault else None

    def remember_vault(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps({"vault_path": str(self.base_dir)}, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------- profile I/O
    def detect_existing_profile(self) -> bool:
        return self.markdown_path.exists() or self.json_path.exists()

    def load_markdown_profile(self, path: Path | None = None) -> str:
        return (path or self.markdown_path).read_text(encoding="utf-8")

    def load_json_profile(self, path: Path | None = None) -> dict[str, Any]:
        return json.loads((path or self.json_path).read_text(encoding="utf-8"))

    def save_markdown_profile(self, markdown: str, path: Path | None = None) -> Path:
        self.create_default_directories()
        output_path = path or self.markdown_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return output_path

    def save_json_profile(self, profile: dict[str, Any], path: Path | None = None) -> Path:
        self.create_default_directories()
        output_path = path or self.json_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        return output_path

    def get_reports_dir(self) -> Path:
        self.create_default_directories()
        return self.reports_dir

    def get_imports_dir(self) -> Path:
        self.create_default_directories()
        return self.imports_dir
