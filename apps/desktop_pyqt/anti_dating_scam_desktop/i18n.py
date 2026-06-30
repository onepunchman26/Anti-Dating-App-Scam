"""Tiny bilingual text helper for the desktop GUI.

The project's bilingual rule (see ``AGENTS.md`` / ``PROGRESS_TRACKER.md``) covers
human-facing docs and in-app text. This helper lets every screen and widget
compose an "English / 中文" display string at the call site, without needing a
full locale/translation framework. Widgets stay generic (they just render
whatever string they are given); only the call sites need to use ``bi()``.
"""

from __future__ import annotations


def bi(en: str, zh: str) -> str:
    """Compose a combined bilingual display string: "English / 中文".

    If ``zh`` is empty, returns ``en`` unchanged (useful for purely dynamic
    fragments where a translation isn't practical, e.g. raw file paths).
    """
    en = en.strip()
    zh = zh.strip()
    if not zh:
        return en
    return f"{en} / {zh}"
