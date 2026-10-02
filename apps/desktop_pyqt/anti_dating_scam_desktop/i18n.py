"""Language selection for the desktop GUI.

The project's bilingual rule requires every human-facing string to exist in both
English and Simplified Chinese. Rather than concatenating them into one messy
"English / 中文" line, we keep the two languages **separate** and show one at a
time, chosen by the user via a language toggle (mirroring the HTML report).

Call sites stay simple: ``bi("English text", "中文文本")`` returns whichever
language is currently selected. Widgets remain generic — they render the string
they are given; only the call sites carry both languages.
"""

from __future__ import annotations

import json
from pathlib import Path

_SETTINGS_PATH = Path.home() / ".ai_slowmatch" / "ui.json"

# "en" | "zh" — process-wide current language.
_LANG = "en"


def current_language() -> str:
    return _LANG


def set_language(lang: str, *, persist: bool = True) -> str:
    """Set the current language ("en"/"zh"); persist the choice by default."""
    global _LANG
    _LANG = "zh" if str(lang).lower().startswith("zh") else "en"
    if persist:
        _save()
    return _LANG


def toggle_language(*, persist: bool = True) -> str:
    return set_language("en" if _LANG == "zh" else "zh", persist=persist)


def load_saved_language() -> str | None:
    """Load and apply a previously saved language, or return ``None`` if none."""
    try:
        data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    lang = data.get("language")
    if lang in ("en", "zh"):
        set_language(lang, persist=False)
        return lang
    return None


def _save() -> None:
    try:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_PATH.write_text(json.dumps({"language": _LANG}, indent=2), encoding="utf-8")
    except OSError:
        pass


def bi(en: str, zh: str) -> str:
    """Return the string in the currently selected language.

    Falls back to the other language when one side is empty, so purely dynamic
    fragments (e.g. raw file paths passed as ``bi(path, "")``) still render.
    """
    en = (en or "").strip()
    zh = (zh or "").strip()
    if _LANG == "zh":
        return zh or en
    return en or zh


def other_language_label() -> str:
    """Label for the language you would switch *to* (for a toggle button)."""
    return "中文" if _LANG == "en" else "English"
