"""Portable Work runtime installer and redacted diagnostics; no downloads or model calls.

Account fingerprints are explicit ownership claims, never credentials or authentication.
Separate Windows users/devices are required for an adversarial account-isolation test.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from uuid import uuid4

PRODUCT = "AI-SlowMatch"
REPOSITORY = "onepunchman26/Anti-Dating-App-Scam"
EXECUTABLE = "SlowMatch-Work.exe"
MANIFEST = "work-release.json"
DATA_SCHEMA = 1
HEX = r"[a-f0-9]{64}"
SLOT = r"[a-f0-9]{32}"
VERSION = r"\d+\.\d+\.\d+"
RELEASE = rf"{VERSION}-[a-f0-9]{{12}}(?:-repair-[a-f0-9]{{8}})?"
MAX_FILES = 4000
MAX_TOTAL = 1_000_000_000
LICENSE_STATUS = "project_license_not_declared; bundled_dependency_notices_included"


class DistributionError(ValueError):
    """Only stable, non-private codes may reach diagnostics."""


def logical_path(path):
    """Normalize extended Win32 prefixes before policy/ownership comparisons."""
    value = os.path.abspath(path)
    if os.name == "nt":
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
    return Path(value)


def native_path(path):
    """Use supported extended paths without changing Windows protection/settings."""
    value = os.path.abspath(path)
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return Path(value)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DistributionError("invalid_json")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise DistributionError("invalid_json")
    return value


def check_path(path, *, directory=None):
    """Reject every existing reparse point; no links, junctions or hardlinked files."""
    path = Path(os.path.abspath(path))
    for item in [path, *path.parents]:
        try:
            info = native_path(item).lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise DistributionError("unsafe_path")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise DistributionError("unsafe_path")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise DistributionError("unsafe_path")
    if native_path(path).exists():
        if directory is True and not native_path(path).is_dir():
            raise DistributionError("unsafe_path")
        if directory is False and not native_path(path).is_file():
            raise DistributionError("unsafe_path")
    return path


def private_location(path):
    path = logical_path(check_path(path, directory=True))
    if any(
        part.lower().startswith("onedrive")
        or part.lower()
        in {
            ".git",
            "plugins",
            "dist",
            "build",
            "public",
            "node_modules",
        }
        for part in path.parts
    ):
        raise DistributionError("private_directory_required")
    for ancestor in [path, *path.parents]:
        if native_path(ancestor / ".git").exists():
            raise DistributionError("private_directory_required")
    for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if os.environ.get(key) and path.is_relative_to(Path(os.path.abspath(os.environ[key]))):
            raise DistributionError("private_directory_required")
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if not local or not logical_path(native_path(path).resolve()).is_relative_to(
            logical_path(native_path(local).resolve())
        ):
            raise DistributionError("local_appdata_directory_required")
    return native_path(path)


def mkdir(path):
    path = native_path(check_path(path, directory=True))
    missing = []
    parent = path
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for item in reversed(missing):
        item.mkdir(mode=0o777 if os.name == "nt" else 0o700)
        check_path(item, directory=True)
    return path.resolve(strict=True)


def read_bytes(path, limit):
    path = native_path(check_path(path, directory=False))
    before = path.stat()
    if before.st_size > limit:
        raise DistributionError("file_limit")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        actual = os.fstat(descriptor)
        if (actual.st_dev, actual.st_ino) != (before.st_dev, before.st_ino):
            raise DistributionError("file_changed")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(descriptor)
        current = check_path(path, directory=False).stat()
        if (
            len(raw) > limit
            or after.st_mtime_ns != before.st_mtime_ns
            or after.st_size != before.st_size
            or (current.st_dev, current.st_ino) != (actual.st_dev, actual.st_ino)
        ):
            raise DistributionError("file_changed")
        return raw
    finally:
        os.close(descriptor)


def atomic(path, value):
    path = native_path(path)
    check_path(path, directory=False)
    temporary = path.parent / (".pending-" + uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        check_path(path, directory=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def relative_name(value):
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        raise DistributionError("unsafe_manifest_path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or ":" in value
        or any(part in {".", "..", ""} or part.endswith((".", " ")) for part in path.parts)
        or any(
            re.fullmatch(r"(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?", part)
            for part in path.parts
        )
        or path.as_posix() != value
    ):
        raise DistributionError("unsafe_manifest_path")
    return path


def manifest(package, *, verify_files=True):
    package = check_path(package, directory=True).resolve(strict=True)
    raw = read_bytes(package / MANIFEST, 2_000_000)
    value = _json(raw)
    expected = {
        "schema_version",
        "product",
        "repository",
        "version",
        "channel",
        "platform",
        "entrypoint",
        "data_schema",
        "source_commit",
        "source_digest",
        "files",
        "dependencies",
        "license_status",
        "service_origin",
        "source_dirty",
    }
    if (
        set(value) != expected
        or value["schema_version"] != 1
        or value["product"] != PRODUCT
        or value["repository"] != REPOSITORY
        or value["entrypoint"] != EXECUTABLE
        or value["channel"] != "controlled-preview"
        or value["platform"] != "windows-x64"
        or not re.fullmatch(VERSION, value["version"])
        or not re.fullmatch(r"[a-f0-9]{40}", value["source_commit"])
        or not re.fullmatch(HEX, value["source_digest"])
        or type(value["source_dirty"]) is not bool
        or value["license_status"] != LICENSE_STATUS
        or not re.fullmatch(r"https://[a-z0-9.-]+\.chatgpt\.site", value["service_origin"])
        or not isinstance(value["dependencies"], dict)
        or not isinstance(value["files"], dict)
        or len(value["files"]) > MAX_FILES
    ):
        raise DistributionError("invalid_release_manifest")
    if value["data_schema"] != DATA_SCHEMA:
        raise DistributionError("data_schema_upgrade_not_supported")
    if EXECUTABLE not in value["files"]:
        raise DistributionError("missing_entrypoint")
    total = 0
    expected_files = {MANIFEST}
    folded_files = {MANIFEST.casefold()}
    for name, detail in value["files"].items():
        relative_name(name)
        if name.casefold() in folded_files:
            raise DistributionError("duplicate_component_path")
        folded_files.add(name.casefold())
        if (
            set(detail) != {"sha256", "size"}
            or not re.fullmatch(HEX, detail["sha256"])
            or type(detail["size"]) is not int
            or not 0 <= detail["size"] <= 300_000_000
        ):
            raise DistributionError("invalid_component_manifest")
        total += detail["size"]
        if total > MAX_TOTAL:
            raise DistributionError("package_limit")
        if verify_files:
            component = read_bytes(package / name, detail["size"])
            if len(component) != detail["size"] or digest(component) != detail["sha256"]:
                raise DistributionError("component_integrity_failed")
        expected_files.add(name)
    if not verify_files:
        check_path(package / EXECUTABLE, directory=False)
        return value, digest(raw)
    actual = set()
    for root, directories, files in os.walk(package, followlinks=False):
        for name in directories:
            check_path(Path(root) / name, directory=True)
        for name in files:
            item = check_path(Path(root) / name, directory=False)
            actual.add(item.relative_to(package).as_posix())
            if len(actual) > MAX_FILES + 1:
                raise DistributionError("package_limit")
    if actual != expected_files:
        raise DistributionError("unexpected_package_file")
    return value, digest(raw)


def owner_identity():
    if os.name == "nt":
        binary = Path(os.environ["SystemRoot"]) / "System32" / "whoami.exe"
        result = subprocess.run(
            [str(binary), "/user", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        identity = next(csv.reader(io.StringIO(result.stdout)))[1]
        if not re.fullmatch(r"S-1-[\d-]+", identity):
            raise DistributionError("os_owner_unavailable")
    else:
        identity = str(os.getuid())
    return digest(("slowmatch-os-owner-v1\n" + identity).encode())


def default_home():
    if os.name != "nt" or not os.environ.get("LOCALAPPDATA"):
        raise DistributionError("supported_windows_required")
    return Path(os.environ["LOCALAPPDATA"]) / PRODUCT / "portable"


@contextmanager
def locked(home):
    from anti_dating_scam.services.work_profile import WorkStorage

    with WorkStorage(home)._writer(home):
        yield


class Distribution:
    def write_daily_launcher(self, release):
        if not re.fullmatch(RELEASE, release):
            raise DistributionError("invalid_release")
        target = check_path(self.home / "Start-SlowMatch.cmd", directory=False)
        content = (
            "@echo off\r\nREM AI-SlowMatch managed daily launcher\r\n"
            '"%~dp0releases\\' + release + '\\SlowMatch-Work.exe" launch\r\n'
            "if errorlevel 1 pause\r\n"
        )
        if target.exists() and b"AI-SlowMatch managed daily launcher" not in read_bytes(
            target, 4096
        ):
            raise DistributionError("unrecognized_launcher_preserved")
        temporary = self.home / (".pending-" + uuid4().hex)
        try:
            with temporary.open("xb") as stream:
                stream.write(content.encode("ascii"))
                stream.flush()
                os.fsync(stream.fileno())
            check_path(target, directory=False)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def __init__(self, home=None):
        self.home = private_location(home or default_home())
        self.home = mkdir(self.home)
        private_location(self.home)
        self.releases = mkdir(self.home / "releases")
        self.accounts = private_location(self.home.parent / "accounts")

    def active(self):
        pointer = _json(read_bytes(self.home / "active.json", 4096))
        if (
            set(pointer) != {"schema_version", "release", "version", "manifest_sha256"}
            or pointer["schema_version"] != 1
            or not re.fullmatch(RELEASE, pointer["release"])
            or not re.fullmatch(VERSION, pointer["version"])
            or not re.fullmatch(HEX, pointer["manifest_sha256"])
        ):
            raise DistributionError("invalid_active_pointer")
        return pointer

    def checked_active(self, *, full=True):
        pointer = self.active()
        package = self.releases / pointer["release"]
        value, checksum = manifest(package, verify_files=full)
        if checksum != pointer["manifest_sha256"] or value["version"] != pointer["version"]:
            raise DistributionError("active_integrity_failed")
        return pointer, value, package

    def recover_active_pointer(self, incoming_checksum):
        """Recover only one unambiguous, fully verified identical release."""
        try:
            broken = read_bytes(self.home / "active.json", 4096)
        except (OSError, DistributionError):
            raise DistributionError("active_pointer_unrecoverable") from None
        candidates = [item for item in self.releases.iterdir() if re.fullmatch(RELEASE, item.name)]
        if len(candidates) != 1:
            raise DistributionError("active_pointer_recovery_ambiguous")
        package = candidates[0]
        try:
            value, checksum = manifest(package)
        except (OSError, ValueError, TypeError):
            raise DistributionError("verified_installed_release_required") from None
        if checksum != incoming_checksum or not package.name.startswith(
            value["version"] + "-" + checksum[:12]
        ):
            raise DistributionError("active_pointer_recovery_requires_same_release")
        recovery = mkdir(self.home / "pointer-recovery")
        target = recovery / (digest(broken) + ".json")
        if not target.exists():
            if len(list(recovery.iterdir())) >= 5:
                raise DistributionError("pointer_recovery_limit")
            atomic(
                target,
                {"schema_version": 1, "sha256": digest(broken), "pointer_bytes_hex": broken.hex()},
            )
        return {
            "schema_version": 1,
            "release": package.name,
            "version": value["version"],
            "manifest_sha256": checksum,
        }

    def _remove_managed(self, path):
        path = check_path(path, directory=True)
        # Confirm the resolved absolute target before any recursive operation.
        if path.parent.resolve() != self.releases.resolve() or path == self.releases:
            raise DistributionError("unsafe_cleanup")
        if not (
            re.fullmatch(RELEASE, path.name) or re.fullmatch(r"\.staging-[a-f0-9]{32}", path.name)
        ):
            raise DistributionError("unsafe_cleanup")
        for root, directories, files in os.walk(path, followlinks=False):
            for name in directories:
                check_path(Path(root) / name, directory=True)
            for name in files:
                check_path(Path(root) / name, directory=False)
        shutil.rmtree(path)

    @staticmethod
    def probe(package, expected_version):
        if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
            raise DistributionError("supported_windows_x64_required")
        result = subprocess.run(
            [str(package / EXECUTABLE), "_runtime-check"],
            capture_output=True,
            timeout=30,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode or len(result.stdout) > 4096:
            raise DistributionError("runtime_probe_failed")
        data = _json(result.stdout)
        if data.get("ok") is not True or data.get("version") != expected_version:
            raise DistributionError("runtime_probe_failed")

    def install(self, package, *, repair=False, expected_manifest=None):
        value, checksum = manifest(package)
        if expected_manifest is not None and checksum != expected_manifest:
            raise DistributionError("release_checksum_mismatch")
        package = Path(package).resolve(strict=True)
        with locked(self.home):
            recovered_pointer = False
            previous = None
            if (self.home / "active.json").exists():
                try:
                    previous = self.active()
                except (DistributionError, OSError, ValueError, TypeError):
                    if not repair:
                        raise DistributionError("active_pointer_invalid_use_repair") from None
                    previous = self.recover_active_pointer(checksum)
                    recovered_pointer = True
            if previous and tuple(map(int, value["version"].split("."))) < tuple(
                map(int, previous["version"].split("."))
            ):
                raise DistributionError("downgrade_not_supported")
            # A killed install can only leave a reserved staging folder. Retry
            # cleans this before even an otherwise-idempotent return.
            for child in self.releases.iterdir():
                if re.fullmatch(r"\.staging-[a-f0-9]{32}", child.name):
                    self._remove_managed(child)
            if previous and previous["manifest_sha256"] == checksum and not recovered_pointer:
                try:
                    self.checked_active()
                    self.probe(self.releases / previous["release"], value["version"])
                    self.write_daily_launcher(previous["release"])
                    return {
                        "ok": True,
                        "status": "already_installed",
                        "version": value["version"],
                        "data_preserved": True,
                        "model_calls": 0,
                    }
                except (DistributionError, OSError):
                    if not repair:
                        raise DistributionError("repair_required") from None
            staging = self.releases / (".staging-" + uuid4().hex)
            mkdir(staging)
            try:
                for name in [*value["files"], MANIFEST]:
                    source = package / name
                    destination = staging / name
                    mkdir(destination.parent)
                    with destination.open("xb") as output:
                        output.write(read_bytes(source, 300_000_000))
                        output.flush()
                        os.fsync(output.fileno())
                _, staged_checksum = manifest(staging)
                if staged_checksum != checksum:
                    raise DistributionError("package_changed_during_copy")
                self.probe(staging, value["version"])
                name = value["version"] + "-" + checksum[:12]
                target = self.releases / name
                if target.exists():
                    try:
                        _, existing = manifest(target)
                    except (DistributionError, OSError):
                        existing = None
                    if existing == checksum:
                        self._remove_managed(staging)
                    else:
                        name += "-repair-" + uuid4().hex[:8]
                        target = self.releases / name
                        os.replace(staging, target)
                else:
                    os.replace(staging, target)
                # Data schema is checked before activation; no data migration runs.
                pointer = {
                    "schema_version": 1,
                    "release": name,
                    "version": value["version"],
                    "manifest_sha256": checksum,
                }
                if previous:
                    atomic(self.home / "previous.json", previous)
                atomic(self.home / "active.json", pointer)
                self.write_daily_launcher(name)
            finally:
                if staging.exists():
                    self._remove_managed(staging)
        return {
            "ok": True,
            "status": "repaired_active_pointer" if recovered_pointer else "installed",
            "version": value["version"],
            "data_preserved": True,
            "model_calls": 0,
        }

    def binding(self, account_key, scope):
        if not re.fullmatch(HEX, account_key or "") or not re.fullmatch(
            r"production|test:[a-z0-9][a-z0-9_-]{0,39}", scope or ""
        ):
            raise DistributionError("explicit_account_binding_required")
        # Ordinary calls inspect only the pinned small manifest. Full binary
        # hashing belongs to installation, repair and explicitly requested doctor.
        _, release, _ = self.checked_active(full=False)
        return digest(
            encoded(
                {
                    "service_origin": release["service_origin"],
                    "account_fingerprint": account_key,
                    "scope": scope,
                }
            )
        )

    def create_slot(self, account_key, scope, confirmed=False):
        if confirmed is not True:
            raise DistributionError("owner_confirmation_required")
        binding = self.binding(account_key, scope)
        owner = owner_identity()
        with locked(self.home):
            mkdir(self.accounts)
            # Index is local binding metadata; diagnostics never return its contents.
            index_path = self.home / "slots.json"
            index = _json(read_bytes(index_path, 100_000)) if index_path.exists() else {}
            # Deterministic opaque location makes interruption before index
            # persistence recoverable without scanning private records.
            slot = digest(encoded(["slowmatch-slot-v1", binding, owner]))[:32]
            if len(index) >= 100 and slot not in index:
                raise DistributionError("slot_limit")
            location = mkdir(self.accounts / slot)
            existing = (location / "owner.json").exists()
            if existing:
                self.slot(slot, account_key, scope)
            else:
                atomic(
                    location / "owner.json",
                    {
                        "schema_version": 1,
                        "binding": binding,
                        "os_owner": owner,
                        "data_schema": DATA_SCHEMA,
                    },
                )
            from anti_dating_scam.services.work_profile import WorkProfileService

            WorkProfileService(location / "work")
            index[slot] = {"binding": binding, "os_owner": owner}
            atomic(index_path, index)
            return {
                "ok": True,
                "slot": slot,
                "status": "existing_owner_slot" if existing else "created_owner_slot",
                "authentication": "caller_claim_requires_current_remote_verification",
            }

    def slot(self, slot, account_key, scope):
        if not re.fullmatch(SLOT, slot or ""):
            raise DistributionError("explicit_slot_required")
        binding = self.binding(account_key, scope)
        location = private_location(self.accounts / slot)
        data = _json(read_bytes(location / "owner.json", 4096))
        if data != {
            "schema_version": 1,
            "binding": binding,
            "os_owner": owner_identity(),
            "data_schema": DATA_SCHEMA,
        }:
            raise DistributionError("owner_binding_mismatch")
        return location / "work"

    def doctor(self, slot=None, account_key=None, scope=None):
        pointer, _, package = self.checked_active()
        self.probe(package, pointer["version"])
        ownership = "not_checked"
        if any((slot, account_key, scope)):
            location = self.slot(slot, account_key, scope)
            check_path(location, directory=True)
            ownership = "passed_local_binding_only"
        return {
            "ok": True,
            "version": pointer["version"],
            "channel": "controlled-preview",
            "checks": {
                "package_integrity": "passed",
                "terminal_runtime": "passed",
                "owner_slot": ownership,
                "native_chatgpt": "not_checked",
                "remote_authenticated_identity": "not_checked",
                "two_independent_accounts": "not_checked",
            },
            "next_step": "verify_current_account_and_native_tool_call",
            "model_calls": 0,
        }

    def local_probe(self, slot, account_key, scope):
        location = self.slot(slot, account_key, scope)
        probe = mkdir(location.parent / "probe")
        target = probe / ("check-" + uuid4().hex + ".json")
        value = {"synthetic": True, "purpose": "local_tool_read_write_check", "revision": 1}
        try:
            atomic(target, value)
            if _json(read_bytes(target, 1024)) != value:
                raise DistributionError("local_probe_failed")
        finally:
            check_path(target, directory=False).unlink(missing_ok=True)
        return {
            "ok": True,
            "local_read_write": "passed_synthetic_only",
            "private_profile_read": False,
            "native_caller": "not_independently_verified",
            "remote_authentication": "not_checked",
            "model_calls": 0,
        }

    def register_plugin(self):
        pointer, _, package = self.checked_active()
        cli = shutil.which("codex")
        if not cli:
            raise DistributionError("supported_plugin_installer_unavailable")

        def invoke(command):
            result = subprocess.run(
                [cli, *command],
                capture_output=True,
                timeout=60,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if result.returncode:
                raise DistributionError("native_plugin_registration_failed")
            if len(result.stdout) > 1_000_000:
                raise DistributionError("native_installer_output_limit")
            return result.stdout

        def inventory():
            value = _json(invoke(["plugin", "marketplace", "list", "--json"]))
            entries = value.get("marketplaces")
            if not isinstance(entries, list) or len(entries) > 100:
                raise DistributionError("native_marketplace_inventory_invalid")
            matches = [
                entry
                for entry in entries
                if isinstance(entry, dict) and entry.get("name") == "slowmatch-local"
            ]
            if len(matches) > 1 or (matches and not isinstance(matches[0].get("root"), str)):
                raise DistributionError("native_marketplace_inventory_invalid")
            if matches and len(matches[0]["root"]) > 4000:
                raise DistributionError("native_marketplace_inventory_invalid")
            return Path(matches[0]["root"]) if matches else None

        def same(left, right):
            return logical_path(native_path(left).resolve()) == logical_path(
                native_path(right).resolve()
            )

        self.verify_owned_marketplace(package)
        previous = inventory()
        migrating = previous is not None and not same(previous, package)
        if migrating:
            self.verify_owned_marketplace(previous)
            invoke(["plugin", "marketplace", "remove", "slowmatch-local", "--json"])
        try:
            if previous is None or migrating:
                invoke(["plugin", "marketplace", "add", str(logical_path(package)), "--json"])
            invoke(["plugin", "add", "slowmatch@slowmatch-local", "--json"])
        except (DistributionError, OSError, ValueError):
            if migrating:
                try:
                    current = inventory()
                    if current is not None and same(current, package):
                        invoke(["plugin", "marketplace", "remove", "slowmatch-local", "--json"])
                    elif current is not None and not same(current, previous):
                        raise DistributionError("native_marketplace_rollback_conflict")
                    if current is None or not same(current, previous):
                        invoke(
                            ["plugin", "marketplace", "add", str(logical_path(previous)), "--json"]
                        )
                except (DistributionError, OSError, ValueError):
                    raise DistributionError("native_marketplace_rollback_failed") from None
                raise DistributionError(
                    "native_registration_failed_previous_source_restored"
                ) from None
            raise
        atomic(
            self.home / "plugin-registration.json",
            {"release": pointer["release"], "status": "installer_completed"},
        )
        return {
            "ok": True,
            "status": "native_installer_completed",
            "owned_marketplace_migrated": migrating,
            "native_chatgpt_loading": "not_checked",
            "model_calls": 0,
        }

    def verify_owned_marketplace(self, package):
        """Only our exact single-plugin marketplace and recognized source may move."""
        try:
            package = native_path(check_path(package, directory=True)).resolve(strict=True)
            marketplace = _json(read_bytes(package / ".agents/plugins/marketplace.json", 100_000))
            plugin = _json(read_bytes(package / "plugins/slowmatch/plugin.json", 100_000))
            entries = marketplace.get("plugins")
            if (
                marketplace.get("name") != "slowmatch-local"
                or not isinstance(entries, list)
                or len(entries) != 1
                or entries[0].get("name") != "slowmatch"
                or entries[0].get("source") != {"source": "local", "path": "./plugins/slowmatch"}
                or plugin.get("name") != "slowmatch"
                or plugin.get("author", {}).get("name") != "onepuchman"
            ):
                raise ValueError("unrecognized")
            if logical_path(package.parent) == logical_path(self.releases.resolve()):
                manifest(package)
                if not re.fullmatch(RELEASE, package.name):
                    raise ValueError("unrecognized")
                return
            config = configparser.ConfigParser(interpolation=None)
            config.read_string(read_bytes(package / ".git/config", 64_000).decode("utf-8"))
            origin = config.get('remote "origin"', "url").strip().casefold()
            repository = REPOSITORY.casefold()
            allowed = {
                f"https://github.com/{repository}",
                f"https://github.com/{repository}.git",
                f"git@github.com:{repository}.git",
                f"ssh://git@github.com/{repository}.git",
            }
            if origin not in allowed:
                raise ValueError("unrecognized")
        except (OSError, ValueError, TypeError, AttributeError, configparser.Error):
            raise DistributionError("existing_marketplace_not_verified_owned") from None

    def uninstall(self):
        with locked(self.home):
            active = self.active() if (self.home / "active.json").exists() else None
            # Disable future calls first. Never delete accounts/configuration.
            if active:
                atomic(self.home / "uninstalled.json", active)
                check_path(self.home / "active.json", directory=False).unlink()
            pending = 0
            for child in self.releases.iterdir():
                if re.fullmatch(RELEASE, child.name) or re.fullmatch(
                    r"\.staging-[a-f0-9]{32}", child.name
                ):
                    try:
                        self._remove_managed(child)
                    except PermissionError:
                        # Windows can lock the executable currently running this
                        # command. Re-run uninstall from the extracted download.
                        pending += 1
        return {
            "ok": True,
            "status": "runtime_deactivated_cleanup_pending" if pending else "runtime_uninstalled",
            "private_data_preserved": True,
            "configuration_preserved": True,
            "locked_release_directories": pending,
            "plugin_removal": "use_supported_client_plugin_removal",
            "model_calls": 0,
        }


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise DistributionError("invalid_arguments")


def runtime_check():
    import ssl

    from anti_dating_scam.version import build_info
    from anti_dating_scam.work_cli import dispatch

    operations = dispatch("schema", {"compact": True})["operations"]
    try:
        context = ssl.create_default_context()
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise DistributionError("tls_verification_required")
    except OSError:
        raise DistributionError("tls_runtime_unavailable") from None
    return {
        "ok": True,
        "version": build_info()["version"],
        "operation_count": len(operations),
        "tls_verification": "ready",
        "model_calls": 0,
    }


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        parser = Parser(description="AI-SlowMatch controlled-preview runtime / 受控预览运行组件")
        sub = parser.add_subparsers(dest="command", required=True)
        companion = sub.add_parser("companion")
        companion.add_argument("--state-root", type=Path)
        companion.add_argument("--no-browser", action="store_true")
        launch = sub.add_parser("launch")
        launch.add_argument("--state-root", type=Path)
        launch.add_argument("--no-browser", action="store_true")
        for name in (
            "install",
            "repair",
            "doctor",
            "uninstall",
            "register-plugin",
            "slot-create",
            "run",
        ):
            command = sub.add_parser(name)
            command.add_argument("--home", type=Path)
            if name in {"install", "repair"}:
                command.add_argument("--package", type=Path, default=Path(sys.executable).parent)
                command.add_argument("--expected-manifest-sha256")
            if name in {"doctor", "slot-create", "run"}:
                command.add_argument("--account-key")
                command.add_argument("--scope")
            if name in {"doctor", "run"}:
                command.add_argument("--slot")
            if name == "slot-create":
                command.add_argument("--confirmed", action="store_true")
            if name == "run":
                command.add_argument("operation")
                command.add_argument("--input-json", default="-")
        sub.add_parser("_runtime-check")
        schema = sub.add_parser("schema")
        schema.add_argument("--operation")
        schema.add_argument("--object")
        args = parser.parse_args(argv)
        if args.command == "companion":
            from anti_dating_scam.api.web_companion import main as companion_main

            options = ["--state-root", str(args.state_root)] if args.state_root else []
            if args.no_browser:
                options.append("--no-browser")
            companion_main(options)
            return 0
        elif args.command == "launch":
            from anti_dating_scam.services.local_launcher import launch

            result = launch(state_root=args.state_root, open_browser=not args.no_browser)
        elif args.command == "_runtime-check":
            result = runtime_check()
        elif args.command == "schema":
            from anti_dating_scam.work_cli import dispatch

            arguments = (
                {"operation": args.operation}
                if args.operation
                else {"object": args.object}
                if args.object
                else {"compact": True}
            )
            if args.operation and args.object:
                raise DistributionError("invalid_arguments")
            result = {"ok": True, "result": dispatch("schema", arguments)}
        else:
            distribution = Distribution(args.home)
            if args.command in {"install", "repair"}:
                result = distribution.install(
                    args.package,
                    repair=args.command == "repair",
                    expected_manifest=args.expected_manifest_sha256,
                )
            elif args.command == "doctor":
                result = distribution.doctor(args.slot, args.account_key, args.scope)
            elif args.command == "slot-create":
                result = distribution.create_slot(args.account_key, args.scope, args.confirmed)
            elif args.command == "run":
                location = distribution.slot(args.slot, args.account_key, args.scope)
                raw = (
                    sys.stdin.buffer.read(2_000_001)
                    if args.input_json == "-"
                    else read_bytes(Path(args.input_json), 2_000_000)
                )
                if len(raw) > 2_000_000:
                    raise DistributionError("input_limit")
                from anti_dating_scam.services.report_review import _decode
                from anti_dating_scam.work_cli import dispatch

                arguments = _decode(raw)
                if args.operation == "local-probe":
                    if arguments:
                        raise DistributionError("invalid_arguments")
                    result = distribution.local_probe(args.slot, args.account_key, args.scope)
                else:
                    result = {"ok": True, "result": dispatch(args.operation, arguments, location)}
            else:
                result = getattr(distribution, args.command.replace("-", "_"))()
        code = 0
    except Exception as error:
        # Private input, source paths and third-party stderr never enter diagnostics.
        try:
            from anti_dating_scam.services.local_launcher import LaunchError
            from anti_dating_scam.services.work_profile import WorkProfileError

            known = isinstance(error, (DistributionError, WorkProfileError, LaunchError))
        except ImportError:
            known = isinstance(error, DistributionError)
        value = str(error) if known else "operation_failed"
        result = {"ok": False, "error": {"code": value}, "model_calls": 0}
        code = 1
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
