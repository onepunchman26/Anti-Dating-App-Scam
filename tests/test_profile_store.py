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
