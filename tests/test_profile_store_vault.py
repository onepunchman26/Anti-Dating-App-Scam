from anti_dating_scam_desktop.profile_store import DEFAULT_VAULT_NAME, ProfileStore


def test_create_vault_builds_structure(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path / "seed", config_path=tmp_path / "config.json")

    vault = store.create_vault(tmp_path / "parent")

    assert vault == tmp_path / "parent" / DEFAULT_VAULT_NAME
    assert (vault / "profile").is_dir()
    assert (vault / "imports").is_dir()
    assert (vault / "reports").is_dir()
    assert store.markdown_path == vault / "profile" / "profile.mpm.md"
    assert store.json_path == vault / "profile" / "profile.json"
    assert (vault / "AGENTS.md").exists()
    assert (vault / "CLAUDE.md").exists()


def test_agent_instructions_contain_safety_boundaries(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path, config_path=tmp_path / "config.json")

    store.write_agent_instructions()

    text = store.agents_md_path.read_text(encoding="utf-8").lower()
    assert "social score" in text
    assert "privacy-first" in text
    # The two agent files carry identical guidance.
    assert store.claude_md_path.read_text(encoding="utf-8") == store.agents_md_path.read_text(
        encoding="utf-8"
    )


def test_remember_and_reload_vault(tmp_path) -> None:
    config = tmp_path / "config.json"
    store = ProfileStore(base_dir=tmp_path / "seed", config_path=config)

    vault = store.create_vault(tmp_path / "p")

    # A fresh store sharing the same config pointer reopens the remembered vault.
    reopened = ProfileStore(config_path=config)
    assert reopened.base_dir == vault


def test_use_existing_vault_points_and_remembers(tmp_path) -> None:
    config = tmp_path / "config.json"
    existing = tmp_path / "myvault"
    (existing / "profile").mkdir(parents=True)
    store = ProfileStore(base_dir=tmp_path / "seed", config_path=config)

    store.use_existing_vault(existing)

    assert store.base_dir == existing
    assert ProfileStore(config_path=config).base_dir == existing


def test_saved_profile_lands_inside_vault_profile_dir(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path / "seed", config_path=tmp_path / "config.json")
    vault = store.create_vault(tmp_path / "parent")

    md_path = store.save_markdown_profile("# AI-SlowMatch Local Personal Profile\n")
    json_path = store.save_json_profile({"schema_version": "0.1", "owner_label": "local_user"})

    assert md_path == vault / "profile" / "profile.mpm.md"
    assert json_path == vault / "profile" / "profile.json"
    assert store.detect_existing_profile() is True
