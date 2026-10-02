from anti_dating_scam_desktop import agent_handoff
from anti_dating_scam_desktop.profile_store import ProfileStore


def _vault(tmp_path) -> ProfileStore:
    store = ProfileStore(base_dir=tmp_path / "x", config_path=tmp_path / "config.json")
    store.create_vault(tmp_path / "parent")
    return store


def test_list_vault_data_files_covers_profile_and_imports_only(tmp_path) -> None:
    store = _vault(tmp_path)
    store.save_markdown_profile("# Profile\n")
    store.save_import_text("hello", "notes.md")
    # A report should NOT be treated as input data.
    (store.get_reports_dir() / "old_report.md").write_text("stale", encoding="utf-8")

    rel = {path.as_posix() for path in agent_handoff.list_vault_data_files(store.base_dir)}

    assert "profile/profile.mpm.md" in rel
    assert "imports/notes.md" in rel
    assert all(not path.startswith("reports/") for path in rel)


def test_build_analysis_request_states_rules_and_output_standard(tmp_path) -> None:
    store = _vault(tmp_path)
    store.save_import_text("Send me money for a flight, my love.", "chat.md")

    body = agent_handoff.build_analysis_request(store.base_dir)

    # Output standard: names the exact report files the agent must write.
    assert agent_handoff.REPORT_MARKDOWN_NAME in body
    assert agent_handoff.REPORT_JSON_NAME in body
    # Data manifest references the user's file.
    assert "imports/chat.md" in body
    # Rules / safety boundaries are present (no scoring, no money advice).
    assert "score" in body.lower()
    assert "money" in body.lower()
    # Schema field names so the JSON companion stays loadable.
    for field in ("risk_level", "risk_signals", "recommended_next_steps"):
        assert field in body


def test_build_agent_prompt_points_at_vault(tmp_path) -> None:
    store = _vault(tmp_path)

    prompt = agent_handoff.build_agent_prompt(store.base_dir)

    assert str(store.base_dir) in prompt
    assert agent_handoff.ANALYSIS_REQUEST_NAME in prompt


def test_write_analysis_request_and_find_latest_report(tmp_path) -> None:
    store = _vault(tmp_path)

    request_path = store.write_analysis_request(
        agent_handoff.build_analysis_request(store.base_dir)
    )
    assert request_path == store.analysis_request_path
    assert request_path.exists()

    # No report until the agent writes one.
    assert store.find_latest_report() is None

    (store.get_reports_dir() / "notes.txt").write_text("misc", encoding="utf-8")
    (store.get_reports_dir() / "risk_report.md").write_text("# Report\n", encoding="utf-8")

    # The standard risk_report.md is preferred over other files in reports/.
    assert store.find_latest_report().name == "risk_report.md"


def test_self_portrait_request_is_about_the_user_and_names_frameworks(tmp_path) -> None:
    store = _vault(tmp_path)
    store.save_import_text("I always need space after an argument.", "chat.md")

    body = agent_handoff.build_self_portrait_request(store.base_dir)

    # Framed as understanding the user's own personality, not a scam read.
    assert "self-portrait" in body.lower()
    assert "user's own" in body.lower()
    # Output standard: the two reports + json companion.
    assert agent_handoff.SELF_PORTRAIT_SIMPLE_NAME in body
    assert agent_handoff.SELF_PORTRAIT_DETAILED_NAME in body
    assert agent_handoff.SELF_PORTRAIT_JSON_NAME in body
    # Theory frameworks named across disciplines.
    for framework in ("Big Five", "attachment", "Schwartz", "Goffman"):
        assert framework in body
    # Data manifest references the user's own file.
    assert "imports/chat.md" in body


def test_self_portrait_prompt_points_at_request_and_vault(tmp_path) -> None:
    store = _vault(tmp_path)

    prompt = agent_handoff.build_self_portrait_prompt(store.base_dir)

    assert str(store.base_dir) in prompt
    assert agent_handoff.SELF_PORTRAIT_REQUEST_NAME in prompt
    assert agent_handoff.SELF_PORTRAIT_SIMPLE_NAME in prompt


def test_criteria_interview_request_is_interactive_and_non_sycophantic(tmp_path) -> None:
    store = _vault(tmp_path)
    store.save_import_text("I want someone ambitious and always available.", "notes.md")

    body = agent_handoff.build_criteria_interview_request(store.base_dir)

    # Interactive: interview happens in chat before any output is written.
    assert "INTERACTIVE" in body
    assert "one question at a time" in body.lower()
    # The anti-sycophancy stance is written into the contract itself.
    assert "Do not conform to the user's views" in body
    assert "cheerleader" in body
    assert "No flattery" in body
    # Revealed vs stated preferences is the core synthesis.
    assert "stated" in body.lower() and "revealed" in body.lower()
    # Ideal profiles must be realistic, not cinematic: costs + no dominant option.
    assert "not cinematic" in body.lower()
    assert "Pareto" in body
    # Data-saving standard: transcript into imports/, outputs into reports/.
    assert agent_handoff.CRITERIA_TRANSCRIPT_RELPATH in body
    assert agent_handoff.MATE_CRITERIA_MD_NAME in body
    assert agent_handoff.MATE_CRITERIA_JSON_NAME in body
    assert agent_handoff.IDEAL_PROFILES_JSON_NAME in body
    # Safety boundaries: incisive is not cruel; no gendered blame; no person-scores.
    assert "No gendered blame" in body
    assert "Never score" in body
    # Manifest carries the user's file.
    assert "imports/notes.md" in body


def test_criteria_interview_prompt_demands_challenge_not_agreement(tmp_path) -> None:
    store = _vault(tmp_path)

    prompt = agent_handoff.build_criteria_interview_prompt(store.base_dir)

    assert str(store.base_dir) in prompt
    assert agent_handoff.CRITERIA_INTERVIEW_REQUEST_NAME in prompt
    assert "do NOT just agree with me" in prompt


def test_profile_store_mate_criteria_roundtrip(tmp_path) -> None:
    store = _vault(tmp_path)

    request_path = store.write_criteria_interview_request(
        agent_handoff.build_criteria_interview_request(store.base_dir)
    )
    assert request_path == store.criteria_interview_request_path
    assert request_path.exists()

    assert store.has_mate_criteria() is False
    assert store.load_mate_criteria() is None

    store.get_reports_dir()
    store.mate_criteria_path.write_text("# My Mate-Selection Criteria\n", encoding="utf-8")

    assert store.has_mate_criteria() is True
    assert "Criteria" in store.load_mate_criteria()


def test_profile_store_self_portrait_roundtrip(tmp_path) -> None:
    store = _vault(tmp_path)

    request_path = store.write_self_portrait_request(
        agent_handoff.build_self_portrait_request(store.base_dir)
    )
    assert request_path == store.self_portrait_request_path
    assert request_path.exists()

    assert store.has_self_portrait() is False
    assert store.load_self_portrait() is None

    store.get_reports_dir()  # ensure reports/ exists
    store.self_portrait_path.write_text("# Your Self-Portrait\n", encoding="utf-8")

    assert store.has_self_portrait() is True
    assert "Self-Portrait" in store.load_self_portrait()
