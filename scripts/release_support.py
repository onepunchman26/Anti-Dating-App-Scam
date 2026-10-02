"""Source snapshots and recoverable local promotion for the fixed Desktop entry."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tomllib
import zipfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

DIRECTORIES = {"src", "apps", "tests", "docs", "examples", "packaging", "scripts", ".github"}
ROOT_FILES = {
    ".gitignore",
    ".env.example",
    "AGENTS.md",
    "pyproject.toml",
    "README.md",
    "PLAN_FOR_ONEPUCHMAN.md",
    "PROGRESS_TRACKER.md",
    "CURRENT_STATUS.md",
    "OWNER_REVIEW.md",
    "run_desktop.py",
    "run_local_app.py",
    "run_rendezvous_node.py",
    "setup_windows.ps1",
    "build_exe.ps1",
    "release.ps1",
}
SOURCE_SUFFIXES = {
    ".py",
    ".json",
    ".toml",
    ".md",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".ps1",
    ".sh",
    ".yml",
    ".yaml",
    ".txt",
    ".svg",
    ".gitkeep",
}
EXE = "AI-SlowMatch.exe"
DIGEST = r"^[0-9a-f]{64}$"


class ReleaseError(ValueError):
    pass


class ReleaseManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal["1"] = "1"
    build_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    created_at: str
    git_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    dirty: bool
    source_digest: str = Field(pattern=DIGEST)
    executable: Literal["AI-SlowMatch.exe"] = EXE
    sha256: str = Field(pattern=DIGEST)
    checks: dict[str, Literal["passed"]]
    acceptance: Literal["development; real AI and microphone acceptance separate"] = (
        "development; real AI and microphone acceptance separate"
    )


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + "." + uuid4().hex)
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _inside(root: Path, path: Path) -> None:
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ReleaseError("Path leaves the managed directory.")
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ReleaseError("Linked managed directory.")


def source_files(root: Path) -> list[str]:
    """Explicit development allowlist, including untracked source, never vaults."""
    result = []
    for name in sorted(ROOT_FILES):
        path = root / name
        if path.is_file():
            _inside(root, path)
            result.append(name)
    for name in sorted(DIRECTORIES):
        base = root / name
        if not base.exists():
            continue
        for directory, children, files in os.walk(base, followlinks=False):
            children[:] = sorted(
                x
                for x in children
                if not x.endswith((".egg-info", ".dist-info"))
                and x
                not in {
                    "__pycache__",
                    ".pytest_cache",
                    "node_modules",
                    ".git",
                    "vault",
                    "imports",
                    ".peer-session",
                    ".dating-introduction",
                    ".relationship-memory",
                    ".video-context",
                    "matching-node",
                }
            )
            for filename in sorted(files):
                path = Path(directory) / filename
                if path.suffix not in SOURCE_SUFFIXES and filename != ".gitkeep":
                    continue
                _inside(root, path)
                if not stat.S_ISREG(path.stat().st_mode):
                    raise ReleaseError("Non-regular source file.")
                result.append(path.relative_to(root).as_posix())
    return sorted(result)


def source_hashes(root: Path) -> dict[str, str]:
    return {name: digest(root / name) for name in source_files(root)}


def source_digest(hashes: dict) -> str:
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def backup_source(root: Path, destination: Path) -> Path:
    root, destination = root.resolve(), destination.resolve()
    if destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ReleaseError("Backups must be outside the checkout.")
    onedrive = os.environ.get("OneDrive")
    if onedrive and destination.is_relative_to(Path(onedrive).resolve()):
        raise ReleaseError("Backups must be outside OneDrive.")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / ("source-" + uuid4().hex)
    target.mkdir()
    hashes = source_hashes(root)
    with zipfile.ZipFile(target / "source.zip", "x", zipfile.ZIP_DEFLATED) as archive:
        for name, expected in hashes.items():
            data = (root / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ReleaseError("Source changed during snapshot.")
            archive.writestr(name, data)
    if hashes != source_hashes(root):
        raise ReleaseError("Source changed during snapshot.")
    subprocess.run(
        ["git", "-C", str(root), "bundle", "create", str(target / "history.bundle"), "--all"],
        check=True,
        capture_output=True,
    )
    (target / "working-tree.patch").write_bytes(
        subprocess.check_output(
            ["git", "-C", str(root), "diff", "--binary", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
    )
    _json(
        target / "snapshot.json",
        {
            "schema_version": 1,
            "managed_by": "slowmatch-source-backup",
            "created_at": datetime.now(UTC).isoformat(),
            "files": hashes,
            "head": git(root, "rev-parse", "HEAD"),
            "source_digest": source_digest(hashes),
            "archive_sha256": digest(target / "source.zip"),
            "history_sha256": digest(target / "history.bundle"),
            "restore_verified": False,
        },
    )
    restore_source(target, target / "restore-check")
    metadata = json.loads((target / "snapshot.json").read_text(encoding="utf-8"))
    metadata["restore_verified"] = True
    _json(target / "snapshot.json", metadata)
    return target


def restore_source(snapshot: Path, target: Path) -> None:
    """Restore only into a new directory; validate names before any extraction."""
    if target.exists():
        raise ReleaseError("Restore requires a new empty destination.")
    metadata = json.loads((snapshot / "snapshot.json").read_text(encoding="utf-8"))
    if metadata.get("managed_by") != "slowmatch-source-backup":
        raise ReleaseError("Not a managed source backup.")
    if (
        digest(snapshot / "source.zip") != metadata["archive_sha256"]
        or digest(snapshot / "history.bundle") != metadata["history_sha256"]
    ):
        raise ReleaseError("Backup hash mismatch.")
    with zipfile.ZipFile(snapshot / "source.zip") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(metadata["files"]):
            raise ReleaseError("Backup entries mismatch.")
        for name in names:
            if (
                "\\" in name
                or ":" in name
                or name.startswith("/")
                or any(p in {".", "..", ""} for p in name.split("/"))
            ):
                raise ReleaseError("Unsafe backup entry.")
            if hashlib.sha256(archive.read(name)).hexdigest() != metadata["files"][name]:
                raise ReleaseError("Backup content mismatch.")
        target.mkdir(parents=True)
        for name in names:
            path = target / name
            _inside(target, path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(name))
    subprocess.run(
        [
            "git",
            "clone",
            "--bare",
            "--quiet",
            str(snapshot / "history.bundle"),
            str(target / "restored-history.git"),
        ],
        check=True,
        capture_output=True,
    )


def read_release(path: Path) -> ReleaseManifest:
    if path.stat().st_size > 100_000:
        raise ReleaseError("Oversized release manifest.")
    return ReleaseManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


@contextmanager
def promotion_lock(releases: Path):
    releases.mkdir(parents=True, exist_ok=True)
    lock = releases / ".promotion.lock"
    _inside(releases, lock)
    with lock.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ReleaseError("Another release operation is in progress.") from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _recover(root: Path) -> None:
    releases = root / "releases"
    transaction = releases / "promotion.json"
    if not transaction.exists():
        return
    data = json.loads(transaction.read_text(encoding="utf-8"))
    after = ReleaseManifest.model_validate(data["after"])
    before = ReleaseManifest.model_validate(data["before"]) if data["before"] else None
    current_hash = digest(root / EXE) if (root / EXE).exists() else None
    if current_hash == after.sha256:
        _json(releases / "current.json", after.model_dump())
    elif before and current_hash == before.sha256:
        _json(releases / "current.json", before.model_dump())
    elif not before and current_hash is None:
        pass
    else:
        raise ReleaseError("Unknown current executable; preserve files and inspect transaction.")
    transaction.unlink()


def promote(root: Path, candidate: Path, manifest: ReleaseManifest) -> None:
    """Atomic executable replacement; recoverable receipt, never kill a running app."""
    root = root.resolve()
    releases = root / "releases"
    _inside(root, releases)
    _inside(root, root / EXE)
    required = {"compile", "pytest", "lint", "package", "smoke"}
    if not required.issubset(manifest.checks) or digest(candidate) != manifest.sha256:
        raise ReleaseError("Candidate gates or hash are invalid.")
    with promotion_lock(releases):
        _recover(root)
        current = releases / "current.json"
        before = read_release(current) if current.exists() else None
        if (root / EXE).exists() and (before is None or digest(root / EXE) != before.sha256):
            raise ReleaseError(
                "Unmanaged or changed root executable; preserve it before promotion."
            )
        archive = releases / manifest.build_id
        archive.mkdir(exist_ok=True)
        _inside(releases, archive)
        archived_exe = archive / EXE
        _inside(releases, archived_exe)
        if archived_exe.exists() and digest(archived_exe) != manifest.sha256:
            raise ReleaseError("Build identity already belongs to another artifact.")
        if not archived_exe.exists():
            shutil.copy2(candidate, archived_exe)
        if digest(archived_exe) != manifest.sha256:
            raise ReleaseError("Archived artifact hash mismatch.")
        _json(archive / "manifest.json", manifest.model_dump())
        staged = root / (".slowmatch-promote-" + uuid4().hex + ".tmp")
        try:
            shutil.copy2(archived_exe, staged)
            with staged.open("r+b") as stream:
                os.fsync(stream.fileno())
            if digest(staged) != manifest.sha256:
                raise ReleaseError("Promotion copy hash mismatch.")
            _json(
                releases / "promotion.json",
                {
                    "before": before.model_dump() if before else None,
                    "after": manifest.model_dump(),
                },
            )
            try:
                os.replace(staged, root / EXE)
            except PermissionError:
                _recover(root)
                raise ReleaseError(
                    "Close AI-SlowMatch, then retry promotion. Old app preserved."
                ) from None
            _json(current, manifest.model_dump())
            (releases / "promotion.json").unlink()
        finally:
            staged.unlink(missing_ok=True)


def rollback(root: Path, build_id: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{32}", build_id):
        raise ReleaseError("Invalid build identifier.")
    archive = root / "releases" / build_id
    _inside(root, archive)
    manifest = read_release(archive / "manifest.json")
    if manifest.build_id != build_id:
        raise ReleaseError("Archive identity mismatch.")
    promote(root, archive / EXE, manifest)


def _remove_managed_tree(parent: Path, target: Path) -> None:
    """Validate every absolute target before recursive deletion, including junctions."""
    parent, target = parent.absolute(), target.absolute()
    if target.parent != parent or target.resolve() != target or parent.resolve() != parent:
        raise ReleaseError("Retention target is not an ordinary managed child directory.")
    for directory, children, files in os.walk(target, followlinks=False):
        for path in [Path(directory), *(Path(directory) / name for name in children + files)]:
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ReleaseError("Retention will not follow linked files or directories.")
            if not path.resolve().is_relative_to(target):
                raise ReleaseError("Retention path leaves the validated target.")
    shutil.rmtree(target)


def apply_retention(root: Path, backups: Path, *, keep_backups=5, keep_releases=3) -> list[str]:
    """Prune verified managed copies only; .keep, unknown and invalid copies survive."""
    if keep_backups < 1 or keep_releases < 2:
        raise ReleaseError("Keep at least one backup and two releases.")
    removed = []
    candidates = []
    if backups.exists():
        for folder in backups.glob("source-*"):
            try:
                _inside(backups, folder)
                data = json.loads((folder / "snapshot.json").read_text(encoding="utf-8"))
                if (
                    data.get("managed_by") != "slowmatch-source-backup"
                    or data.get("restore_verified") is not True
                    or digest(folder / "source.zip") != data["archive_sha256"]
                    or digest(folder / "history.bundle") != data["history_sha256"]
                ):
                    continue
                candidates.append((data["created_at"], folder))
            except (OSError, ValueError, KeyError):
                continue
        for _date, folder in sorted(candidates, reverse=True)[keep_backups:]:
            if not (folder / ".keep").exists():
                _remove_managed_tree(backups, folder)
                removed.append(folder.name)
    releases = root / "releases"
    with promotion_lock(releases):
        _recover(root)
        current = read_release(releases / "current.json")
        candidates = []
        for folder in releases.iterdir():
            if not re.fullmatch(r"[0-9a-f]{32}", folder.name):
                continue
            try:
                _inside(releases, folder)
                manifest = read_release(folder / "manifest.json")
                if manifest.build_id == folder.name and digest(folder / EXE) == manifest.sha256:
                    candidates.append((manifest.created_at, folder))
            except (OSError, ValueError):
                continue
        for _date, folder in sorted(candidates, reverse=True)[keep_releases:]:
            if folder.name != current.build_id and not (folder / ".keep").exists():
                _remove_managed_tree(releases, folder)
                removed.append(folder.name)
    return removed


def write_build_metadata(root: Path, target: Path, build_id: str | None = None) -> dict:
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ReleaseError("Use a three-component product version.")
    info = {
        "version": version,
        "build_id": build_id or uuid4().hex,
        "git_commit": git(root, "rev-parse", "HEAD"),
        "dirty": bool(git(root, "status", "--porcelain")),
        "source_digest": source_digest(source_hashes(root)),
    }
    target.mkdir(parents=True, exist_ok=True)
    _json(target / "build_info.json", info)
    numbers = tuple(int(part) for part in version.split(".")) + (0,)
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    resource = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=numbers,
            prodvers=numbers,
            mask=0x3F,
            flags=0,
            OS=0x40004,
            fileType=1,
            subtype=0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo(
                [
                    StringTable(
                        "040904B0",
                        [
                            StringStruct("FileVersion", version),
                            StringStruct("ProductVersion", version),
                            StringStruct("ProductName", "AI-SlowMatch"),
                            StringStruct("FileDescription", "AI-SlowMatch Relationship Copilot"),
                            StringStruct("OriginalFilename", EXE),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )
    (target / "version-resource.txt").write_text(str(resource), encoding="utf-8")
    return info
