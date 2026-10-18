"""Maintainer-only, pinned Windows onedir build; never installs or downloads.

The payload is PyInstaller's runtime plus an explicit public file allowlist.
ZIP metadata/order are deterministic; reproducible binary bytes across build
machines are not claimed. Source dirty state and dependency versions are recorded.
"""

from __future__ import annotations

import importlib.metadata
import json
import marshal
import os
import platform
import shutil
import subprocess
import sys
import tomllib
import types
import zipfile
from pathlib import Path

try:
    from scripts import work_distribution_runtime as runtime
except ModuleNotFoundError:
    import work_distribution_runtime as runtime

SERVICE_ORIGIN = "https://slowmatch-private-pilot.fizzydeer7.chatgpt.site"
PUBLIC_FILES = {
    ".agents/plugins/marketplace.json": ".agents/plugins/marketplace.json",
    "plugins/slowmatch/plugin.json": "plugins/slowmatch/plugin.json",
    "plugins/slowmatch/.app.json": "plugins/slowmatch/.app.json",
    "plugins/slowmatch/CREDITS.md": "plugins/slowmatch/CREDITS.md",
    **{
        f"plugins/slowmatch/licenses/{name}.txt": f"plugins/slowmatch/licenses/{name}.txt"
        for name in ("goutoujunshi-MIT", "goutoujunshi-MIT-zh")
    },
    "plugins/slowmatch/scripts/work.ps1": "plugins/slowmatch/scripts/work.ps1",
    "plugins/slowmatch/skills/setup/SKILL.md": "plugins/slowmatch/skills/setup/SKILL.md",
    "plugins/slowmatch/skills/slowmatch/SKILL.md": "plugins/slowmatch/skills/slowmatch/SKILL.md",
    **{
        name: name
        for name in (
            "plugins/slowmatch/skills/slowmatch/references/activity-planning.md",
            "plugins/slowmatch/skills/slowmatch/references/direction.md",
            "plugins/slowmatch/skills/slowmatch/references/profile-tools.md",
            "plugins/slowmatch/skills/slowmatch/references/reflection.md",
            "plugins/slowmatch/skills/slowmatch/references/relationship-support.md",
            "plugins/slowmatch/skills/slowmatch/references/site-reminder.md",
        )
    },
    "INSTALL_WITH_CHATGPT.md": "INSTALL_WITH_CHATGPT.md",
    "CONTROLLED_TEST.md": "CONTROLLED_TEST.md",
    "docs/DISTRIBUTION_HELP.md": "docs/DISTRIBUTION_HELP.md",
    "docs/LICENSING_STATUS.md": "docs/LICENSING_STATUS.md",
    "scripts/controlled_test_fixtures.ps1": "tools/controlled-test.ps1",
    "src/anti_dating_scam/licenses/open-source-credits.txt": "LICENSES/project-credits.txt",
}
# This small runtime deliberately omits the optional Vosk native runtime/models,
# GUI, web server, provider adapters and test/development packages.
DEPENDENCIES = (
    "pydantic",
    "pydantic_core",
    "annotated-types",
    "typing-inspection",
    "typing_extensions",
    "pyinstaller",
    "pyinstaller-hooks-contrib",
    "altgraph",
    "packaging",
    "pefile",
    "pywin32-ctypes",
)
SOURCE_FILES = (
    "pyproject.toml",
    "packaging/constraints-windows-py312.txt",
    "scripts/work_distribution_runtime.py",
    "scripts/work_distribution_build.py",
    "src/anti_dating_scam/__init__.py",
    "src/anti_dating_scam/version.py",
    "src/anti_dating_scam/work_cli.py",
    "src/anti_dating_scam/models/__init__.py",
    "src/anti_dating_scam/models/work_profile.py",
    "src/anti_dating_scam/models/work_planning.py",
    "src/anti_dating_scam/models/relationship_support.py",
    "src/anti_dating_scam/services/__init__.py",
    "src/anti_dating_scam/services/work_profile.py",
    "src/anti_dating_scam/services/work_planning.py",
    "src/anti_dating_scam/services/relationship_support.py",
    "src/anti_dating_scam/services/report_review.py",
    "src/anti_dating_scam/services/personal_model.py",
    "src/anti_dating_scam/services/relationship_memory.py",
    "src/anti_dating_scam/services/voice_input.py",
    "src/anti_dating_scam/reports/__init__.py",
    "src/anti_dating_scam/reports/local_artifacts.py",
)


def dependency_versions(root):
    pins = {}
    raw = runtime.read_bytes(root / "packaging/constraints-windows-py312.txt", 100_000).decode()
    for line in raw.splitlines():
        if "==" in line and not line.startswith("#"):
            name, version = line.strip().split("==", 1)
            pins[name.lower().replace("_", "-")] = version
    versions = {}
    for name in DEPENDENCIES:
        version = importlib.metadata.version(name)
        if pins.get(name.lower().replace("_", "-")) != version:
            raise runtime.DistributionError("pinned_build_dependency_mismatch")
        versions[name] = version
    return {"python": platform.python_version(), **versions}


def public_sources(root):
    sources = sorted(set(SOURCE_FILES) | set(PUBLIC_FILES))
    # Enumerate only named public build sources; never walk the developer tree.
    hashes = {name: runtime.digest(runtime.read_bytes(root / name, 2_000_000)) for name in sources}
    git = shutil.which("git")
    if not git:
        raise runtime.DistributionError("maintainer_git_required")
    commit = subprocess.run(
        [git, "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True, timeout=15
    ).stdout.strip()
    changed = subprocess.run(
        [git, "status", "--porcelain", "--", *sources],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    ).stdout
    return {
        "source_commit": commit,
        "source_dirty": bool(changed),
        "source_digest": runtime.digest(runtime.encoded(hashes)),
        "source_files": hashes,
    }


def copy_public(root, payload, source_hashes=None):
    for source, destination in PUBLIC_FILES.items():
        target = payload / destination
        runtime.mkdir(target.parent)
        raw = runtime.read_bytes(root / source, 2_000_000)
        if source_hashes is not None and runtime.digest(raw) != source_hashes.get(source):
            raise runtime.DistributionError("build_sources_changed")
        target.write_bytes(raw)


def copy_notices(payload):
    notices = runtime.mkdir(payload / "LICENSES")
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    (notices / "Python-LICENSE.txt").write_bytes(runtime.read_bytes(python_license, 2_000_000))
    for name in DEPENDENCIES:
        distribution = importlib.metadata.distribution(name)
        files = [
            file
            for file in distribution.files or []
            if ".dist-info/" in str(file).replace("\\", "/")
            and any(
                word in file.name.lower() for word in ("license", "licence", "copying", "notice")
            )
        ]
        if not files:
            raise runtime.DistributionError("dependency_notice_missing")
        target = runtime.mkdir(notices / name)
        for number, file in enumerate(sorted(files, key=str)):
            # Keep original notice text; no source/developer directory is recorded.
            filename = f"{number:02d}-" + file.name
            (target / filename).write_bytes(
                runtime.read_bytes(distribution.locate_file(file), 2_000_000)
            )


def package_manifest(payload, version, provenance, dependencies):
    files = {}
    for path in sorted(payload.rglob("*")):
        runtime.check_path(path)
        if path.is_file():
            name = path.relative_to(payload).as_posix()
            runtime.relative_name(name)
            raw = runtime.read_bytes(path, 300_000_000)
            files[name] = {"sha256": runtime.digest(raw), "size": len(raw)}
    value = {
        "schema_version": 1,
        "product": runtime.PRODUCT,
        "repository": runtime.REPOSITORY,
        "version": version,
        "channel": "controlled-preview",
        "platform": "windows-x64",
        "entrypoint": runtime.EXECUTABLE,
        "data_schema": runtime.DATA_SCHEMA,
        **{key: provenance[key] for key in ("source_commit", "source_dirty", "source_digest")},
        "files": files,
        "dependencies": dependencies,
        "license_status": runtime.LICENSE_STATUS,
        "service_origin": SERVICE_ORIGIN,
    }
    (payload / runtime.MANIFEST).write_bytes(runtime.encoded(value))
    runtime.manifest(payload)
    return value


def clean_generated_metadata(payload):
    """Remove only PyInstaller-copied editable project installation metadata.

    Frozen version.py reads generated build_info.json; the developer environment's
    project dist-info is neither required nor a valid source of release identity.
    """
    internal = runtime.check_path(payload / "_internal", directory=True).resolve(strict=True)
    for child in internal.iterdir():
        if child.name.lower().startswith("anti_dating_scam-") and child.name.endswith(".dist-info"):
            child = runtime.check_path(child, directory=True)
            if child.resolve().parent != internal:
                raise runtime.DistributionError("unsafe_generated_metadata_path")
            for path in child.rglob("*"):
                runtime.check_path(path)
            # Confirmed absolute target is an immediate generated child of this
            # exact payload, never the installed developer environment.
            shutil.rmtree(child)


def audit_developer_paths(payload, root):
    forbidden = set()
    for value in (root, Path.home(), Path(sys.prefix)):
        for path in (str(value), str(value.resolve()), str(runtime.logical_path(value))):
            for variant in (path, path.replace("\\", "/"), path.replace("\\", "\\\\")):
                if len(variant) > 8:
                    forbidden.add(variant.casefold().encode())
                    forbidden.add(variant.casefold().encode("utf-16le"))
    for file in payload.rglob("*"):
        if file.is_file():
            name = file.name.lower()
            if name in {"direct_url.json", ".python-version"} or name.endswith(
                (".pth", ".egg-link")
            ):
                raise runtime.DistributionError("developer_install_metadata_in_payload")
            raw = runtime.read_bytes(file, 300_000_000).lower()
            if any(value in raw for value in forbidden):
                raise runtime.DistributionError("developer_path_in_payload")


def deterministic_zip(payload, destination):
    # Archive only a fully validated manifest; no glob of user/source directories.
    value, _ = runtime.manifest(payload)
    with zipfile.ZipFile(
        destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name in sorted([*value["files"], runtime.MANIFEST]):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, runtime.read_bytes(payload / name, 300_000_000))


def audit_embedded_sources(root, executable):
    """Reuse existing desktop audit's exact-source comparison for the Work CLI."""
    from PyInstaller.archive.readers import CArchiveReader

    def verify(code, relative):
        if not isinstance(code, types.CodeType):
            raise runtime.DistributionError("invalid_embedded_code")
        pending = [code]
        while pending:
            current = pending.pop()
            if Path(current.co_filename).is_absolute() or ":" in current.co_filename:
                raise runtime.DistributionError("embedded_developer_path")
            pending.extend(
                value for value in current.co_consts if isinstance(value, types.CodeType)
            )
        actual = compile(
            runtime.read_bytes(root / relative, 2_000_000),
            code.co_filename,
            "exec",
            dont_inherit=True,
            optimize=1,
        )
        if actual != code:
            raise runtime.DistributionError("embedded_source_mismatch")

    archive = CArchiveReader(str(executable))
    pyz = archive.open_embedded_archive("PYZ.pyz")
    audited = []
    for name in pyz.toc:
        if name.startswith(("vosk", "PySide6", "anti_dating_scam_desktop")):
            raise runtime.DistributionError("unexpected_optional_runtime")
        if name == "anti_dating_scam" or name.startswith("anti_dating_scam."):
            path = "src/" + name.replace(".", "/")
            path = path + ".py" if path + ".py" in SOURCE_FILES else path + "/__init__.py"
            if path not in SOURCE_FILES:
                raise runtime.DistributionError("unlisted_embedded_project_source")
            verify(pyz.extract(name), path)
            audited.append(name)
    for required in (
        "anti_dating_scam.work_cli",
        "anti_dating_scam.services.work_profile",
        "anti_dating_scam.services.work_planning",
        "anti_dating_scam.services.relationship_support",
    ):
        if required not in audited:
            raise runtime.DistributionError("required_embedded_source_missing")
    verify(
        marshal.loads(archive.extract("work_distribution_runtime")),
        "scripts/work_distribution_runtime.py",
    )
    return {
        "source_modules": len(audited) + 1,
        "embedded_source_match": True,
        "project_code_paths": "relative",
        "optional_vosk": "not_bundled",
    }


def build(root, output, *, allow_dirty=False):
    if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise runtime.DistributionError("supported_windows_x64_required")
    if sys.version_info[:2] != (3, 12):
        raise runtime.DistributionError("pinned_python_312_required")
    root = runtime.check_path(root, directory=True).resolve(strict=True)
    output = runtime.private_location(output)
    runtime.mkdir(output)
    if any(output.iterdir()):
        raise runtime.DistributionError("empty_build_output_required")
    project = tomllib.loads(runtime.read_bytes(root / "pyproject.toml", 100_000).decode())[
        "project"
    ]
    plugin = runtime._json(runtime.read_bytes(root / "plugins/slowmatch/plugin.json", 100_000))
    if project["name"] != "anti-dating-scam" or plugin["version"] != project["version"]:
        raise runtime.DistributionError("source_version_mismatch")
    dependencies = dependency_versions(root)
    provenance = public_sources(root)
    if provenance["source_dirty"] and not allow_dirty:
        raise runtime.DistributionError("dirty_release_sources_require_explicit_override")
    generated = runtime.mkdir(output / "generated")
    build_info = {
        "version": project["version"],
        "build_id": provenance["source_digest"][:32],
        "git_commit": provenance["source_commit"],
        "dirty": provenance["source_dirty"],
    }
    (generated / "build_info.json").write_bytes(runtime.encoded(build_info))
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "SlowMatch-Work",
        "--paths",
        str(root / "src"),
        "--distpath",
        str(output / "compiled"),
        "--workpath",
        str(output / "intermediate"),
        "--specpath",
        str(output / "spec"),
        "--add-data",
        # PyInstaller's SOURCE:DEST parser recognizes normal Windows drive
        # prefixes, but not an extended \\?\ prefix. Only this CLI argument is
        # normalized; our guarded filesystem I/O keeps long-path support.
        f"{runtime.logical_path(generated / 'build_info.json')};anti_dating_scam",
        "--optimize",
        "1",
    ]
    for name in (
        "PySide6",
        "shiboken6",
        "anti_dating_scam_desktop",
        "tkinter",
        "pytest",
        "IPython",
        "vosk",
        "fastapi",
        "uvicorn",
    ):
        command.extend(["--exclude-module", name])
    command.append(str(root / "scripts/work_distribution_runtime.py"))
    # Build logs remain local; ordinary-user diagnostics never include this log.
    with (output / "maintainer-build.log").open("wb") as log:
        completed = subprocess.run(
            command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=False, timeout=600
        )
    if completed.returncode:
        raise runtime.DistributionError("maintainer_build_failed")
    # Ensure no edited build source was silently combined with the pinned digest.
    if public_sources(root) != provenance:
        raise runtime.DistributionError("build_sources_changed")
    payload = output / "compiled/SlowMatch-Work"
    clean_generated_metadata(payload)
    audit = audit_embedded_sources(root, payload / runtime.EXECUTABLE)
    copy_public(root, payload, provenance["source_files"])
    copy_notices(payload)
    if public_sources(root) != provenance:
        raise runtime.DistributionError("build_sources_changed")
    (payload / "source-provenance.json").write_bytes(runtime.encoded(provenance))
    (payload / "package-audit.json").write_bytes(runtime.encoded(audit))
    audit_developer_paths(payload, root)
    manifest = package_manifest(payload, project["version"], provenance, dependencies)
    runtime.Distribution.probe(payload, project["version"])
    # A stable archive filename is tied to the version; overwrite is forbidden.
    filename = f"AI-SlowMatch-Work-{project['version']}-windows-x64-controlled-preview.zip"
    archive = output / filename
    deterministic_zip(payload, archive)
    manifest_hash = runtime.digest(runtime.read_bytes(payload / runtime.MANIFEST, 2_000_000))
    archive_hash = runtime.digest(runtime.read_bytes(archive, runtime.MAX_TOTAL))
    sums = f"{archive_hash}  {filename}\n{manifest_hash}  {runtime.MANIFEST}\n"
    (output / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    return {
        "ok": True,
        "version": project["version"],
        "archive": filename,
        "archive_sha256": archive_hash,
        "manifest_sha256": manifest_hash,
        "source_commit": provenance["source_commit"],
        "source_dirty": provenance["source_dirty"],
        "payload_relative": "compiled/SlowMatch-Work",
        "files": len(manifest["files"]),
        "artifact_runtime_probe": "passed",
        "installation": "not_checked",
        "native_chatgpt": "not_checked",
        "model_calls": 0,
    }


def main(argv=None):
    parser = runtime.Parser(description="Maintainer Windows Work runtime build")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-dirty", action="store_true")
    try:
        args = parser.parse_args(argv)
        result = build(args.source, args.output, allow_dirty=args.allow_dirty)
        code = 0
    except Exception as error:
        result = {
            "ok": False,
            "error": {
                "code": str(error)
                if isinstance(error, runtime.DistributionError)
                else "maintainer_build_failed"
            },
        }
        code = 1
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
