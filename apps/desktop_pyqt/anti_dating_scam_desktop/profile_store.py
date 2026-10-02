import json
import os
import tempfile
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
built from. Manual agent access is intended only for an independently isolated
local model. A desktop CLI can still send inference or logs to remote services:
stop before reading vault files if that applies. Use the application's reviewed
disclosure workflow for external AI instead. These instructions are not a sandbox.

手动代理访问仅供已独立隔离的本地模型。桌面 CLI 也可能向远程服务发送推理内容或日志；
若存在这种情况，请在读取档案前停止。外部 AI 应使用应用内的披露审核流程。
说明文件本身不是隔离沙箱。

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
        self.analysis_request_path = self.base_dir / "ANALYSIS_REQUEST.md"
        self.self_portrait_request_path = self.base_dir / "SELF_PORTRAIT_REQUEST.md"
        self.self_portrait_path = self.reports_dir / "self_portrait.md"
        self.self_portrait_detailed_path = self.reports_dir / "self_portrait.detailed.md"
        self.self_portrait_json_path = self.reports_dir / "self_portrait.json"
        self.self_portrait_html_path = self.reports_dir / "self_portrait.html"
        self.criteria_interview_request_path = self.base_dir / "CRITERIA_INTERVIEW_REQUEST.md"
        self.mate_criteria_path = self.reports_dir / "mate_criteria.md"
        self.mate_criteria_json_path = self.reports_dir / "mate_criteria.json"
        self.ideal_profiles_json_path = self.reports_dir / "ideal_partner_profiles.json"

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
        candidate = ProfileStore(Path(vault_dir), config_path=self.config_path)
        if candidate.has_legacy_profile() and not candidate.detect_existing_profile():
            raise ValueError(
                "Review and confirm legacy profile migration first. / 请先复核并确认旧版档案迁移。"
            )
        candidate.create_default_directories()
        candidate.remember_vault()
        self.set_base_dir(candidate.base_dir)

    def has_legacy_profile(self, path: Path | None = None) -> bool:
        """Recognise fixed historical root files without loading or copying them."""
        root = Path(path) if path is not None else self.base_dir
        return any(os.path.lexists(root / name) for name in ("profile.mpm.md", "profile.json"))

    def is_vault(self, path: Path) -> bool:
        """Whether ``path`` looks like an AI-SlowMatch vault folder.

        A vault is recognised by its structure (a ``profile/`` subfolder or the
        agent instruction files we drop in), or by already holding a profile -
        not just by existing. This lets the UI tell "an empty-but-real vault"
        apart from "any random folder".
        """
        path = Path(path)
        if not path.is_dir():
            return False
        if self.has_legacy_profile(path):
            return True
        if (path / "profile" / "profile.mpm.md").exists():
            return True
        if (path / "profile" / "profile.json").exists():
            return True
        if (path / "profile").is_dir():
            return True
        return (path / "AGENTS.md").exists() or (path / "CLAUDE.md").exists()

    def resolve_vault(self, path: Path) -> Path | None:
        """Map a user-picked folder to the actual vault folder, or ``None``.

        Handles the common mistake of picking the *parent* directory the vault
        was created under (which contains ``AI-SlowMatch-Vault/``) instead of
        the vault folder itself. Returns ``None`` when nothing vault-like is
        found so the caller can offer to initialise the folder as a vault.
        """
        path = Path(path)
        if self.is_vault(path):
            return path
        named_child = path / DEFAULT_VAULT_NAME
        if self.is_vault(named_child):
            return named_child
        if path.is_dir():
            vault_children = [child for child in path.iterdir() if self.is_vault(child)]
            if len(vault_children) == 1:
                return vault_children[0]
        return None

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
        descriptor, temporary = tempfile.mkstemp(
            prefix=".vault-pointer-", suffix=".tmp", dir=self.config_path.parent,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(json.dumps({"vault_path": str(self.base_dir)}, indent=2))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.config_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    # ------------------------------------------------------------- profile I/O
    def detect_existing_profile(self) -> bool:
        return self.markdown_path.exists() or self.json_path.exists()

    def load_markdown_profile(self, path: Path | None = None) -> str:
        return (path or self.markdown_path).read_text(encoding="utf-8")

    def load_json_profile(self, path: Path | None = None) -> dict[str, Any]:
        return json.loads((path or self.json_path).read_text(encoding="utf-8-sig"))

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

    # --------------------------------------------------- agent-mode handoff I/O
    def save_import_text(self, text: str, filename: str) -> Path:
        """Save user-provided text (e.g. a conversation to review) into imports/."""
        self.create_default_directories()
        output_path = self.imports_dir / filename
        output_path.write_text(text, encoding="utf-8")
        return output_path

    def write_analysis_request(self, text: str) -> Path:
        """Write the ANALYSIS_REQUEST.md contract into the vault root."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_request_path.write_text(text, encoding="utf-8")
        return self.analysis_request_path

    def write_self_portrait_request(self, text: str) -> Path:
        """Write the SELF_PORTRAIT_REQUEST.md contract into the vault root."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.self_portrait_request_path.write_text(text, encoding="utf-8")
        return self.self_portrait_request_path

    def has_self_portrait(self) -> bool:
        return self.self_portrait_path.exists() or self.self_portrait_json_path.exists()

    def load_self_portrait(self) -> str | None:
        """The simple, user-facing self-portrait Markdown the agent wrote, if any."""
        active = self.read_active_report("self_portrait")
        if active is not None:
            return active.markdown
        return self.load_original_self_portrait()

    def read_active_report(self, kind: str):
        """Resolve a verified selected snapshot; errors never trigger original fallback."""
        from anti_dating_scam.services.active_reports import ActiveReportService

        return ActiveReportService(self.base_dir).resolve(kind)

    def load_original_self_portrait(self) -> str | None:
        """Legacy original content, used only after resolving the no-selection default."""
        if self.self_portrait_path.exists():
            return self.self_portrait_path.read_text(encoding="utf-8")
        return None

    def load_self_portrait_json(self) -> dict[str, Any] | None:
        """The structured self-portrait the agent wrote, if any (drives the HTML)."""
        active = self.read_active_report("self_portrait")
        if active is not None:
            return active.canonical["report"]
        return self.load_original_self_portrait_json()

    def load_original_self_portrait_json(self) -> dict[str, Any] | None:
        if self.self_portrait_json_path.exists():
            try:
                return json.loads(self.self_portrait_json_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
        return None

    def write_self_portrait_html(self, html: str) -> Path:
        """Save the rendered visual (HTML) self-portrait into reports/."""
        self.create_default_directories()
        self.self_portrait_html_path.write_text(html, encoding="utf-8")
        return self.self_portrait_html_path

    def write_criteria_interview_request(self, text: str) -> Path:
        """Write the CRITERIA_INTERVIEW_REQUEST.md contract into the vault root."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.criteria_interview_request_path.write_text(text, encoding="utf-8")
        return self.criteria_interview_request_path

    def has_mate_criteria(self) -> bool:
        return self.mate_criteria_path.exists() or self.mate_criteria_json_path.exists()

    def load_mate_criteria(self) -> str | None:
        """The user-facing mate-criteria Markdown the agent wrote, if any."""
        active = self.read_active_report("mate_criteria")
        if active is not None:
            return active.markdown
        return self.load_original_mate_criteria()

    def load_original_mate_criteria(self) -> str | None:
        if self.mate_criteria_path.exists():
            return self.mate_criteria_path.read_text(encoding="utf-8")
        return None

    def find_latest_report(self) -> Path | None:
        """Most recently modified report file in reports/, or ``None``.

        Prefers the standard ``risk_report.md`` the agent is asked to write, but
        falls back to any Markdown/JSON the agent left behind.
        """
        if not self.reports_dir.is_dir():
            return None
        candidates = [path for path in self.reports_dir.glob("*") if path.is_file()]
        if not candidates:
            return None

        def sort_key(path: Path) -> tuple[int, float]:
            preferred = 1 if path.name == "risk_report.md" else 0
            return (preferred, path.stat().st_mtime)

        return max(candidates, key=sort_key)
