"""Offline bootstrap tests: synthetic ZIPs only; no network, EXE or real installation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install_work_preview.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
WINDOWS_PS51 = Path(os.environ.get("SystemRoot", "C:/Windows")) / (
    "System32/WindowsPowerShell/v1.0/powershell.exe"
)
pytestmark = pytest.mark.skipif(
    os.name != "nt" or not POWERSHELL, reason="Windows PowerShell required"
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def make_archive(tmp_path, *, files=None, extras=(), overrides=None, modes=None):
    files = files or {
        "SlowMatch-Work.exe": b"synthetic text; never executed",
        "_internal/test.dll": b"test",
    }
    manifest = {
        "schema_version": 1,
        "version": "0.8.4",
        "repository": "onepunchman26/Anti-Dating-App-Scam",
        "product": "AI-SlowMatch",
        "channel": "controlled-preview",
        "platform": "windows-x64",
        "entrypoint": "SlowMatch-Work.exe",
        "data_schema": 1,
        "source_dirty": False,
        "source_commit": "a" * 40,
        "source_digest": "b" * 64,
        "service_origin": "https://slowmatch-private-pilot.fizzydeer7.chatgpt.site",
        "files": {name: {"sha256": sha(body), "size": len(body)} for name, body in files.items()},
        **(overrides or {}),
    }
    raw = json.dumps(manifest, separators=(",", ":")).encode()
    archive = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name, body in [*files.items(), ("work-release.json", raw), *extras]:
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ((modes or {}).get(name, stat.S_IFREG | 0o644)) << 16
            zipped.writestr(info, body)
    # ZipInfo normalizes Windows separators; preserve hostile raw names in both headers.
    for name, _ in extras:
        if "\\" in name:
            archive.write_bytes(
                archive.read_bytes().replace(name.replace("\\", "/").encode(), name.encode())
            )
    return archive, sha(archive.read_bytes()), sha(raw)


def invoke(
    tmp_path,
    archive=None,
    archive_hash="",
    manifest_hash="",
    setup="",
    action="expand",
    uri="",
    powershell=None,
    destination=None,
):
    environment = {
        **os.environ,
        "SM_TEST_SCRIPT": str(SCRIPT),
        "SM_TEST_ARCHIVE": str(archive or ""),
        "SM_TEST_DEST": str(destination or tmp_path / "unpacked"),
        "SM_TEST_ARCHIVE_HASH": archive_hash,
        "SM_TEST_MANIFEST_HASH": manifest_hash,
        "SM_TEST_URI": uri,
    }
    operation = {
        "expand": (
            "Expand-SMVerifiedArchive $env:SM_TEST_ARCHIVE $env:SM_TEST_DEST "
            "$env:SM_TEST_ARCHIVE_HASH $env:SM_TEST_MANIFEST_HASH | Out-Null; "
            "@{ok=$true} | ConvertTo-Json -Compress"
        ),
        "unready": "Invoke-SMPreviewInstall | ConvertTo-Json -Compress",
        "cache": (
            "$valid = Test-SMVerifiedCache $env:SM_TEST_ARCHIVE $env:SM_TEST_ARCHIVE_HASH; "
            "@{ok=$true; reusable=$valid} | ConvertTo-Json -Compress"
        ),
        "uri": (
            "Assert-SMDownloadUri ([Uri]$env:SM_TEST_URI); @{ok=$true} | ConvertTo-Json -Compress"
        ),
    }[action]
    code = f"""
$ErrorActionPreference = 'Stop'
. $env:SM_TEST_SCRIPT
{setup}
try {{ {operation} }}
catch {{ @{{ok=$false; error=$_.Exception.Message}} | ConvertTo-Json -Compress }}
"""
    completed = subprocess.run(
        [str(powershell or POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", code],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_valid_archive_extracts_only_manifested_bytes(tmp_path):
    archive, archive_hash, manifest_hash = make_archive(tmp_path)
    assert invoke(tmp_path, archive, archive_hash, manifest_hash) == {"ok": True}
    assert (
        tmp_path / "unpacked/SlowMatch-Work.exe"
    ).read_bytes() == b"synthetic text; never executed"
    assert {
        p.relative_to(tmp_path / "unpacked").as_posix()
        for p in (tmp_path / "unpacked").rglob("*")
        if p.is_file()
    } == {"SlowMatch-Work.exe", "_internal/test.dll", "work-release.json"}


@pytest.mark.parametrize("powershell", [POWERSHELL, WINDOWS_PS51], ids=["current", "windows51"])
def test_long_paths_extract_with_builtin_powershell_without_policy_changes(tmp_path, powershell):
    if not powershell or not Path(powershell).is_file():
        pytest.skip("PowerShell edition unavailable")
    if powershell == WINDOWS_PS51:
        policy_check = subprocess.run(
            [str(powershell), "-NoProfile", "-NonInteractive", "-Command", "Get-ExecutionPolicy"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if policy_check.returncode and "CouldNotAutoloadMatchingModule" in policy_check.stderr:
            pytest.skip(
                "Windows PowerShell 5.1 policy module unavailable in test process; no bypass"
            )
        assert policy_check.returncode == 0, policy_check.stderr
        if policy_check.stdout.strip() == "Restricted":
            pytest.skip("Windows PowerShell 5.1 script execution is Restricted; no bypass")
    archive, archive_hash, manifest_hash = make_archive(tmp_path)
    branch = tmp_path / ("a" * 90)
    destination = branch / ("b" * 90) / "unpacked"
    assert len(str(destination)) > 260
    try:
        result = invoke(
            tmp_path,
            archive,
            archive_hash,
            manifest_hash,
            powershell=powershell,
            destination=destination,
        )
        assert result == {"ok": True}
        native = Path("\\\\?\\" + str(destination))
        assert (native / "SlowMatch-Work.exe").read_bytes() == b"synthetic text; never executed"
    finally:
        # Only this test's known absolute synthetic branch; protect unrelated fixture files.
        assert branch.is_absolute() and branch.parent.resolve() == tmp_path.resolve()
        native_branch = "\\\\?\\" + str(branch)
        if os.path.isdir(native_branch):
            shutil.rmtree(native_branch)


@pytest.mark.parametrize(
    "name",
    [
        "../outside",
        "/absolute",
        "C:/absolute",
        "a\\b",
        "file:ads",
        "nul.txt",
        "COM1",
        "a/../b",
        "a//b",
        "name. ",
        "a/",
        "a\x01b",
    ],
)
def test_rejects_unsafe_paths_before_extracting(tmp_path, name):
    archive, archive_hash, manifest_hash = make_archive(tmp_path, extras=[(name, b"bad")])
    result = invoke(tmp_path, archive, archive_hash, manifest_hash)
    assert result["error"] == "SMB:unsafe_archive_path"
    assert not (tmp_path / "unpacked").exists()


@pytest.mark.parametrize(
    "extras", [[("SLOWMATCH-WORK.EXE", b"collision")], [("_internal", b"prefix collision")]]
)
def test_rejects_windows_collisions_before_extracting(tmp_path, extras):
    archive, archive_hash, manifest_hash = make_archive(tmp_path, extras=extras)
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == "SMB:archive_path_collision"
    )
    assert not (tmp_path / "unpacked").exists()


def test_rejects_zip_symlink_before_extracting(tmp_path):
    archive, archive_hash, manifest_hash = make_archive(
        tmp_path, modes={"SlowMatch-Work.exe": stat.S_IFLNK | 0o777}
    )
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == "SMB:archive_special_file_rejected"
    )


@pytest.mark.parametrize("which", ["archive", "manifest"])
def test_integrity_mismatch_stops_before_extraction(tmp_path, which):
    archive, archive_hash, manifest_hash = make_archive(tmp_path)
    if which == "archive":
        archive_hash = "0" * 64
    else:
        manifest_hash = "0" * 64
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == f"SMB:{which}_integrity_failed"
    )
    assert not (tmp_path / "unpacked").exists()


@pytest.mark.parametrize(
    "overrides",
    [
        {"version": "999.0.0"},
        {"source_dirty": True},
        {"repository": "other/repo"},
        {"service_origin": "https://other.chatgpt.site"},
    ],
)
def test_rejects_changed_release_identity(tmp_path, overrides):
    archive, archive_hash, manifest_hash = make_archive(tmp_path, overrides=overrides)
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == "SMB:release_identity_mismatch"
    )


def test_unlisted_entry_is_rejected(tmp_path):
    archive, archive_hash, manifest_hash = make_archive(
        tmp_path, extras=[("unexpected.txt", b"not allowed")]
    )
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == "SMB:manifest_entries_mismatch"
    )


def test_component_hash_mismatch_is_not_accepted(tmp_path):
    body = b"synthetic; never executed"
    files = {"SlowMatch-Work.exe": body}
    archive, archive_hash, manifest_hash = make_archive(
        tmp_path,
        files=files,
        overrides={"files": {"SlowMatch-Work.exe": {"sha256": "0" * 64, "size": len(body)}}},
    )
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == "SMB:component_integrity_failed"
    )


def test_extreme_compression_is_rejected(tmp_path):
    archive, archive_hash, manifest_hash = make_archive(
        tmp_path, files={"SlowMatch-Work.exe": b"a" * 1000001}
    )
    assert invoke(tmp_path, archive, archive_hash, manifest_hash)["error"] == "SMB:archive_limit"


@pytest.mark.parametrize("limit", ["SMEntryLimit = 2", "SMFileLimit = 10", "SMTotalLimit = 10"])
def test_archive_resource_limits_are_enforced(tmp_path, limit):
    archive, archive_hash, manifest_hash = make_archive(tmp_path)
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash, setup=f"$script:{limit}")["error"]
        == "SMB:archive_limit"
    )


def test_existing_destination_is_never_overwritten(tmp_path):
    archive, archive_hash, manifest_hash = make_archive(tmp_path)
    destination = tmp_path / "unpacked"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("unrelated synthetic work")
    assert (
        invoke(tmp_path, archive, archive_hash, manifest_hash)["error"]
        == "SMB:fresh_staging_required"
    )
    assert marker.read_text() == "unrelated synthetic work"


def test_unready_release_fails_without_filesystem_network_or_runtime(tmp_path):
    result = invoke(tmp_path, setup="$script:SMArchiveSha256 = 'UNREADY'", action="unready")
    assert result["ok"] is False
    assert result["error"] == "release_not_ready"
    assert result["model_calls"] == 0
    assert list(tmp_path.iterdir()) == []
    assert str(tmp_path) not in json.dumps(result)


def test_bootstrap_has_no_arbitrary_sources_or_policy_bypass():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "param([switch]$RegisterPlugin, [switch]$Launch)" in source
    assert (
        "releases/download/v0.8.4/AI-SlowMatch-Work-0.8.4-windows-x64-controlled-preview.zip"
        in source
    )
    assert "Expand-Archive" not in source
    assert "Invoke-Expression" not in source
    assert "Set-ExecutionPolicy" not in source
    assert "ExecutionPolicy Bypass" not in source
    assert "slot-create" not in source


def test_invalid_public_cache_is_preserved_and_fresh_download_can_be_used(tmp_path):
    archive, _, _ = make_archive(tmp_path)
    original = archive.read_bytes()
    result = invoke(tmp_path, archive, "0" * 64, action="cache")
    assert result == {"ok": True, "reusable": False}
    assert archive.read_bytes() == original


def test_valid_public_cache_can_be_reused(tmp_path):
    archive, archive_hash, _ = make_archive(tmp_path)
    assert invoke(tmp_path, archive, archive_hash, action="cache") == {"ok": True, "reusable": True}


def test_directory_cannot_impersonate_cache(tmp_path):
    assert (
        invoke(tmp_path, tmp_path, "0" * 64, action="cache")["error"] == "SMB:cached_path_not_file"
    )


@pytest.mark.parametrize(
    "uri",
    [
        "http://github.com/asset",
        "https://attacker.invalid/asset",
        "https://github.com.attacker.invalid/asset",
        "https://user@github.com/asset",
        "https://github.com:444/asset",
    ],
)
def test_redirect_policy_rejects_untrusted_origins_without_network(tmp_path, uri):
    assert invoke(tmp_path, action="uri", uri=uri)["error"] == "SMB:download_redirect_rejected"


def test_documented_github_cdn_redirect_is_allowed_without_network(tmp_path):
    result = invoke(
        tmp_path, action="uri", uri="https://release-assets.githubusercontent.com/asset"
    )
    assert result == {"ok": True}
