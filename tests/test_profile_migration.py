"""Synthetic exact-byte layout migration; never infer or repair profile content."""

import json
import os
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from anti_dating_scam.engine.personal_profile_builder import PersonalProfileBuilder
from anti_dating_scam.services import profile_migration as module
from anti_dating_scam.services.profile_migration import (
    ProfileMigrationError,
    ProfileMigrationService,
)


def _seed(tmp_path, *, destination="absent", members="both"):
    vault = tmp_path / "synthetic-vault"
    vault.mkdir()
    if members in ("both", "markdown"):
        (vault / "profile.mpm.md").write_bytes(
            b"\xef\xbb\xbf# Synthetic owner notes\r\n\r\n<script>literal_only()</script>\r\n",
        )
    if members in ("both", "json"):
        value = PersonalProfileBuilder().build(manual_notes="Synthetic adult values calm trust.")
        (vault / "profile.json").write_bytes(
            b"\xef\xbb\xbf" + (json.dumps(value, ensure_ascii=False, indent=3) + "\r\n  ").encode(),
        )
    if destination != "absent":
        (vault / "profile").mkdir()
    if destination == "occupied":
        (vault / "profile" / "do-not-touch.txt").write_text("existing", encoding="utf-8")
    return ProfileMigrationService(vault), vault


@pytest.mark.parametrize("destination", ["absent", "empty"])
@pytest.mark.parametrize("members", ["both", "markdown", "json"])
def test_exact_byte_copy_is_complete_reopens_and_preserves_flat_sources(
    tmp_path, destination, members,
):
    service, vault = _seed(tmp_path, destination=destination, members=members)
    original = {path.name: path.read_bytes() for path in vault.iterdir() if path.is_file()}
    before = sorted(path.name for path in vault.iterdir())
    preview = service.inspect()
    assert preview.eligible
    assert preview.destination_state == destination
    assert sorted(path.name for path in vault.iterdir()) == before  # Inspect never writes.
    assert all(item.text.startswith("\ufeff") for item in preview.files if item.present)
    result = service.migrate(preview, confirmed=True)
    assert result.directory_path == str(vault / "profile")
    assert result.source_digest == preview.source_digest
    assert set(result.files) == set(original)
    assert {path.name: path.read_bytes() for path in (vault / "profile").iterdir()} == original
    assert all((vault / name).read_bytes() == raw for name, raw in original.items())
    reopened = ProfileMigrationService(vault).inspect()
    assert reopened.source_digest == preview.source_digest
    assert reopened.destination_state == "occupied"
    assert not reopened.eligible
    assert not list(vault.glob(".pending-profile-migration-*"))
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true", [], {}])
def test_explicit_boolean_confirmation_required_without_writes(tmp_path, confirmed):
    service, vault = _seed(tmp_path)
    preview = service.inspect()
    before = {path.name: path.read_bytes() for path in vault.iterdir()}
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=confirmed)
    assert {path.name: path.read_bytes() for path in vault.iterdir()} == before


@pytest.mark.parametrize("raw", [
    b'{"broken":', b'{"same":1,"same":2}', b'{"value":NaN}', b'{"value":Infinity}',
    b'{"value":1e9999}', b'[]', b'null', b'"text"', b'{"text":"\\ud800"}',
    b'\xff\xfe', b'',
])
def test_invalid_json_is_reviewable_but_never_migrated(tmp_path, raw):
    service, vault = _seed(tmp_path)
    (vault / "profile.json").write_bytes(raw)
    preview = service.inspect()
    assert not preview.eligible
    member = next(item for item in preview.files if item.filename == "profile.json")
    assert member.sha256 == module._hash(raw)
    if raw != b"\xff\xfe":
        assert member.text == raw.decode("utf-8")
    else:
        assert member.text is None and member.encoding == "binary"
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)
    assert (vault / "profile.json").read_bytes() == raw
    assert not (vault / "profile").exists()


@pytest.mark.parametrize("field,value", [
    ("unknown_extension", {"kept": "no silent loss"}), ("created_at", "not a date"),
    ("updated_at", "2026-09-28"), ("schema_version", "0.2"),
    ("uncertainty_notes", []), ("owner_label", ""),
    ("created_at", "2026-09-28T00:00:00+00:60"),
    ("created_at", "2026-09-28T00:00:00-00:60"),
    ("updated_at", "2026-09-28T00:00:00+24:00"),
    ("updated_at", "2026-09-28T00:00:00-24:00"),
])
def test_unsupported_fields_and_invalid_contract_are_not_dropped_or_repaired(
    tmp_path, field, value,
):
    service, vault = _seed(tmp_path)
    original = json.loads((vault / "profile.json").read_text(encoding="utf-8-sig"))
    original[field] = value
    raw = json.dumps(original).encode()
    (vault / "profile.json").write_bytes(raw)
    preview = service.inspect()
    assert not preview.eligible
    assert any(issue.code == "invalid_profile_json" for issue in preview.issues)
    text = next(item.text for item in preview.files if item.filename == "profile.json")
    assert text == raw.decode()
    assert (vault / "profile.json").read_bytes() == raw


def test_invalid_markdown_and_missing_sources_remain_ineligible(tmp_path):
    service, vault = _seed(tmp_path, members="markdown")
    (vault / "profile.mpm.md").write_bytes(b"\xff\xfe")
    assert not service.inspect().eligible
    (vault / "profile.mpm.md").unlink()
    preview = service.inspect()
    assert not preview.eligible
    assert any(issue.code == "missing_sources" for issue in preview.issues)
    assert all(not item.present for item in preview.files)


@pytest.mark.parametrize("change", ["bytes", "removed", "added", "destination", "empty_directory"])
def test_preview_binds_source_presence_bytes_and_destination(tmp_path, change):
    service, vault = _seed(tmp_path, members="markdown")
    preview = service.inspect()
    if change == "bytes":
        (vault / "profile.mpm.md").write_text("new version", encoding="utf-8")
    elif change == "removed":
        (vault / "profile.mpm.md").unlink()
    elif change == "added":
        (vault / "profile.json").write_text("{}", encoding="utf-8")
    elif change == "destination":
        (vault / "profile").mkdir()
        (vault / "profile" / "keep.txt").write_text("new destination", encoding="utf-8")
    else:
        (vault / "profile").mkdir()
    before = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert not (vault / ".profile-migration").exists()


@pytest.mark.parametrize("field,value", [
    ("eligible", True), ("preview_digest", "0" * 64), ("issues", []),
    ("destination_state", "empty"), ("vault_digest", "0" * 64),
])
def test_tampered_preview_is_recomputed_before_copy(tmp_path, field, value):
    service, vault = _seed(tmp_path, destination="occupied" if field == "eligible" else "absent")
    preview = service.inspect().model_copy(update={field: value})
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)
    assert not (vault / ".profile-migration").exists()


def test_mutated_nested_preview_and_another_vault_are_rejected(tmp_path):
    service, vault = _seed(tmp_path)
    preview = service.inspect()
    preview.files.reverse()
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)
    other = tmp_path / "other-vault"
    other.mkdir()
    for name in module._NAMES:
        (other / name).write_bytes((vault / name).read_bytes())
    with pytest.raises(ProfileMigrationError):
        ProfileMigrationService(other).migrate(service.inspect(), confirmed=True)
    assert not (other / "profile").exists()


def test_occupied_destination_is_never_merged_or_overwritten(tmp_path):
    service, vault = _seed(tmp_path, destination="occupied")
    before = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    preview = service.inspect()
    assert not preview.eligible and preview.destination_state == "occupied"
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)
    assert {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize("destination", ["absent", "empty"])
@pytest.mark.parametrize("failure", ["write", "rename", "staged_bytes", "source_change"])
def test_failed_commit_preserves_sources_and_restores_empty_destination(
    tmp_path, monkeypatch, destination, failure,
):
    service, vault = _seed(tmp_path, destination=destination)
    preview = service.inspect()
    before = {path.name: path.read_bytes() for path in vault.iterdir() if path.is_file()}
    original_write = service._io._write_new

    def write(path, raw):
        if failure == "write" and path.name == "profile.json":
            raise OSError("PRIVATE_DATA_MUST_NOT_LEAK")
        original_write(path, raw)
        if failure == "staged_bytes" and path.name == "profile.json":
            path.write_bytes(b"changed staged bytes")
        if failure == "source_change" and path.name == "profile.json":
            (vault / "profile.mpm.md").write_bytes(b"changed by synthetic concurrent owner")

    def rename(_source, _destination):
        raise OSError("PRIVATE_DATA_MUST_NOT_LEAK")

    monkeypatch.setattr(service._io, "_write_new", write)
    if failure == "rename":
        monkeypatch.setattr(module.os, "rename", rename)
    with pytest.raises(ProfileMigrationError) as error:
        service.migrate(preview, confirmed=True)
    assert "PRIVATE_DATA_MUST_NOT_LEAK" not in str(error.value)
    assert "无法" in str(error.value)
    for name, raw in before.items():
        if failure != "source_change" or name != "profile.mpm.md":
            assert (vault / name).read_bytes() == raw
    assert (vault / "profile").exists() == (destination == "empty")
    if destination == "empty":
        assert list((vault / "profile").iterdir()) == []
    assert not list(vault.glob(".pending-profile-migration-*"))


def test_complete_directory_is_published_once_after_all_member_checks(tmp_path, monkeypatch):
    service, vault = _seed(tmp_path)
    original_rename = module.os.rename
    published = []

    def rename(source, destination):
        assert Path(destination) == vault / "profile"
        assert not Path(destination).exists()
        assert {path.name for path in Path(source).iterdir()} == set(module._NAMES)
        assert all((Path(source) / name).read_bytes() == (vault / name).read_bytes()
                   for name in module._NAMES)
        published.append(True)
        return original_rename(source, destination)

    monkeypatch.setattr(module.os, "rename", rename)
    service.migrate(service.inspect(), confirmed=True)
    assert published == [True]


@pytest.mark.parametrize("destination", ["absent", "empty"])
@pytest.mark.parametrize("change", ["identity", "bytes", "members"])
def test_staged_content_is_rechecked_immediately_before_publication(
    tmp_path, monkeypatch, destination, change,
):
    service, vault = _seed(tmp_path, destination=destination)
    preview = service.inspect()
    originals = {name: (vault / name).read_bytes() for name in module._NAMES}
    original_inspect = service._inspect
    injected = []

    def inspect():
        result = original_inspect()
        stages = list(vault.glob(".pending-profile-migration-*"))
        if stages and not injected:
            stage = stages[0]
            injected.append(stage)
            if change == "identity":
                # A different directory containing identical bytes must still fail.
                stage.rename(vault / ".synthetic-retained-stage")
                stage.mkdir()
                for name, raw in originals.items():
                    (stage / name).write_bytes(raw)
            elif change == "bytes":
                (stage / "profile.json").write_bytes(b"changed after validation")
            else:
                (stage / "unexpected").write_bytes(b"do not remove")
        return result

    monkeypatch.setattr(service, "_inspect", inspect)
    with pytest.raises(ProfileMigrationError):
        service.migrate(preview, confirmed=True)
    assert injected
    assert (vault / "profile").exists() == (destination == "empty")
    if destination == "empty":
        assert not list((vault / "profile").iterdir())
    assert all((vault / name).read_bytes() == raw for name, raw in originals.items())
    if change == "identity":
        assert all((injected[0] / name).read_bytes() == raw for name, raw in originals.items())
    elif change == "members":
        assert (injected[0] / "unexpected").read_bytes() == b"do not remove"


def test_competing_threads_publish_only_one_complete_profile(tmp_path):
    service, vault = _seed(tmp_path)
    preview = service.inspect()

    def save(_index):
        try:
            return ProfileMigrationService(vault).migrate(preview, confirmed=True)
        except ProfileMigrationError:
            return None

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(save, range(4)))
    assert len([item for item in results if item is not None]) == 1
    assert all((vault / "profile" / name).read_bytes() == (vault / name).read_bytes()
               for name in module._NAMES)


@pytest.mark.parametrize("member", ["profile.mpm.md", "profile.json"])
def test_hardlinked_source_rejected_before_read(tmp_path, member):
    service, vault = _seed(tmp_path)
    original = vault / member
    os.link(original, tmp_path / "alias")
    with pytest.raises(ProfileMigrationError):
        service.inspect()
    assert not (vault / ".profile-migration").exists()


@pytest.mark.parametrize("unsafe", ["source_directory", "destination_file", "lock_file"])
def test_nonregular_paths_fail_without_replacement(tmp_path, unsafe):
    service, vault = _seed(tmp_path)
    if unsafe == "source_directory":
        (vault / "profile.json").unlink()
        (vault / "profile.json").mkdir()
    elif unsafe == "destination_file":
        (vault / "profile").write_text("do not replace", encoding="utf-8")
    else:
        (vault / ".profile-migration").write_text("not a lock directory", encoding="utf-8")
    with pytest.raises(ProfileMigrationError):
        preview = service.inspect()
        service.migrate(preview, confirmed=True)
    assert (vault / "profile.mpm.md").is_file()


def test_bounded_sources_and_unrelated_files_are_never_read(tmp_path, monkeypatch):
    service, vault = _seed(tmp_path)
    (vault / "imports").mkdir()
    (vault / "imports" / "not-selected.txt").write_text("never read", encoding="utf-8")
    (vault / "profile.json").write_bytes(b"x" * (module.MAX_FILE_BYTES + 1))
    with pytest.raises(ProfileMigrationError):
        service.inspect()
    (vault / "profile.json").unlink()
    calls = []
    original = service._io._read

    def read(path, limit):
        calls.append(path)
        return original(path, limit)

    monkeypatch.setattr(service._io, "_read", read)
    assert service.inspect().eligible
    assert set(calls) == {vault / "profile.mpm.md"}


@pytest.mark.parametrize("target", ["vault", "source", "destination", "lock"])
def test_reparse_points_fail_closed_at_all_migration_boundaries(tmp_path, monkeypatch, target):
    service, vault = _seed(tmp_path, destination="empty")
    lock = vault / ".profile-migration"
    lock.mkdir()
    unsafe = {
        "vault": vault, "source": vault / "profile.json",
        "destination": vault / "profile", "lock": lock,
    }[target]
    original_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        info = original_lstat(path, *args, **kwargs)
        if path != unsafe:
            return info
        values = {name: getattr(info, name) for name in dir(info) if name.startswith("st_")}
        values["st_file_attributes"] = (
            values.get("st_file_attributes", 0)
            | getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
        )
        return SimpleNamespace(**values)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ProfileMigrationError):
        preview = service.inspect()
        service.migrate(preview, confirmed=True)
    assert list((vault / "profile").iterdir()) == []


def test_unsafe_or_extra_pending_members_are_left_untouched_on_failure(tmp_path, monkeypatch):
    service, vault = _seed(tmp_path)
    original = service._io._write_new

    def write(path, raw):
        original(path, raw)
        if path.name == "profile.json":
            (path.parent / "foreign-entry").write_bytes(b"do not remove an unexpected member")

    monkeypatch.setattr(service._io, "_write_new", write)
    with pytest.raises(ProfileMigrationError):
        service.migrate(service.inspect(), confirmed=True)
    pending = list(vault.glob(".pending-profile-migration-*"))
    assert len(pending) == 1
    assert (pending[0] / "foreign-entry").read_bytes() == b"do not remove an unexpected member"
    assert not (vault / "profile").exists()


def test_destination_appearing_during_staging_is_never_overwritten(tmp_path, monkeypatch):
    service, vault = _seed(tmp_path)
    original = service._io._write_new

    def write(path, raw):
        original(path, raw)
        if path.name == "profile.json":
            (vault / "profile").mkdir()
            (vault / "profile" / "new.txt").write_bytes(b"concurrent owner entry")

    monkeypatch.setattr(service._io, "_write_new", write)
    with pytest.raises(ProfileMigrationError):
        service.migrate(service.inspect(), confirmed=True)
    assert {path.name for path in (vault / "profile").iterdir()} == {"new.txt"}
    assert (vault / "profile" / "new.txt").read_bytes() == b"concurrent owner entry"


_PROCESS_WRITER = """
import json, sys, time
from pathlib import Path
from anti_dating_scam.services.profile_migration import (
    ProfileMigrationError, ProfileMigrationPreview, ProfileMigrationService,
)
vault, control = Path(sys.argv[1]), Path(sys.argv[2])
preview = ProfileMigrationPreview.model_validate_json((control / 'preview.json').read_bytes())
service = ProfileMigrationService(vault)
(control / ('ready-' + sys.argv[3])).write_text('ready', encoding='ascii')
deadline = time.monotonic() + 20
while not (control / 'start').exists():
    if time.monotonic() > deadline:
        raise RuntimeError('Synthetic process barrier timed out.')
    time.sleep(0.01)
try:
    saved = service.migrate(preview, confirmed=True)
    print(json.dumps({'saved': True, 'source_digest': saved.source_digest}), flush=True)
except ProfileMigrationError:
    print(json.dumps({'saved': False}), flush=True)
"""


def test_four_processes_publish_one_complete_copy_and_fresh_reader_reopens(tmp_path):
    service, vault = _seed(tmp_path, destination="empty")
    preview = service.inspect()
    control = tmp_path / "synthetic-control"
    control.mkdir()
    (control / "preview.json").write_text(preview.model_dump_json(), encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    options = {
        "cwd": tmp_path, "env": environment, "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8",
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }
    children, outputs = [], []
    try:
        for index in range(4):
            children.append(subprocess.Popen([
                sys.executable, "-c", _PROCESS_WRITER, str(vault), str(control), str(index),
            ], **options))
        deadline = time.monotonic() + 20
        while len(list(control.glob("ready-*"))) < 4:
            assert all(child.poll() is None for child in children)
            assert time.monotonic() < deadline
            time.sleep(0.01)
        (control / "start").write_text("start", encoding="ascii")
        outputs = [child.communicate(timeout=25) for child in children]
        assert all(child.returncode == 0 for child in children), outputs
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    rows = [json.loads(stdout) for stdout, _stderr in outputs]
    assert sum(row["saved"] for row in rows) == 1
    saved = next(row for row in rows if row["saved"])
    assert saved["source_digest"] == preview.source_digest
    reader = """
import json, sys
from pathlib import Path
from anti_dating_scam.services.profile_migration import ProfileMigrationService
vault = Path(sys.argv[1])
preview = ProfileMigrationService(vault).inspect()
assert preview.destination_state == 'occupied' and not preview.eligible
for member in preview.files:
    if member.present:
        original = (vault / member.filename).read_bytes()
        assert (vault / 'profile' / member.filename).read_bytes() == original
assert not list(vault.glob('.pending-profile-migration-*'))
print(json.dumps({'source_digest': preview.source_digest}))
"""
    fresh = subprocess.run(
        [sys.executable, "-c", reader, str(vault)], timeout=20, check=True, **options,
    )
    assert json.loads(fresh.stdout)["source_digest"] == preview.source_digest
