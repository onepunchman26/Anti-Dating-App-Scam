"""Isolated synthetic install/rollback/ownership tests; no native-account claims."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from anti_dating_scam.services.work_profile import WorkProfileService
from scripts import work_distribution_build as builder
from scripts import work_distribution_runtime as runtime


def package(tmp_path, version="0.8.0", label="payload", **overrides):
    folder = tmp_path / label
    folder.mkdir()
    components = {
        runtime.EXECUTABLE: b"synthetic runtime binary; never executed",
        "_internal/pinned.dll": b"synthetic dependency",
        ".agents/plugins/marketplace.json": runtime.encoded(
            {
                "name": "slowmatch-local",
                "plugins": [
                    {
                        "name": "slowmatch",
                        "source": {"source": "local", "path": "./plugins/slowmatch"},
                    }
                ],
            }
        ),
        "plugins/slowmatch/plugin.json": runtime.encoded(
            {"name": "slowmatch", "version": version, "author": {"name": "onepuchman"}}
        ),
    }
    for name, raw in components.items():
        file = folder / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    value = {
        "schema_version": 1,
        "product": runtime.PRODUCT,
        "repository": runtime.REPOSITORY,
        "version": version,
        "channel": "controlled-preview",
        "platform": "windows-x64",
        "entrypoint": runtime.EXECUTABLE,
        "data_schema": 1,
        "source_commit": "a" * 40,
        "source_digest": "b" * 64,
        "source_dirty": False,
        "dependencies": {"python": "3.12.14"},
        "license_status": runtime.LICENSE_STATUS,
        "service_origin": builder.SERVICE_ORIGIN,
        "files": {
            name: {"sha256": runtime.digest(raw), "size": len(raw)}
            for name, raw in components.items()
        },
        **overrides,
    }
    (folder / runtime.MANIFEST).write_bytes(runtime.encoded(value))
    return folder


@pytest.fixture
def installation(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.Distribution, "probe", staticmethod(lambda *_: None))
    monkeypatch.setattr(runtime, "owner_identity", lambda: "c" * 64)
    distribution = runtime.Distribution(tmp_path / "user-storage/portable")
    source = package(tmp_path)
    distribution.install(source)
    return distribution, source


def account(distribution, key="d" * 64, scope="test:synthetic"):
    result = distribution.create_slot(key, scope, confirmed=True)
    return result["slot"], distribution.slot(result["slot"], key, scope)


def test_repeat_install_retains_config_and_existing_account(installation):
    distribution, source = installation
    slot, location = account(distribution)
    marker = location / "synthetic-private-marker.txt"
    marker.write_text("PRIVATE_SYNTHETIC_DATA", encoding="utf-8")
    configuration = distribution.home / "unrelated-configuration.json"
    configuration.write_text('{"keep":true}', encoding="utf-8")
    pointer = distribution.active()
    result = distribution.install(source)
    assert result["status"] == "already_installed"
    assert distribution.active() == pointer
    assert account(distribution)[0] == slot
    assert len(list(distribution.accounts.iterdir())) == 1
    assert marker.read_text() == "PRIVATE_SYNTHETIC_DATA"
    assert configuration.read_text() == '{"keep":true}'


def test_retry_cleans_reserved_interrupted_staging_only(installation):
    distribution, source = installation
    interrupted = distribution.releases / (".staging-" + "1" * 32)
    interrupted.mkdir()
    (interrupted / "partial-component").write_bytes(b"partial")
    unrelated = distribution.releases / "user-notes"
    unrelated.mkdir()
    distribution.install(source)
    assert not interrupted.exists()
    assert unrelated.exists()
    assert distribution.checked_active()[0]["version"] == "0.8.0"


def test_interrupted_owner_creation_recovers_same_slot(installation, monkeypatch):
    distribution, _ = installation
    original = runtime.atomic

    def interrupted(path, value):
        if path.name == "slots.json":
            raise OSError("synthetic interrupted index write")
        original(path, value)

    monkeypatch.setattr(runtime, "atomic", interrupted)
    with pytest.raises(OSError):
        account(distribution)
    orphan = next(distribution.accounts.iterdir())
    monkeypatch.setattr(runtime, "atomic", original)
    slot, _ = account(distribution)
    assert slot == orphan.name
    assert len(list(distribution.accounts.iterdir())) == 1


def test_upgrade_failed_probe_preserves_old_runtime_and_data(installation, tmp_path, monkeypatch):
    distribution, _ = installation
    _, location = account(distribution)
    profile = WorkProfileService(location).read_profile().model_dump(mode="json")
    previous = distribution.active()
    upgrade = package(tmp_path, "0.9.0", "upgrade")

    def reject(*_):
        raise runtime.DistributionError("runtime_probe_failed")

    monkeypatch.setattr(distribution, "probe", reject)
    with pytest.raises(runtime.DistributionError, match="runtime_probe_failed"):
        distribution.install(upgrade)
    assert distribution.active() == previous
    assert WorkProfileService(location).read_profile().model_dump(mode="json") == profile
    assert not list(distribution.releases.glob(".staging-*"))


def test_upgrade_activation_failure_retry_reuses_verified_release(
    installation, tmp_path, monkeypatch
):
    distribution, _ = installation
    previous = distribution.active()
    upgrade = package(tmp_path, "0.9.0", "upgrade")
    original = runtime.atomic

    def interrupt(path, value):
        if path.name == "active.json":
            raise OSError("synthetic activation interruption")
        original(path, value)

    monkeypatch.setattr(runtime, "atomic", interrupt)
    with pytest.raises(OSError):
        distribution.install(upgrade)
    assert distribution.active() == previous
    monkeypatch.setattr(runtime, "atomic", original)
    distribution.install(upgrade)
    assert distribution.active()["version"] == "0.9.0"
    assert json.loads((distribution.home / "previous.json").read_text()) == previous
    assert len(list(distribution.releases.iterdir())) == 2


@pytest.mark.parametrize(
    "override,code",
    [
        ({"data_schema": 2}, "data_schema_upgrade_not_supported"),
        ({"version": "0.7.0"}, "downgrade_not_supported"),
        ({"repository": "someone-else/similar-name"}, "invalid_release_manifest"),
        ({"service_origin": "https://localhost"}, "invalid_release_manifest"),
    ],
)
def test_incompatible_upgrade_refused_before_activation(installation, tmp_path, override, code):
    distribution, _ = installation
    previous = distribution.active()
    other = package(tmp_path, label="other", **override)
    with pytest.raises(runtime.DistributionError, match=code):
        distribution.install(other)
    assert distribution.active() == previous


def test_repair_uses_new_verified_directory_preserves_owner(installation):
    distribution, source = installation
    slot, location = account(distribution)
    previous = distribution.active()
    corrupted = distribution.releases / previous["release"] / "_internal/pinned.dll"
    corrupted.write_bytes(b"corruption")
    with pytest.raises(runtime.DistributionError, match="repair_required"):
        distribution.install(source)
    distribution.install(source, repair=True)
    assert "-repair-" in distribution.active()["release"]
    assert distribution.slot(slot, "d" * 64, "test:synthetic") == location
    assert distribution.doctor()["checks"]["package_integrity"] == "passed"


def test_checksum_mismatch_refused(installation):
    distribution, source = installation
    with pytest.raises(runtime.DistributionError, match="release_checksum_mismatch"):
        distribution.install(source, expected_manifest="f" * 64)


def test_accounts_and_scope_explicit_no_fallback(installation, monkeypatch):
    distribution, _ = installation
    first, _ = account(distribution)
    other, _ = account(distribution, "e" * 64)
    production, _ = account(distribution, scope="production")
    assert len({first, other, production}) == 3
    for slot, key, scope in [(first, "e" * 64, "test:synthetic"), (first, "d" * 64, "production")]:
        with pytest.raises(runtime.DistributionError, match="owner_binding_mismatch"):
            distribution.slot(slot, key, scope)
    with pytest.raises(runtime.DistributionError, match="explicit_slot_required"):
        distribution.slot(None, "d" * 64, "test:synthetic")
    with pytest.raises(runtime.DistributionError, match="explicit_account_binding_required"):
        distribution.slot(first, None, "test:synthetic")
    monkeypatch.setattr(runtime, "owner_identity", lambda: "f" * 64)
    with pytest.raises(runtime.DistributionError, match="owner_binding_mismatch"):
        distribution.slot(first, "d" * 64, "test:synthetic")


def test_owner_confirmation_and_bad_scope_rejected(installation):
    distribution, _ = installation
    with pytest.raises(runtime.DistributionError, match="owner_confirmation_required"):
        distribution.create_slot("d" * 64, "production")
    for scope in ("test:", "test:../../private", "", None):
        with pytest.raises(runtime.DistributionError, match="explicit_account_binding_required"):
            distribution.create_slot("d" * 64, scope, True)


def test_diagnostics_and_probe_never_expose_or_load_private_profile(installation, monkeypatch):
    distribution, _ = installation
    slot, location = account(distribution)
    private = location / "private-synthetic.txt"
    private.write_text("DO_NOT_COPY_PRIVATE_MARKER", encoding="utf-8")
    before = {file.name: file.read_bytes() for file in location.iterdir() if file.is_file()}

    def forbidden(*_):
        raise AssertionError("Self-check must not load the profile")

    monkeypatch.setattr(WorkProfileService, "read_profile", forbidden)
    result = distribution.doctor(slot, "d" * 64, "test:synthetic")
    probe = distribution.local_probe(slot, "d" * 64, "test:synthetic")
    serialized = json.dumps([result, probe])
    assert len(serialized) < 1200
    for secret in (str(distribution.home), slot, "d" * 64, "DO_NOT_COPY_PRIVATE_MARKER"):
        assert secret not in serialized
    assert result["checks"]["native_chatgpt"] == "not_checked"
    assert result["checks"]["remote_authenticated_identity"] == "not_checked"
    assert probe["local_read_write"] == "passed_synthetic_only"
    assert not list((location.parent / "probe").iterdir())
    assert before == {file.name: file.read_bytes() for file in location.iterdir() if file.is_file()}


def test_daily_binding_does_not_rehash_all_runtime_components(installation, monkeypatch):
    distribution, _ = installation
    slot, _ = account(distribution)
    original = runtime.read_bytes
    reads = []

    def count(path, limit):
        reads.append(Path(path).name)
        return original(path, limit)

    monkeypatch.setattr(runtime, "read_bytes", count)
    distribution.slot(slot, "d" * 64, "test:synthetic")
    assert set(reads) <= {"active.json", "work-release.json", "owner.json"}


def test_uninstall_and_reinstall_preserve_accounts_and_other_config(installation):
    distribution, source = installation
    slot, location = account(distribution)
    (location / "retained.txt").write_text("PRIVATE_SYNTHETIC", encoding="utf-8")
    (distribution.home / "other.json").write_text("{}", encoding="utf-8")
    result = distribution.uninstall()
    assert result["status"] == "runtime_uninstalled"
    assert not (distribution.home / "active.json").exists()
    assert not list(distribution.releases.iterdir())
    assert (location / "retained.txt").read_text() == "PRIVATE_SYNTHETIC"
    assert (distribution.home / "other.json").exists()
    distribution.uninstall()
    distribution.install(source)
    assert account(distribution)[0] == slot


def fake_legacy_marketplace(tmp_path, repository=runtime.REPOSITORY):
    root = package(tmp_path, "0.7.0", "legacy-public-source")
    (root / ".git").mkdir()
    (root / ".git/config").write_text(
        f'[remote "origin"]\nurl = https://github.com/{repository}.git\n', encoding="utf-8"
    )
    return root


def native_registry(monkeypatch, old, fail_new_add=False):
    state = {"slowmatch-local": str(old), "unrelated-marketplace": "synthetic-unrelated-root"}
    calls = []
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "synthetic-codex")

    def invoke(command, **_):
        arguments = command[1:]
        calls.append(arguments)
        if arguments[:3] == ["plugin", "marketplace", "list"]:
            return SimpleNamespace(
                returncode=0,
                stdout=runtime.encoded(
                    {"marketplaces": [{"name": name, "root": root} for name, root in state.items()]}
                ),
            )
        if arguments[:3] == ["plugin", "marketplace", "remove"]:
            assert arguments[3] == "slowmatch-local"
            state.pop("slowmatch-local", None)
        if arguments[:3] == ["plugin", "marketplace", "add"]:
            if fail_new_add and runtime.logical_path(
                Path(arguments[3]).resolve()
            ) != runtime.logical_path(old.resolve()):
                return SimpleNamespace(returncode=1, stdout=b"{}")
            state["slowmatch-local"] = arguments[3]
        return SimpleNamespace(returncode=0, stdout=b"{}")

    monkeypatch.setattr(runtime.subprocess, "run", invoke)
    return state, calls


def test_owned_original_marketplace_migrates_idempotently_only_own_source(
    installation,
    tmp_path,
    monkeypatch,
):
    distribution, _ = installation
    old = fake_legacy_marketplace(tmp_path)
    state, calls = native_registry(monkeypatch, old)
    result = distribution.register_plugin()
    assert result["owned_marketplace_migrated"] is True
    installed = distribution.releases / distribution.active()["release"]
    assert runtime.logical_path(Path(state["slowmatch-local"]).resolve()) == runtime.logical_path(
        installed.resolve()
    )
    assert state["unrelated-marketplace"] == "synthetic-unrelated-root"
    calls.clear()
    assert distribution.register_plugin()["owned_marketplace_migrated"] is False
    assert len(calls) == 2


def test_native_marketplace_add_failure_restores_only_verified_previous_source(
    installation,
    tmp_path,
    monkeypatch,
):
    distribution, _ = installation
    old = fake_legacy_marketplace(tmp_path)
    state, _ = native_registry(monkeypatch, old, fail_new_add=True)
    with pytest.raises(runtime.DistributionError, match="previous_source_restored"):
        distribution.register_plugin()
    assert runtime.logical_path(Path(state["slowmatch-local"]).resolve()) == runtime.logical_path(
        old.resolve()
    )
    assert state["unrelated-marketplace"] == "synthetic-unrelated-root"


def test_foreign_same_named_marketplace_is_not_removed(installation, tmp_path, monkeypatch):
    distribution, _ = installation
    old = fake_legacy_marketplace(tmp_path, "other-owner/similar-product")
    state, calls = native_registry(monkeypatch, old)
    with pytest.raises(runtime.DistributionError, match="existing_marketplace_not_verified_owned"):
        distribution.register_plugin()
    assert state["slowmatch-local"] == str(old)
    assert len(calls) == 1


def test_public_copy_rechecks_exact_original_bytes_not_only_final_source_state(
    tmp_path, monkeypatch
):
    source, payload = tmp_path / "source", tmp_path / "payload"
    source.mkdir()
    payload.mkdir()
    (source / "guide.md").write_bytes(b"original reviewed guide")
    hashes = {"guide.md": runtime.digest((source / "guide.md").read_bytes())}
    monkeypatch.setattr(builder, "PUBLIC_FILES", {"guide.md": "guide.md"})
    (source / "guide.md").write_bytes(b"changed during copy")
    with pytest.raises(runtime.DistributionError, match="build_sources_changed"):
        builder.copy_public(source, payload, hashes)
    assert not (payload / "guide.md").exists()


def test_locked_uninstall_reports_pending_without_claiming_removed(installation, monkeypatch):
    distribution, _ = installation

    def locked_file(_):
        raise PermissionError("synthetic Windows running executable")

    monkeypatch.setattr(distribution, "_remove_managed", locked_file)
    result = distribution.uninstall()
    assert result["status"] == "runtime_deactivated_cleanup_pending"
    assert result["locked_release_directories"] == 1
    assert not (distribution.home / "active.json").exists()


def test_plugin_uses_supported_commands_no_configuration_rewrite(installation, monkeypatch):
    distribution, _ = installation
    calls = []
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "synthetic-codex")

    def invoke(command, **_):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=b'{"marketplaces":[]}')

    monkeypatch.setattr(runtime.subprocess, "run", invoke)
    result = distribution.register_plugin()
    assert len(calls) == 3
    assert calls[0][1:4] == ["plugin", "marketplace", "list"]
    assert calls[1][1:4] == ["plugin", "marketplace", "add"]
    assert calls[2][1:] == ["plugin", "add", "slowmatch@slowmatch-local", "--json"]
    assert result["native_chatgpt_loading"] == "not_checked"
    monkeypatch.setattr(runtime.shutil, "which", lambda _: None)
    with pytest.raises(runtime.DistributionError, match="supported_plugin_installer_unavailable"):
        distribution.register_plugin()


@pytest.mark.parametrize(
    "name",
    [
        "../private",
        "C:/private",
        "a\\b",
        "/root",
        "a//b",
        "a/./b",
        "NUL.txt",
        "private:stream",
        "trailing. ",
        "a\nlog",
    ],
)
def test_manifest_path_tricks_rejected(name):
    with pytest.raises(runtime.DistributionError, match="unsafe_manifest_path"):
        runtime.relative_name(name)


def test_manifest_unlisted_data_and_case_collisions_rejected(tmp_path):
    source = package(tmp_path)
    (source / "unlisted-private-data.json").write_text("{}", encoding="utf-8")
    with pytest.raises(runtime.DistributionError, match="unexpected_package_file"):
        runtime.manifest(source)
    (source / "unlisted-private-data.json").unlink()
    value = json.loads((source / runtime.MANIFEST).read_text())
    value["files"][runtime.EXECUTABLE.upper()] = value["files"][runtime.EXECUTABLE]
    (source / runtime.MANIFEST).write_bytes(runtime.encoded(value))
    with pytest.raises(runtime.DistributionError, match="duplicate_component_path"):
        runtime.manifest(source)


def test_hardlinked_component_rejected(tmp_path):
    source = package(tmp_path)
    os.link(source / runtime.EXECUTABLE, tmp_path / "linked")
    with pytest.raises(runtime.DistributionError, match="unsafe_path"):
        runtime.manifest(source)


def test_private_install_location_rejects_sync_repository_and_public(tmp_path):
    for suffix in ("OneDrive/product", "public/product", "plugins/product"):
        with pytest.raises(runtime.DistributionError, match="private_directory_required"):
            runtime.Distribution(tmp_path / suffix)
    repository = tmp_path / "source"
    (repository / ".git").mkdir(parents=True)
    with pytest.raises(runtime.DistributionError, match="private_directory_required"):
        runtime.Distribution(repository / "runtime")


def test_json_errors_and_missing_installation_are_redacted(tmp_path, capsys):
    private_path = tmp_path / "SYNTHETIC_PRIVATE_PATH"
    assert (
        runtime.main(
            ["install", "--home", str(tmp_path / "new/portable"), "--package", str(private_path)]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "SYNTHETIC_PRIVATE_PATH" not in output
    assert json.loads(output)["error"]["code"] == "operation_failed"


def test_core_dispatch_and_selective_schema_actual_python(installation, monkeypatch, capsys):
    distribution, _ = installation
    slot, _ = account(distribution)
    monkeypatch.setattr(runtime.sys, "stdin", io.TextIOWrapper(io.BytesIO(b"{}")))
    assert (
        runtime.main(
            [
                "run",
                "--home",
                str(distribution.home),
                "--slot",
                slot,
                "--account-key",
                "d" * 64,
                "--scope",
                "test:synthetic",
                "profile-index",
                "--input-json",
                "-",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert runtime.main(["schema", "--operation", "profile-read"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["result"]["operation"] == "profile-read"
    assert "schema" in result["result"]


def test_archive_bytes_deterministic_and_only_manifest_allowlist(tmp_path):
    source = package(tmp_path)
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    builder.deterministic_zip(source, first)
    builder.deterministic_zip(source, second)
    assert first.read_bytes() == second.read_bytes()
    import zipfile

    with zipfile.ZipFile(first) as archive:
        expected = set(runtime.manifest(source)[0]["files"]) | {runtime.MANIFEST}
        assert set(archive.namelist()) == expected
    (source / "secret.txt").write_text("DO_NOT_PACKAGE", encoding="utf-8")
    with pytest.raises(runtime.DistributionError, match="unexpected_package_file"):
        builder.deterministic_zip(source, tmp_path / "refused.zip")


def test_public_allowlist_includes_guides_and_excludes_private_or_developer_state():
    assert (
        builder.PUBLIC_FILES["scripts/controlled_test_fixtures.ps1"] == "tools/controlled-test.ps1"
    )
    for name in (
        "INSTALL_WITH_CHATGPT.md",
        "docs/DISTRIBUTION_HELP.md",
        "plugins/slowmatch/skills/setup/SKILL.md",
    ):
        assert name in builder.PUBLIC_FILES
    assert not any(
        name.startswith(("data/", "vault/", ".vscode/", "paper/", ".venv"))
        for name in builder.PUBLIC_FILES
    )
    assert "vosk" not in builder.DEPENDENCIES


@pytest.mark.skipif(os.name != "nt", reason="Win32 extended path behavior")
def test_long_private_paths_install_and_core_persistence_without_os_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.Distribution, "probe", staticmethod(lambda *_: None))
    monkeypatch.setattr(runtime, "owner_identity", lambda: "c" * 64)
    location = tmp_path / ("long-private-owner-directory-" + "x" * 120) / "portable"
    distribution = runtime.Distribution(location)
    source = package(tmp_path)
    distribution.install(source)
    slot, data = account(distribution)
    assert len(str(data)) > 260
    service = WorkProfileService(data)
    saved = service.update_profile(
        {
            "expected_revision": 0,
            "confirmed": True,
            "changes": [
                {
                    "action": "upsert",
                    "claim": {
                        "topic": "values",
                        "text": "Synthetic long-path check",
                        "source": {"source_type": "self_report", "reference": "synthetic"},
                        "confirmation": "confirmed",
                        "uncertainty": "Synthetic only",
                    },
                }
            ],
        }
    )
    assert saved.revision == 1
    assert (
        WorkProfileService(distribution.slot(slot, "d" * 64, "test:synthetic"))
        .read_profile()
        .revision
        == 1
    )
    assert distribution.uninstall()["status"] == "runtime_uninstalled"
    assert service.read_profile().revision == 1
    # pytest's generic Windows cleanup is not long-path aware. Only remove this
    # exact synthetic test subtree, using the guarded extended absolute path.
    cleanup = distribution.home.parent.resolve()
    assert runtime.logical_path(cleanup).is_relative_to(runtime.logical_path(tmp_path.resolve()))
    runtime.shutil.rmtree(cleanup)


def test_generated_editable_metadata_removed_and_developer_paths_refused(tmp_path):
    payload = tmp_path / "payload"
    metadata = payload / "_internal/anti_dating_scam-0.1.0.dist-info"
    metadata.mkdir(parents=True)
    (metadata / "direct_url.json").write_text('{"url":"file:///synthetic/developer"}')
    retained = payload / "_internal/pydantic-2.13.5.dist-info"
    retained.mkdir()
    (retained / "METADATA").write_text("Synthetic dependency notice")
    builder.clean_generated_metadata(payload)
    assert not metadata.exists()
    assert retained.exists()
    root = tmp_path / "source"
    (payload / "leak.json").write_text(json.dumps({"path": str(root)}))
    with pytest.raises(runtime.DistributionError, match="developer_path_in_payload"):
        builder.audit_developer_paths(payload, root)
    (payload / "leak.json").unlink()
    (payload / "direct_url.json").write_text("{}")
    with pytest.raises(runtime.DistributionError, match="developer_install_metadata_in_payload"):
        builder.audit_developer_paths(payload, root)


@pytest.mark.skipif(os.name != "nt", reason="Windows PyInstaller source/destination syntax")
def test_pyinstaller_add_data_parser_receives_normalized_extended_path(tmp_path):
    from PyInstaller.__main__ import generate_parser

    generated = runtime.native_path(tmp_path / "generated/build_info.json")
    argument = f"{runtime.logical_path(generated)};anti_dating_scam"
    parsed = generate_parser().parse_args(["--add-data", argument, "synthetic-entry.py"])
    assert len(parsed.datas) == 1
    assert Path(parsed.datas[0][0]) == runtime.logical_path(generated)
    assert parsed.datas[0][1] == "anti_dating_scam"


def test_repair_recovers_one_verified_identical_release_and_preserves_bad_pointer(installation):
    distribution, source = installation
    slot, data = account(distribution)
    (data / "synthetic-retained.txt").write_text("SYNTHETIC_PRIVATE")
    before = distribution.active()
    (distribution.home / "active.json").write_bytes(b'{"truncated":')
    with pytest.raises(runtime.DistributionError, match="active_pointer_invalid_use_repair"):
        distribution.install(source)
    result = distribution.install(source, repair=True)
    assert result["status"] == "repaired_active_pointer"
    assert distribution.active() == before
    assert account(distribution)[0] == slot
    assert (data / "synthetic-retained.txt").read_text() == "SYNTHETIC_PRIVATE"
    backups = list((distribution.home / "pointer-recovery").iterdir())
    assert len(backups) == 1
    assert (
        bytes.fromhex(json.loads(backups[0].read_text())["pointer_bytes_hex"]) == b'{"truncated":'
    )


def test_pointer_repair_refuses_ambiguous_upgrade_and_invalid_installed_payload(
    installation,
    tmp_path,
):
    distribution, source = installation
    upgrade = package(tmp_path, "0.9.0", "upgrade")
    (distribution.home / "active.json").write_bytes(b"invalid")
    with pytest.raises(runtime.DistributionError, match="recovery_requires_same_release"):
        distribution.install(upgrade, repair=True)
    distribution.install(source, repair=True)
    distribution.install(upgrade)
    (distribution.home / "active.json").write_bytes(b"invalid")
    with pytest.raises(runtime.DistributionError, match="active_pointer_recovery_ambiguous"):
        distribution.install(upgrade, repair=True)


def test_pointer_repair_requires_integrity_and_bounds_recovery_input(installation):
    distribution, source = installation
    installed = distribution.releases / distribution.active()["release"]
    (distribution.home / "active.json").write_bytes(b"x" * 4097)
    with pytest.raises(runtime.DistributionError, match="active_pointer_unrecoverable"):
        distribution.install(source, repair=True)
    (distribution.home / "active.json").write_bytes(b"invalid")
    (installed / "_internal/pinned.dll").write_bytes(b"broken")
    with pytest.raises(runtime.DistributionError, match="verified_installed_release_required"):
        distribution.install(source, repair=True)


def test_source_manifest_change_after_validation_never_reaches_executable_probe(
    tmp_path, monkeypatch
):
    distribution = runtime.Distribution(tmp_path / "isolated/portable")
    source = package(tmp_path)
    original_read = runtime.read_bytes
    reads = 0
    probed = []

    def mutate(path, limit):
        nonlocal reads
        if Path(path).resolve() == (source / runtime.MANIFEST).resolve():
            reads += 1
            if reads == 2:
                value = json.loads((source / runtime.MANIFEST).read_text())
                value["source_commit"] = "e" * 40
                (source / runtime.MANIFEST).write_bytes(runtime.encoded(value))
        return original_read(path, limit)

    monkeypatch.setattr(runtime, "read_bytes", mutate)
    monkeypatch.setattr(distribution, "probe", lambda *_: probed.append(True))
    with pytest.raises(runtime.DistributionError, match="package_changed_during_copy"):
        distribution.install(source)
    assert probed == []
    assert not (distribution.home / "active.json").exists()
    assert not list(distribution.releases.iterdir())
