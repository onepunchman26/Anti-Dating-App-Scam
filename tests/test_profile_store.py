import pytest
from anti_dating_scam_desktop.profile_store import ProfileStore


def test_profile_store_detects_no_profile(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)

    assert store.detect_existing_profile() is False


def test_profile_store_detects_existing_markdown_profile(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)
    store.create_default_directories()
    store.markdown_path.write_text("# Profile", encoding="utf-8")

    assert store.detect_existing_profile() is True


def test_profile_store_saves_and_loads_markdown_profile(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)

    path = store.save_markdown_profile("# AI-SlowMatch Local Personal Profile\n")

    assert path.name == "profile.mpm.md"
    assert store.load_markdown_profile() == "# AI-SlowMatch Local Personal Profile\n"


def test_profile_store_saves_and_loads_json_profile(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)

    store.save_json_profile({"schema_version": "0.1", "owner_label": "local_user"})

    assert store.load_json_profile()["owner_label"] == "local_user"


def test_is_vault_recognizes_freshly_created_vault_without_profile(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path / "x", config_path=tmp_path / "config.json")
    vault = store.create_vault(tmp_path / "parent")

    # A fresh vault has the folder structure but no profile files yet; it must
    # still be recognized as a vault so the UI does not dead-end on "open".
    assert store.detect_existing_profile() is False
    assert store.is_vault(vault) is True


def test_is_vault_rejects_unrelated_folder(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path, config_path=tmp_path / "config.json")
    plain = tmp_path / "just_a_folder"
    plain.mkdir()

    assert store.is_vault(plain) is False
    assert store.resolve_vault(plain) is None


def test_resolve_vault_handles_parent_folder_selection(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path / "x", config_path=tmp_path / "config.json")
    parent = tmp_path / "parent"
    vault = store.create_vault(parent)

    # Picking the vault itself, or the parent it was created under, both resolve
    # to the actual vault folder.
    assert store.resolve_vault(vault) == vault
    assert store.resolve_vault(parent) == vault


@pytest.mark.parametrize("filename", ["profile.mpm.md", "profile.json"])
def test_flat_profile_is_recognized_without_automatic_migration(tmp_path, filename):
    vault = tmp_path / "parent" / "legacy"
    vault.mkdir(parents=True)
    original = vault / filename
    original.write_bytes(b"Synthetic flat source")
    store = ProfileStore(tmp_path / "current", config_path=tmp_path / "config.json")
    assert store.is_vault(vault)
    assert store.resolve_vault(vault.parent) == vault
    assert not (vault / "profile").exists()
    with pytest.raises(ValueError):
        store.use_existing_vault(vault)
    assert store.base_dir == tmp_path / "current"
    assert not store.config_path.exists()
    assert not (vault / "profile").exists()
    assert original.read_bytes() == b"Synthetic flat source"


def test_json_with_bom_loads_without_rewriting_source(tmp_path):
    store = ProfileStore(tmp_path, config_path=tmp_path / "config.json")
    store.profile_dir.mkdir()
    raw = b'\xef\xbb\xbf{"owner_label": "synthetic"}\r\n '
    store.json_path.write_bytes(raw)
    assert store.load_json_profile() == {"owner_label": "synthetic"}
    assert store.json_path.read_bytes() == raw


def test_failed_pointer_replace_preserves_previous_selection(tmp_path, monkeypatch):
    import anti_dating_scam_desktop.profile_store as module

    store = ProfileStore(tmp_path / "previous", config_path=tmp_path / "config.json")
    store.remember_vault()
    previous = store.config_path.read_bytes()
    candidate = tmp_path / "candidate"
    (candidate / "profile").mkdir(parents=True)

    def fail(*args):
        raise OSError("synthetic replacement failure")

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        store.use_existing_vault(candidate)
    assert store.base_dir == tmp_path / "previous"
    assert store.config_path.read_bytes() == previous
    assert not list(tmp_path.glob(".vault-pointer-*.tmp"))
