"""Bounded original-input discovery shared by browser, desktop and handoffs.

Generated reports, correction history and reviewed copies are never implicit owner evidence.
Reject links/reparse traversal before discovery and again at the actual read.
This is not a sandbox against a hostile process changing the filesystem concurrently.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Collection, Iterable
from pathlib import Path

MAX_SCAN_ENTRIES = 5000
MAX_EVIDENCE_FILES = 200
MAX_READ_BYTES = 256_000
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_OUTPUT_DIRS = {
    "reports", "review_history", "reviewed_copies", "active_selections", "legacy_archives",
    "converted_reports", ".profile-migration",
}
_OUTPUT_DIR_PREFIXES = (".pending-profile-migration-",)
_SKIP_DIRS = _OUTPUT_DIRS | {"node_modules", "__pycache__"}
_OUTPUT_NAMES = {
    "agents.md",
    "claude.md",
    "readme.md",
    "analysis_request.md",
    "self_portrait_request.md",
    "criteria_interview_request.md",
    "self_model.json",
    "client_settings.json",
    "app.json",
    "self_portrait.md",
    "self_portrait_detailed.md",
    "self_portrait.detailed.md",
    "self_portrait.json",
    "self_portrait_localization.json",
    "social_self_portrait.md",
    "social_self_portrait.en.md",
    "social_self_portrait.zh.md",
    "social_self_portrait.json",
    "mate_criteria.md",
    "mate_criteria.json",
    "mate_criteria_localization.json",
    "ideal_profiles.json",
    "ideal_partner_profiles.json",
    "relationship_plan.md",
    "relationship_plan.json",
    "risk_report.md",
    "risk_report.json",
    # Its user-only companion remains original owner input and is intentionally allowed.
    "criteria_interview_transcript.md",
}
_GENERATED_REFERENCE_NAMES = {
    "self_model.json",
    "reports/social_self_portrait.md",
    "reports/self_portrait.md",
    "reports/self_portrait.detailed.md",
}


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(Path(path).expanduser()))


def _unlinked(path: Path) -> bool:
    """Check the root, descendants and ancestors, including Windows junctions."""
    try:
        for node in (*reversed(path.parents), path):
            info = node.lstat()
            if (
                stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & _REPARSE_POINT
            ):
                return False
        return True
    except (OSError, ValueError):
        return False


def _allowed_location(
    path: Path, root: Path, generated_roots: Iterable[Path], *, report_reference: bool = False
) -> bool:
    try:
        if not path.is_relative_to(root) or not _unlinked(path):
            return False
        output_dirs = _OUTPUT_DIRS - {"reports"} if report_reference else _OUTPUT_DIRS
        skip_dirs = _SKIP_DIRS - {"reports"} if report_reference else _SKIP_DIRS
        # Absolute ancestors matter when the selected root is itself reports/history.
        if any(part.casefold() in output_dirs for part in path.parts[:-1]):
            return False
        if path.name.casefold() in output_dirs:
            return False
        if any(part.casefold().startswith(_OUTPUT_DIR_PREFIXES) for part in path.parts):
            return False
        relative = path.relative_to(root)
        if any(part.startswith(".") or part.casefold() in skip_dirs for part in relative.parts):
            return False
        resolved, resolved_root = path.resolve(strict=True), root.resolve(strict=True)
        if not resolved.is_relative_to(resolved_root):
            return False
        for excluded in generated_roots:
            absolute = _absolute(excluded)
            if path.is_relative_to(absolute) or resolved.is_relative_to(absolute.resolve()):
                return False
        return True
    except (OSError, ValueError, RuntimeError):
        return False


def evidence_path_allowed(
    path: Path,
    root: Path,
    *,
    generated_roots: Iterable[Path] = (),
) -> bool:
    """Whether this actual regular-file target is eligible original input."""
    path, root = _absolute(path), _absolute(root)
    if path.name.casefold() in _OUTPUT_NAMES or not _allowed_location(path, root, generated_roots):
        return False
    try:
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    except OSError:
        return False


def list_evidence_files(
    root: Path,
    *,
    generated_roots: Iterable[Path] = (),
    suffixes: Collection[str] | None = None,
    max_files: int = MAX_EVIDENCE_FILES,
    max_entries: int = MAX_SCAN_ENTRIES,
) -> list[Path]:
    """Discover a bounded set of eligible files, largest first, without following links."""
    root = _absolute(root)
    generated_roots = tuple(generated_roots)
    if not _allowed_location(root, root, generated_roots) or not root.is_dir():
        return []
    pending = [(root, 0)]
    found: list[tuple[int, Path]] = []
    visited = 0
    limit = max(0, min(max_entries, MAX_SCAN_ENTRIES))
    while pending and visited < limit:
        directory, depth = pending.pop()
        if depth > 32 or not _allowed_location(directory, root, generated_roots):
            continue
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    if visited > limit:
                        break
                    path = Path(entry.path)
                    if not _allowed_location(path, root, generated_roots):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        pending.append((path, depth + 1))
                    elif (suffixes is None or path.suffix.lower() in suffixes) and (
                        evidence_path_allowed(path, root, generated_roots=generated_roots)
                    ):
                        found.append((entry.stat(follow_symlinks=False).st_size, path))
        except OSError:
            continue
    found.sort(key=lambda item: (-item[0], str(item[1]).casefold()))
    return [path for _size, path in found[: max(0, min(max_files, MAX_EVIDENCE_FILES))]]


def read_evidence_text(
    path: Path,
    root: Path,
    *,
    max_chars: int,
    generated_roots: Iterable[Path] = (),
) -> str | None:
    """Read a bounded prefix only; return None for excluded or changed targets."""
    path, root = _absolute(path), _absolute(root)
    generated_roots = tuple(generated_roots)
    return _read_bounded_regular_text(
        path, max_chars,
        lambda: evidence_path_allowed(path, root, generated_roots=generated_roots),
    )


def _generated_reference_allowed(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root).as_posix().casefold()
        if relative not in _GENERATED_REFERENCE_NAMES:
            return False
        # A history/report subtree cannot masquerade as a whole vault.
        if any(part.casefold() in _OUTPUT_DIRS for part in root.parts):
            return False
        if not _allowed_location(path, root, (), report_reference=True):
            return False
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    except (OSError, ValueError):
        return False


def read_generated_reference(path: Path, vault_root: Path, *, max_chars: int) -> str | None:
    """Read only fixed prior AI artifacts; never resolve user-supplied source labels.

    These bytes remain unverified generated context, not original owner evidence.
    Correction history, reviewed copies, arbitrary report names and filesystem links are excluded.
    """
    path, root = _absolute(path), _absolute(vault_root)
    return _read_bounded_regular_text(
        path, max_chars, lambda: _generated_reference_allowed(path, root)
    )


def _read_bounded_regular_text(
    path: Path, max_chars: int, allowed: Callable[[], bool]
) -> str | None:
    if not 1 <= max_chars <= MAX_READ_BYTES // 4:
        raise ValueError("Evidence text limit is outside the supported range.")
    if not allowed():
        return None
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (
                opened.st_nlink != 1
                or not stat.S_ISREG(opened.st_mode)
                or not allowed()
            ):
                return None
            current = path.lstat()
            if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
                return None
            path_before = current
            raw = stream.read(min(MAX_READ_BYTES, max_chars * 4 + 4))
            if not allowed():
                return None
            after = os.fstat(stream.fileno())
            current = path.lstat()
            # Windows fstat/lstat expose different ctime meanings in some Python
            # versions; compare ctime only within the same API before/after.
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_nlink")
            original = tuple(getattr(opened, field) for field in fields)
            if any(
                tuple(getattr(info, field) for field in fields) != original
                for info in (after, current)
            ):
                return None
            if (
                opened.st_ctime_ns != after.st_ctime_ns
                or path_before.st_ctime_ns != current.st_ctime_ns
            ):
                return None
        text = raw.decode("utf-8-sig", errors="ignore")
        truncated = len(text) > max_chars or opened.st_size > len(raw)
        return text[:max_chars] + ("\n...[truncated for length]..." if truncated else "")
    except (OSError, ValueError):
        return None
