import json

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend, ai_settings
from anti_dating_scam_desktop.ai_backend import (
    AnthropicChatBackend,
    BackendError,
    ClaudeAgentBackend,
    OllamaChatBackend,
    parse_delimited,
    run_criteria_synthesis,
    run_self_portrait,
)
from anti_dating_scam_desktop.profile_store import ProfileStore

from anti_dating_scam.ai.privacy import build_reviewed_request


def _store(tmp_path) -> ProfileStore:
    store = ProfileStore(base_dir=tmp_path / "x", config_path=tmp_path / "config.json")
    store.create_vault(tmp_path / "parent")
    store.save_import_text("I value honesty and quiet evenings.", "notes.md")
    return store


# ----------------------------------------------------------------- delimiters
def test_parse_delimited_extracts_sections() -> None:
    text = "===A===\nalpha\n===B===\nbeta\n===END===\n"
    result = parse_delimited(text, ["A", "B"])
    assert result == {"A": "alpha", "B": "beta"}


def test_parse_delimited_reports_missing_sections() -> None:
    with pytest.raises(BackendError, match="missing required sections: B"):
        parse_delimited("===A===\nalpha\n===END===", ["A", "B"])


# --------------------------------------------------------------------- ollama
def test_ollama_chat_sends_system_and_returns_content() -> None:
    captured: dict = {}

    def transport(url, payload, headers, timeout):
        captured["url"] = url
        captured["payload"] = payload
        return {"message": {"content": "hello from local model"}}

    backend = OllamaChatBackend(model="testmodel", transport=transport)
    reply = backend.chat([{"role": "user", "content": "hi"}], system="be sharp")

    assert reply == "hello from local model"
    assert captured["url"].endswith("/api/chat")
    assert captured["payload"]["model"] == "testmodel"
    assert captured["payload"]["messages"][0] == {"role": "system", "content": "be sharp"}


def test_ollama_check_reports_missing_models() -> None:
    backend = OllamaChatBackend(transport=lambda *args: {"models": []})
    available, detail = backend.check()
    assert available is False
    assert "no models" in detail


# ------------------------------------------------------------------ anthropic
def test_anthropic_chat_sets_key_header_and_parses_blocks() -> None:
    captured: dict = {}

    def transport(url, payload, headers, timeout):
        captured["headers"] = headers
        captured["payload"] = payload
        return {"content": [{"type": "text", "text": "cloud reply"}]}

    backend = AnthropicChatBackend(api_key="k-test", model="m", transport=transport)
    reply = backend.chat(
        build_reviewed_request(
            [{"role": "user", "content": "hi"}], system="sys", recipient=backend.recipient
        )
    )

    assert reply == "cloud reply"
    assert captured["headers"]["x-api-key"] == "k-test"
    assert captured["payload"]["system"] == "sys"


def test_anthropic_without_key_is_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    backend = AnthropicChatBackend(api_key="")
    available, detail = backend.check()
    assert available is False
    assert "key" in detail.lower()


# ----------------------------------------------------------------- claude cli
def test_claude_agent_unavailable_without_cli(tmp_path) -> None:
    # which() finds nothing AND the cmd-fallback probe fails -> not found.
    def runner(args, cwd, timeout):
        return 1, "", "'claude' is not recognized as an internal or external command"

    backend = ClaudeAgentBackend(
        tmp_path, which=lambda name: None, runner=runner, known_locations=()
    )
    available, detail = backend.check()
    assert available is False
    assert "not found" in detail


def test_claude_agent_finds_native_install_when_which_is_blind(tmp_path):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    calls = []

    def runner(args, cwd, timeout):
        calls.append(args)
        return 0, "installed", ""

    backend = ClaudeAgentBackend(
        tmp_path, which=lambda name: None, runner=runner, known_locations=(exe,)
    )
    assert backend.check(deep=True)[0] is True
    assert calls == [[str(exe), "--version"]]


def test_claude_agent_cannot_read_or_write_vault(tmp_path):
    calls = []
    backend = ClaudeAgentBackend(tmp_path, runner=lambda *args: calls.append(args))
    with pytest.raises(BackendError, match="vault access is disabled"):
        backend.run_task("do the thing")
    assert calls == []


def test_claude_agent_wraps_windows_npm_shim(tmp_path):
    backend = ClaudeAgentBackend(tmp_path, which=lambda name: "synthetic/claude.CMD")
    assert backend._argv(["--version"]) == [
        "cmd",
        "/d",
        "/c",
        "synthetic/claude.CMD",
        "--version",
    ]


def test_autodetect_picks_first_available_candidate(tmp_path) -> None:
    class Unavailable:
        name = "Dead"

        def check(self):
            return False, "no"

    class Available:
        name = "Alive"

        def check(self):
            return True, "yes"

    backend, detail = ai_backend.autodetect_backend(
        tmp_path, candidates=[Unavailable(), Available()], persist=False
    )
    assert backend is not None and backend.name == "Alive"
    assert "Alive" in detail

    backend, detail = ai_backend.autodetect_backend(
        tmp_path, candidates=[Unavailable()], persist=False
    )
    assert backend is None
    assert "Dead" in detail


# -------------------------------------------------------------- orchestration
class FakeChatBackend:
    name = "Fake"

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.last_system: str | None = None

    def check(self):
        return True, "ok"

    def chat(self, messages, system=None):
        self.last_system = getattr(messages, "system", system)
        return self.reply


def test_legacy_report_without_localization_cannot_overwrite_reports(tmp_path) -> None:
    store = _store(tmp_path)
    reply = (
        "===SELF_PORTRAIT_MD===\n# Portrait\n"
        "===SELF_PORTRAIT_DETAILED_MD===\n# Detailed\n"
        "===SELF_PORTRAIT_JSON===\n"
        + json.dumps(
            {
                "schema_version": "0.2",
                "report_type": "self_portrait",
                "data_coverage": {
                    "sources_read": ["synthetic note"],
                    "covered": [],
                    "not_covered": ["history"],
                },
                "claims": [],
                "consistency_findings": [],
                "open_questions": [],
                "caveats": ["Limited synthetic data."],
            }
        )
        + "\n===END==="
    )
    backend = FakeChatBackend(reply)

    store.self_portrait_path.write_text("Previous validated report", encoding="utf-8")
    with pytest.raises(BackendError):
        run_self_portrait(backend, store)
    assert store.self_portrait_path.read_text(encoding="utf-8") == "Previous validated report"
    assert not store.self_portrait_detailed_path.exists()
    # The contract is the system prompt; the user's data is inlined in the call.
    assert "Self-Portrait Request" in backend.last_system


def test_run_self_portrait_rejects_invalid_json(tmp_path) -> None:
    store = _store(tmp_path)
    reply = (
        "===SELF_PORTRAIT_MD===\nx\n===SELF_PORTRAIT_DETAILED_MD===\ny\n"
        "===SELF_PORTRAIT_JSON===\nnot json\n===END==="
    )
    with pytest.raises(BackendError, match="not valid JSON"):
        run_self_portrait(FakeChatBackend(reply), store)


def test_run_criteria_synthesis_saves_reports_and_transcript(tmp_path) -> None:
    store = _store(tmp_path)
    reply = (
        "===MATE_CRITERIA_MD===\n# Criteria\n"
        "===MATE_CRITERIA_JSON===\n"
        + json.dumps(
            {
                "schema_version": "0.1",
                "report_type": "mate_criteria",
                "stated": [],
                "revealed": [],
                "open_questions": [],
                "caveats": ["Insufficient interview evidence."],
            }
        )
        + "\n===IDEAL_PROFILES_JSON===\n"
        + json.dumps(
            {"schema_version": "0.1", "candidates": [], "caveats": ["No exercise completed."]}
        )
        + "\n===END==="
    )
    messages = [
        {"role": "user", "content": "ready"},
        {"role": "assistant", "content": "q1?"},
        {"role": "user", "content": "a1"},
    ]

    with pytest.raises(BackendError):
        run_criteria_synthesis(FakeChatBackend(reply), store, messages, "system")
    localized = {
        "criteria": {
            "schema_version": "0.1",
            "stated": [],
            "revealed": [],
            "open_questions": [],
            "caveats": ["Insufficient interview evidence."],
        },
        "ideal_profiles": {
            "schema_version": "0.1",
            "candidates": [],
            "caveats": ["No exercise completed."],
        },
        "localized_text": [
            {
                "path": "/criteria/caveats/0",
                "source": "Insufficient interview evidence.",
                "en": "Insufficient interview evidence.",
                "zh": "访谈证据不足。",
            },
            {
                "path": "/ideal_profiles/caveats/0",
                "source": "No exercise completed.",
                "en": "No exercise completed.",
                "zh": "尚未完成假想候选人练习。",
            },
        ],
    }
    path = run_criteria_synthesis(FakeChatBackend(json.dumps(localized)), store, messages, "system")

    assert path == store.mate_criteria_path
    assert store.mate_criteria_json_path.exists()
    assert store.ideal_profiles_json_path.exists()
    transcript = store.imports_dir / "interview" / "criteria_interview_transcript.md"
    assert "q1?" in transcript.read_text(encoding="utf-8")


def test_build_interview_system_includes_contract_and_live_rules(tmp_path) -> None:
    store = _store(tmp_path)
    system = ai_backend.build_interview_system(store)
    assert "Do not conform to the user's views" in system
    assert "ONE question per reply" in system
    assert "imports/notes.md" not in system
    assert "honesty and quiet evenings" not in system
    assert "honesty and quiet evenings" in ai_backend.build_interview_context(store)


# ------------------------------------------------------------------- settings
def test_ai_settings_roundtrip_never_persists_secrets(tmp_path) -> None:
    path = tmp_path / "ai.json"
    ai_settings.save_settings(
        ai_settings.AISettings(mode=ai_settings.MODE_OLLAMA, ollama_model="phi3"), path
    )
    loaded = ai_settings.load_settings(path)
    assert loaded.mode == ai_settings.MODE_OLLAMA
    assert loaded.ollama_model == "phi3"
    raw = path.read_text(encoding="utf-8").lower()
    assert "key" not in raw and "token" not in raw


def test_active_backend_registry_roundtrip() -> None:
    fake = FakeChatBackend("x")
    ai_backend.set_active(fake)
    assert ai_backend.get_active() is fake
    assert ai_backend.active_name() == "Fake"
    ai_backend.set_active(None)
    assert ai_backend.active_name() is None


def test_inline_vault_data_caps_size(tmp_path) -> None:
    store = _store(tmp_path)
    store.save_import_text("x" * 20000, "huge.md")
    text = ai_backend.inline_vault_data(store)
    assert "truncated for length" in text
    assert len(text) < 40000
    assert "notes.md" in text


def test_self_portrait_prompt_note_lists_all_sections() -> None:
    # Guard against drift between the format note and the parser's expectations.
    for name in ai_backend._PORTRAIT_SECTIONS:
        assert name in ai_backend._PORTRAIT_FORMAT_NOTE
    for name in ai_backend._CRITERIA_SECTIONS:
        assert name in ai_backend._CRITERIA_FORMAT_NOTE
    assert agent_handoff.MATE_CRITERIA_MD_NAME == "mate_criteria.md"


def _structured_portrait_reply() -> str:
    return json.dumps(
        {
            "report": {
                "schema_version": "0.2",
                "claims": [],
                "consistency_findings": [],
                "data_coverage": {
                    "sources_read": ["synthetic notes"],
                    "covered": [],
                    "not_covered": ["History is unknown."],
                },
                "open_questions": ["What matters most in a relationship?"],
                "caveats": ["Limited synthetic input; conclusions remain provisional."],
            },
            "localized_text": [
                {
                    "path": "/report/data_coverage/not_covered/0",
                    "source": "History is unknown.",
                    "en": "History is unknown.",
                    "zh": "尚不了解关系经历。",
                },
                {
                    "path": "/report/open_questions/0",
                    "source": "What matters most in a relationship?",
                    "en": "What matters most in a relationship?",
                    "zh": "你最看重关系中的什么？",
                },
                {
                    "path": "/report/caveats/0",
                    "source": "Limited synthetic input; conclusions remain provisional.",
                    "en": "Limited synthetic input; conclusions remain provisional.",
                    "zh": "虚构测试材料有限，结论仍属暂定。",
                },
            ],
        }
    )


def test_structured_portrait_roundtrip_uses_native_output_schema(tmp_path):
    store = _store(tmp_path)
    request = ai_backend.prepare_self_portrait_request(store)
    assert set(request.response_schema["required"]) == {
        "report",
        "localized_text",
    }
    assert "honesty and quiet evenings" not in request.system
    assert "honesty and quiet evenings" in request.messages[0].content
    run_self_portrait(FakeChatBackend(_structured_portrait_reply()), store, request=request)
    report = json.loads(store.self_portrait_json_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "0.2"
    assert report["generated_at"]
    assert "中文版" in store.self_portrait_path.read_text(encoding="utf-8")
    assert "尚不了解关系经历" in store.self_portrait_detailed_path.read_text(encoding="utf-8")
    assert store.self_portrait_json_path.with_name("self_portrait_localization.json").is_file()


@pytest.mark.parametrize(
    "failure",
    ["truncated", "invalid_report", "missing_localization", "extra_narrative", "free_summary"],
)
def test_invalid_structured_portrait_never_overwrites_existing_reports(tmp_path, failure):
    store = _store(tmp_path)
    paths = [
        store.self_portrait_path,
        store.self_portrait_detailed_path,
        store.self_portrait_json_path,
    ]
    for path in paths:
        path.write_text("previous approved report", encoding="utf-8")
    data = json.loads(_structured_portrait_reply())
    if failure == "invalid_report":
        data["report"]["claims"] = [{"claim": "Unsupported assertion"}]
    elif failure == "missing_localization":
        del data["localized_text"]
    elif failure == "extra_narrative":
        data["markdown"] = "An unvalidated personality verdict outside the canonical report."
    elif failure == "free_summary":
        data["report"]["summary"] = {"en": "Unsupported conclusion.", "zh": "没有依据的结论。"}
    reply = json.dumps(data)
    if failure == "truncated":
        reply = reply[:50]
    with pytest.raises(BackendError, match="bundle is incomplete or invalid"):
        run_self_portrait(FakeChatBackend(reply), store)
    assert all(path.read_text(encoding="utf-8") == "previous approved report" for path in paths)


def test_structured_criteria_saves_only_validated_companions(tmp_path):
    store = _store(tmp_path)
    data = {
        "criteria": {
            "schema_version": "0.1",
            "stated": [],
            "revealed": [],
            "open_questions": [],
            "caveats": ["No supported preference inference."],
        },
        "ideal_profiles": {
            "schema_version": "0.1",
            "candidates": [],
            "caveats": ["No fictional candidate exercise completed."],
        },
        "localized_text": [
            {
                "path": "/criteria/caveats/0",
                "source": "No supported preference inference.",
                "en": "No supported preference inference.",
                "zh": "暂无依据推断偏好，需要继续访谈。",
            },
            {
                "path": "/ideal_profiles/caveats/0",
                "source": "No fictional candidate exercise completed.",
                "en": "No fictional candidate exercise completed.",
                "zh": "尚未完成假想候选人练习。",
            },
        ],
    }
    messages = [{"role": "user", "content": "I need time to consider."}]
    request = ai_backend.prepare_criteria_request(store, messages, "stale untrusted system")
    assert "stale untrusted system" not in request.system
    assert set(request.response_schema["required"]) == {
        "localized_text",
        "criteria",
        "ideal_profiles",
    }
    run_criteria_synthesis(FakeChatBackend(json.dumps(data)), store, messages, "", request=request)
    assert "需要继续访谈" in store.mate_criteria_path.read_text(encoding="utf-8")
    assert (
        json.loads(store.ideal_profiles_json_path.read_text(encoding="utf-8"))["candidates"] == []
    )


def test_invalid_local_bundle_retries_once_with_untrusted_reply_as_data(tmp_path):
    store = _store(tmp_path)

    class LocalRepairBackend:
        local = True

        def __init__(self):
            self.calls = []

        def chat(self, request):
            self.calls.append(request)
            if len(self.calls) == 1:
                return '{"markdown":"UNTRUSTED_IGNORE_THE_SYSTEM"}'
            return _structured_portrait_reply()

    backend = LocalRepairBackend()
    run_self_portrait(backend, store)
    assert len(backend.calls) == 2
    original, correction = backend.calls
    assert correction.system == original.system
    assert "UNTRUSTED_IGNORE_THE_SYSTEM" not in correction.system
    assert correction.messages[-2].role == "assistant"
    assert "UNTRUSTED_IGNORE_THE_SYSTEM" in correction.messages[-2].content
    assert correction.response_schema == original.response_schema


def test_local_bundle_correction_is_bounded_and_remote_never_retries(tmp_path):
    store = _store(tmp_path)

    class AlwaysInvalid:
        def __init__(self, local):
            self.local, self.calls = local, 0

        def chat(self, request):
            self.calls += 1
            return '{"markdown":"incomplete"}'

    for local, expected_calls in ((True, 2), (False, 1)):
        backend = AlwaysInvalid(local)
        with pytest.raises(BackendError, match="bundle is incomplete"):
            run_self_portrait(backend, store)
        assert backend.calls == expected_calls
        assert not store.self_portrait_path.exists()


def test_report_evidence_must_quote_original_input(tmp_path):
    store = _store(tmp_path)
    data = json.loads(_structured_portrait_reply())
    data["report"]["claims"] = [
        {
            "topic": "values",
            "claim": "Unsupported statement.",
            "type": "observation",
            "confidence": "low",
            "evidence": [
                {"quote": "Fabricated quote absent from input.", "source": "synthetic notes"}
            ],
        }
    ]
    with pytest.raises(BackendError, match="evidence absent"):
        run_self_portrait(FakeChatBackend(json.dumps(data)), store)
    assert not store.self_portrait_path.exists()


def test_bundle_schema_is_inline_for_local_schema_grammar(tmp_path):
    request = ai_backend.prepare_self_portrait_request(_store(tmp_path))
    encoded = json.dumps(request.response_schema)
    assert '"$ref"' not in encoded and '"$defs"' not in encoded
    topics = request.response_schema["properties"]["report"]["properties"]["claims"]
    assert "open_questions" not in topics["items"]["properties"]["topic"]["enum"]


def test_assistant_questions_cannot_ground_owner_criteria(tmp_path):
    store = _store(tmp_path)
    owner_claim = {
        "topic": "values",
        "claim": "The owner prioritizes marriage.",
        "type": "inference",
        "confidence": "low",
        "evidence": [{"quote": "Do you prioritize marriage?", "source": "interview"}],
    }
    response = {
        "localized_text": [],
        "criteria": {
            "schema_version": "0.1",
            "stated": [],
            "revealed": [owner_claim],
            "open_questions": [],
            "caveats": ["Uncertain."],
        },
        "ideal_profiles": {"schema_version": "0.1", "candidates": [], "caveats": ["No exercise."]},
    }
    history = [
        {"role": "assistant", "content": "Do you prioritize marriage?"},
        {"role": "user", "content": "I am unsure."},
    ]
    with pytest.raises(BackendError, match="evidence absent"):
        run_criteria_synthesis(FakeChatBackend(json.dumps(response)), store, history, "")
    assert not store.mate_criteria_path.exists()


def test_legacy_delimiter_reply_cannot_bypass_evidence_grounding(tmp_path):
    store = _store(tmp_path)
    response = json.loads(_structured_portrait_reply())
    response["report"]["claims"] = [
        {
            "topic": "values",
            "claim": "Unsupported statement.",
            "type": "observation",
            "confidence": "low",
            "evidence": [{"quote": "An invented quotation.", "source": "notes"}],
        }
    ]
    legacy = (
        "===SELF_PORTRAIT_MD===\n"
        + "Legacy summary"
        + "\n===SELF_PORTRAIT_DETAILED_MD===\n"
        + "Legacy detailed report"
        + "\n===SELF_PORTRAIT_JSON===\n"
        + json.dumps(response["report"])
        + "\n===END==="
    )
    with pytest.raises(BackendError, match="evidence absent"):
        run_self_portrait(FakeChatBackend(legacy), store)
    assert not store.self_portrait_path.exists()


def test_generated_portrait_and_transcript_never_become_owner_reference_data(tmp_path):
    store = _store(tmp_path)
    store.self_portrait_detailed_path.write_text("GENERATED_MODEL_INFERENCE", encoding="utf-8")
    interview = store.imports_dir / "interview"
    interview.mkdir(exist_ok=True)
    (interview / "criteria_interview_transcript.md").write_text(
        "GENERATED_INTERVIEW_QUESTION", encoding="utf-8"
    )
    (interview / "criteria_interview_user_notes.md").write_text(
        "USER_PROVIDED_ANSWER", encoding="utf-8"
    )
    context = ai_backend.build_interview_context(store)
    assert "GENERATED_MODEL_INFERENCE" not in context
    assert "GENERATED_INTERVIEW_QUESTION" not in context
    assert "USER_PROVIDED_ANSWER" in context
    reference = ai_backend.build_interview_reference(store)
    assert "GENERATED_MODEL_INFERENCE" in reference
    assert "not owner evidence" in reference
