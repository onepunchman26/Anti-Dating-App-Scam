"""One local release command: protect, freeze, test, build, verify and promote."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release_support import (  # noqa: E402
    EXE,
    ReleaseError,
    ReleaseManifest,
    _json,
    apply_retention,
    backup_source,
    digest,
    promote,
    read_release,
    restore_source,
    rollback,
    source_digest,
    source_hashes,
    write_build_metadata,
)


def run_gate(command: list[str], cwd: Path, log: Path) -> None:
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "ADS_NO_AUTOCONNECT": "1"}
    # Import the frozen source, not an editable installation pointing to the checkout.
    environment["PYTHONPATH"] = os.pathsep.join(
        str(cwd / part) for part in ("src", "apps/desktop_pyqt", ".")
    )
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    if result.returncode:
        raise ReleaseError("Release gate failed; see " + str(log))


def build(root: Path, backups: Path, *, stage_only: bool = False) -> Path:
    if os.name != "nt" or sys.version_info[:2] != (3, 12):
        raise ReleaseError("The verified Windows release environment requires Python 3.12.")
    constraints = root / "packaging/constraints-windows-py312.txt"
    for line in constraints.read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.lstrip().startswith("#"):
            name, expected = line.strip().split("==", 1)
            if importlib.metadata.version(name) != expected:
                raise ReleaseError("Dependency snapshot mismatch: " + name)
    identity = uuid4().hex
    stage = root / "build" / "release-candidates" / identity
    stage.mkdir(parents=True)
    print("Protecting source and checking restoration / 保护源码并验证恢复", flush=True)
    snapshot = backup_source(root, backups)
    frozen = stage / "source"
    restore_source(snapshot, frozen)
    # Only allowlisted source participates; the restored bare history is not build input.
    hashes = source_hashes(frozen)
    info = write_build_metadata(root, stage / "metadata", identity)
    if source_digest(hashes) != info["source_digest"]:
        raise ReleaseError("Source changed after backup; start a fresh release.")
    dependencies = {
        dist.metadata["Name"]: dist.version
        for dist in importlib.metadata.distributions()
        if dist.metadata["Name"]
    }
    _json(stage / "dependencies.json", dependencies)
    for name, args in (
        ("compile", ["-m", "compileall", "-q", "src", "apps", "scripts"]),
        ("lint", ["-m", "ruff", "check", "src", "apps", "tests", "scripts"]),
        ("pytest", ["-m", "pytest", "-q", "--tb=short"]),
    ):
        print("Checking " + name + " / 检查 " + name, flush=True)
        run_gate([sys.executable, *args], frozen, stage / (name + ".log"))
    if hashes != source_hashes(frozen):
        raise ReleaseError("Frozen source changed during checks.")
    package = stage / "package"
    print("Building the fixed desktop executable / 构建固定桌面程序", flush=True)
    run_gate(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(frozen / "packaging/build_windows.ps1"),
            "-Target",
            "Desktop",
            "-Python",
            sys.executable,
            "-OutputDirectory",
            str(package),
            "-MetadataDirectory",
            str(stage / "metadata"),
        ],
        frozen,
        stage / "build.log",
    )
    from scripts.audit_package import audit_package

    executable = package / EXE
    _json(stage / "package-audit.json", audit_package(frozen, executable, info))
    if hashes != source_hashes(frozen):
        raise ReleaseError("Frozen source changed during build.")
    manifest = ReleaseManifest(
        **info,
        created_at=datetime.now(UTC).isoformat(),
        sha256=digest(executable),
        checks={name: "passed" for name in ("compile", "lint", "pytest", "package", "smoke")},
    )
    _json(stage / "manifest.json", manifest.model_dump())
    _json(stage / "source-hashes.json", hashes)
    (stage / "release-notes.md").write_text(
        f"# AI-SlowMatch {info['version']}\n\n"
        "English: Verified local development build. Real AI and physical microphone acceptance "
        "are recorded separately; this is not a public release.\n\n"
        "中文版：经验证的本地开发构建。真实 AI 与实体麦克风验收另行记录，非公开发布。\n",
        encoding="utf-8",
    )
    if not stage_only:
        promote(root, executable, manifest)
        archive = root / "releases" / identity
        for name in (
            "dependencies.json",
            "source-hashes.json",
            "package-audit.json",
            "release-notes.md",
        ):
            shutil.copy2(stage / name, archive / name)
        print("Ready: AI-SlowMatch.exe / 已更新固定启动入口", flush=True)
        try:
            apply_retention(root, backups)
        except (OSError, ValueError):
            print(
                "Retention deferred; verified release and older copies preserved. / "
                "暂缓清理，已验证版本及旧副本继续保留。",
                flush=True,
            )
    print("Verified build / 已验证构建: " + identity, flush=True)
    return stage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["build", "promote", "rollback", "backup", "restore", "metadata"]
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--path", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--build-id")
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    backups = (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        / "AI-SlowMatch"
        / "development-backups"
    )
    try:
        if args.command == "build":
            build(root, backups, stage_only=args.stage_only)
        elif args.command == "backup":
            print(backup_source(root, backups))
        elif args.command == "metadata":
            if not args.path:
                parser.error("--path is required")
            write_build_metadata(root, args.path)
        elif args.command == "restore":
            if not args.path or not args.destination:
                parser.error("--path and --destination are required")
            restore_source(args.path, args.destination)
        elif args.command == "rollback":
            if not args.build_id:
                parser.error("--build-id is required")
            rollback(root, args.build_id)
        else:
            if not args.path:
                parser.error("--path is required")
            manifest = read_release(args.path / "manifest.json")
            promote(root, args.path / "package" / EXE, manifest)
        return 0
    except (ReleaseError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Release stopped safely / 发布已停止：" + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
