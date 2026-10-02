"""Real local file promotion/recovery and synthetic source backup boundaries."""

import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from scripts import release_support as release


def candidate(tmp_path, data=b"synthetic executable", **overrides):
    path = tmp_path / (uuid4().hex + ".candidate")
    path.write_bytes(data)
    values = dict(
        build_id=uuid4().hex,
        version="0.2.0",
        created_at="2026-10-02T00:00:00+00:00",
        git_commit="a" * 40,
        dirty=True,
        source_digest="b" * 64,
        sha256=release.digest(path),
        checks={name: "passed" for name in ("compile", "pytest", "lint", "package", "smoke")},
    )
    values.update(overrides)
    return path, release.ReleaseManifest(**values)


def test_two_promotions_keep_one_entry_and_rollback_exactly(tmp_path):
    root = tmp_path / "product"
    root.mkdir()
    first, a = candidate(tmp_path, b"first")
    second, b = candidate(tmp_path, b"second", version="0.2.1")
    release.promote(root, first, a)
    release.promote(root, second, b)
    assert list(root.glob("*.exe")) == [root / release.EXE]
    assert (root / release.EXE).read_bytes() == b"second"
    release.rollback(root, a.build_id)
    assert (root / release.EXE).read_bytes() == b"first"
    assert release.read_release(root / "releases/current.json") == a
    assert release.digest(root / "releases" / b.build_id / release.EXE) == b.sha256


@pytest.mark.parametrize("failure", ["hash", "gate"])
def test_invalid_candidate_cannot_replace_current(tmp_path, failure):
    root = tmp_path / "product"
    root.mkdir()
    path, original = candidate(tmp_path)
    release.promote(root, path, original)
    other, change = candidate(tmp_path, b"changed")
    if failure == "hash":
        other.write_bytes(b"tampered")
    else:
        change = change.model_copy(update={"checks": {"compile": "passed"}})
    with pytest.raises(release.ReleaseError):
        release.promote(root, other, change)
    assert release.digest(root / release.EXE) == original.sha256
    assert release.read_release(root / "releases/current.json") == original


def test_locked_executable_preserves_current_and_staged_candidate(tmp_path, monkeypatch):
    root = tmp_path / "product"
    root.mkdir()
    a, original = candidate(tmp_path)
    b, change = candidate(tmp_path, b"new")
    release.promote(root, a, original)
    replace = os.replace

    def locked(source, target):
        if Path(target) == root / release.EXE:
            raise PermissionError("synthetic running file lock")
        return replace(source, target)

    monkeypatch.setattr(os, "replace", locked)
    with pytest.raises(release.ReleaseError, match="Close AI-SlowMatch"):
        release.promote(root, b, change)
    assert release.digest(root / release.EXE) == original.sha256
    assert release.read_release(root / "releases/current.json") == original
    assert b.exists()
    monkeypatch.setattr(os, "replace", replace)
    release.promote(root, b, change)
    assert release.digest(root / release.EXE) == change.sha256


def test_recover_after_exe_switch_before_receipt_write(tmp_path, monkeypatch):
    root = tmp_path / "product"
    root.mkdir()
    a, original = candidate(tmp_path)
    b, change = candidate(tmp_path, b"new")
    release.promote(root, a, original)
    write = release._json

    def interrupted(path, value):
        if path == root / "releases/current.json":
            raise OSError("synthetic interruption")
        write(path, value)

    monkeypatch.setattr(release, "_json", interrupted)
    with pytest.raises(OSError):
        release.promote(root, b, change)
    assert release.digest(root / release.EXE) == change.sha256
    monkeypatch.setattr(release, "_json", write)
    with release.promotion_lock(root / "releases"):
        release._recover(root)
    assert release.read_release(root / "releases/current.json") == change
    release.rollback(root, original.build_id)
    assert release.digest(root / release.EXE) == original.sha256


def test_second_promoter_is_rejected(tmp_path):
    with release.promotion_lock(tmp_path):
        with pytest.raises(release.ReleaseError, match="Another release"):
            with release.promotion_lock(tmp_path):
                pytest.fail("Two owners acquired the promotion lock")


def test_retention_keeps_current_pinned_and_unmanaged_archives(tmp_path):
    root = tmp_path / "product"
    root.mkdir()
    manifests = []
    for day in range(1, 6):
        path, manifest = candidate(
            tmp_path, str(day).encode(), created_at=f"2026-10-0{day}T00:00:00Z"
        )
        release.promote(root, path, manifest)
        manifests.append(manifest)
    pinned = root / "releases" / manifests[0].build_id
    (pinned / ".keep").touch()
    unmanaged = root / "releases" / ("f" * 32)
    unmanaged.mkdir()
    (unmanaged / "do-not-delete.txt").write_text("synthetic unmanaged file")
    release.apply_retention(root, tmp_path / "absent-backups")
    assert pinned.exists() and unmanaged.exists()
    assert not (root / "releases" / manifests[1].build_id).exists()
    assert release.digest(root / release.EXE) == manifests[-1].sha256
    with pytest.raises(release.ReleaseError):
        release._remove_managed_tree(root, tmp_path)


def seed_source(root):
    (root / "src").mkdir(parents=True)
    (root / "src/tracked.py").write_text("original = 1\n")
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    for args in (
        ["init", "-q"],
        ["add", "src"],
        [
            "-c",
            "user.name=onepuchman",
            "-c",
            "user.email=synthetic@example.invalid",
            "commit",
            "-qm",
            "Synthetic initial state",
        ],
    ):
        subprocess.run(["git", "-C", str(root), *args], env=env, check=True, capture_output=True)
    (root / "src/tracked.py").write_text("changed = 2\n")
    (root / "src/untracked.py").write_text("new_file = 3\n")
    (root / ".env").write_text("SYNTHETIC_SECRET=do-not-copy")
    (root / "private.slowmatch").write_bytes(b"synthetic private package")
    (root / "vault").mkdir()
    (root / "vault/transcript.json").write_text('{"synthetic":true}')
    (root / "pip/cache").mkdir(parents=True)
    (root / "pip/cache/response.txt").write_text("synthetic cached response")
    for private in (
        ".peer-session",
        ".dating-introduction",
        ".relationship-memory",
        "matching-node",
    ):
        folder = root / "src" / private
        folder.mkdir()
        (folder / "state.json").write_text('{"private":"synthetic-not-for-backup"}')


def test_backup_restore_preserves_dirty_and_untracked_source_excludes_data(tmp_path):
    root = tmp_path / "repo"
    seed_source(root)
    snapshot = release.backup_source(root, tmp_path / "backups")
    manifest = json.loads((snapshot / "snapshot.json").read_text())
    assert manifest["restore_verified"]
    assert set(manifest["files"]) == {"src/tracked.py", "src/untracked.py"}
    restored = tmp_path / "restored"
    release.restore_source(snapshot, restored)
    assert (restored / "src/tracked.py").read_text() == "changed = 2\n"
    assert (restored / "src/untracked.py").read_text() == "new_file = 3\n"
    assert (restored / "restored-history.git/HEAD").is_file()
    with pytest.raises(release.ReleaseError):
        release.restore_source(snapshot, root)
    (snapshot / "source.zip").write_bytes(b"tampered")
    with pytest.raises(release.ReleaseError, match="hash mismatch"):
        release.restore_source(snapshot, tmp_path / "bad-restore")


def test_backup_cannot_be_inside_checkout(tmp_path):
    root = tmp_path / "repo"
    seed_source(root)
    with pytest.raises(release.ReleaseError):
        release.backup_source(root, root / "backups")
