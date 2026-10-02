import json

import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.api import routes_local_ai, routes_matchmaking
from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.reports.canonical_json import document_hash

# Synthetic profile only (no real user data in tests).
PROFILE = {
    "schema_version": "0.1",
    "tier2_summary": {
        "values": ["honesty"],
        "life_goals": "synthetic",
        "communication_style": "patient",
        "boundaries": "no money",
        "uncertainty_notes": "Limited synthetic notes.",
        "evidence_notes": "Synthetic self-report only.",
    },
    "source": "self_model_from_ai_analysis_of_own_data",
}


class StubBackend:
    name = "Stub AI"
    model = "stub-1"

    def chat(self, messages, system=None):  # noqa: ANN001 - test stub
        assert "USER DATA" in messages[0]["content"]
        assert system and "Do NOT flatter" in system
        return (
            "Here you go:\n```json\n"
            + json.dumps(
                {
                    "values": ["honesty", "curiosity"],
                    "life_goals": "synthetic goals",
                    "communication_style": "direct",
                    "boundaries": "clear",
                    "uncertainty_notes": "unsure",
                    "evidence_notes": "from synthetic notes",
                }
            )
            + "\n```"
        )


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(routes_local_ai, "VAULT_DIR", tmp_path)
    monkeypatch.setattr(routes_local_ai, "APP_POINTER_PATH", tmp_path / "pointer" / "app.json")
    monkeypatch.setattr(routes_local_ai, "SELF_MODEL_PATH", tmp_path / "self_model.json")
    monkeypatch.setattr(routes_local_ai, "SETTINGS_PATH", tmp_path / "client_settings.json")
    monkeypatch.setattr(routes_local_ai, "NOTES_PATH", tmp_path / "imports" / "notes.md")
    monkeypatch.setattr(
        routes_local_ai, "PORTRAIT_MD_PATH", tmp_path / "reports" / "social_self_portrait.md"
    )
    monkeypatch.setattr(
        routes_local_ai, "PORTRAIT_JSON_PATH", tmp_path / "reports" / "social_self_portrait.json"
    )
    monkeypatch.setattr(
        routes_local_ai, "PORTRAIT_EN_PATH", tmp_path / "reports" / "social_self_portrait.en.md"
    )
    monkeypatch.setattr(
        routes_local_ai, "PORTRAIT_ZH_PATH", tmp_path / "reports" / "social_self_portrait.zh.md"
    )
    monkeypatch.setattr(
        routes_local_ai, "PLAN_MD_PATH", tmp_path / "reports" / "relationship_plan.md"
    )
    monkeypatch.setattr(
        routes_local_ai, "PLAN_JSON_PATH", tmp_path / "reports" / "relationship_plan.json"
    )
    routes_local_ai.reset_backend()
    routes_matchmaking.reset_service()
    return TestClient(create_client_app(), base_url="http://127.0.0.1:8471")


def _set_backend(client: TestClient, backend) -> None:
    state = client.app.state.local_client_state
    state.set_backend(backend, state.snapshot().generation)


def test_vault_switch_relocates_all_state(client: TestClient, tmp_path) -> None:
    """Obsidian model: switching the vault folder switches model/report/notes."""
    # Save a model into the current (patched) vault, then switch to a new one.
    client.post("/local/profile/save", json={"profile": PROFILE})
    assert client.get("/local/profile/load").json()["profile"] == PROFILE

    other = tmp_path / "synced-vault"
    other.mkdir()
    result = client.post("/local/vault/config", json={"path": str(other)}).json()
    assert result["vault_dir"] == str(other)
    assert result["model_saved"] is False  # the new vault is empty

    # The pointer persisted, and loads resolve against the new vault now.
    pointer = json.loads((tmp_path / "pointer" / "app.json").read_text(encoding="utf-8"))
    assert pointer["vault_dir"] == str(other)
    assert client.get("/local/profile/load").json()["profile"] is None
    assert client.get("/local/status").json()["vault_dir"] == str(other)

    # Saving now writes INTO the synced vault folder.
    client.post("/local/profile/save", json={"profile": PROFILE})
    assert (other / "self_model.json").exists()

    missing = client.post("/local/vault/config", json={"path": str(other / "nope")})
    assert missing.status_code == 400


def test_report_falls_back_to_desktop_prototype_artifacts(client: TestClient, tmp_path) -> None:
    """A vault created by the PySide6 prototype renders immediately."""
    vault = tmp_path / "desktop-vault"
    (vault / "reports").mkdir(parents=True)
    (vault / "reports" / "self_portrait.md").write_text(
        "# Your Self-Portrait\nsynthetic desktop portrait\n", encoding="utf-8"
    )
    (vault / "reports" / "self_portrait.json").write_text(
        json.dumps({"generated_at": "2026-07-10"}), encoding="utf-8"
    )
    switched = client.post("/local/vault/config", json={"path": str(vault)}).json()
    assert switched["report_exists"] is True

    stored = client.get("/local/report").json()
    assert stored["exists"] is True
    assert stored["legacy"] is True
    assert "synthetic desktop portrait" in stored["md"]
    assert stored["generated_at"] == "2026-07-10"


def test_vault_imports_dir_counts_as_data_and_skips_dot_dirs(
    client: TestClient, tmp_path
) -> None:
    vault = tmp_path / "vault2"
    (vault / "imports" / ".obsidian").mkdir(parents=True)
    (vault / "imports" / "chat.md").write_text("synthetic", encoding="utf-8")
    (vault / "imports" / ".obsidian" / "plugin.json").write_text("{}", encoding="utf-8")
    result = client.post("/local/vault/config", json={"path": str(vault)}).json()
    assert result["data_files"] == 1  # chat.md counted; dot-dir content excluded

    files = client.get("/local/data/list").json()
    assert [f["name"] for f in files["files"]] == ["chat.md"]


def test_client_app_serves_ui_matchmaking_and_local_status(client: TestClient) -> None:
    assert "AI-SlowMatch" in client.get("/").text
    assert client.get("/local/status").json()["local_client"] is True
    # matchmaking routes present too (register without consent -> 403 handler wired)
    assert (
        client.post(
            "/matchmaking/register",
            json={"pseudonym": "x", "geohash": "wtw3", "contact": "x", "age": 25},
        ).status_code
        == 403
    )


def test_ai_config_rejects_unknown_backend(client: TestClient) -> None:
    response = client.post("/local/ai/config", json={"backend": "skynet"})
    assert response.status_code == 400


def test_synthesize_requires_backend_then_parses_json(client: TestClient) -> None:
    no_backend = client.post("/local/ai/synthesize", json={"source_text": "hello"})
    assert no_backend.status_code == 400

    _set_backend(client, StubBackend())
    result = client.post(
        "/local/ai/synthesize", json={"source_text": "synthetic notes", "language": "English"}
    ).json()
    assert result["model"]["values"] == ["honesty", "curiosity"]
    assert result["backend"] == "Stub AI"

    empty = client.post("/local/ai/synthesize", json={"source_text": "   "})
    assert empty.status_code == 400


def test_profile_save_load_roundtrip_with_fingerprint(client: TestClient) -> None:
    saved = client.post("/local/profile/save", json={"profile": PROFILE}).json()
    assert saved["fingerprint"] == document_hash(PROFILE)

    loaded = client.get("/local/profile/load").json()
    assert loaded["profile"] == PROFILE
    assert loaded["fingerprint"] == saved["fingerprint"]


def test_extract_json_block_variants() -> None:
    payload = {"values": ["a"]}
    fenced = "text\n```json\n" + json.dumps(payload) + "\n```\nmore"
    bare = "prefix " + json.dumps(payload) + " suffix"
    assert routes_local_ai.extract_json_block(fenced) == payload
    assert routes_local_ai.extract_json_block(bare) == payload
    with pytest.raises(routes_local_ai.BackendError):
        routes_local_ai.extract_json_block("no json here")


def test_import_chatgpt_rejects_empty_body(client: TestClient) -> None:
    assert client.post("/local/import/chatgpt", content=b"").status_code == 400


def test_chat_endpoint_uses_interview_contract(client: TestClient) -> None:
    class ChatStub:
        name = "Stub AI"
        model = "stub-1"

        def chat(self, messages, system=None):  # noqa: ANN001 - test stub
            assert "Do NOT flatter" in system
            assert "reflective interviewer" in system
            assert messages[-1]["content"] == "What are my patterns?"
            return "One question at a time: how do you handle conflict?"

    assert client.post("/local/ai/chat", json={"messages": []}).status_code == 400
    _set_backend(client, ChatStub())
    result = client.post(
        "/local/ai/chat",
        json={"messages": [{"role": "user", "content": "What are my patterns?"}]},
    ).json()
    assert "conflict" in result["reply"]


def test_refine_returns_updated_model(client: TestClient) -> None:
    class RefineStub:
        name = "Stub AI"
        model = "stub-1"

        def chat(self, messages, system=None):  # noqa: ANN001 - test stub
            assert messages[-1]["content"].startswith("Based on our whole conversation")
            return json.dumps(
                {
                    "values": ["honesty"],
                    "life_goals": "updated",
                    "communication_style": "updated",
                    "boundaries": "updated",
                    "uncertainty_notes": "updated",
                    "evidence_notes": "from chat",
                }
            )

    _set_backend(client, RefineStub())
    client.post("/local/data/notes", json={"text": "Synthetic owner notes for refinement."})
    result = client.post("/local/ai/refine", json={"messages": []}).json()
    assert result["model"]["life_goals"] == "updated"


def test_data_config_and_notes(client: TestClient, tmp_path) -> None:
    bad = client.post("/local/data/config", json={"path": str(tmp_path / "missing")})
    assert bad.status_code == 400

    data_dir = tmp_path / "exports"
    data_dir.mkdir()
    (data_dir / "notes.txt").write_text("synthetic", encoding="utf-8")
    (data_dir / "skip.exe").write_text("ignored", encoding="utf-8")
    result = client.post("/local/data/config", json={"path": str(data_dir)}).json()
    assert result["count"] == 1
    assert result["files"][0]["name"] == "notes.txt"

    saved = client.post("/local/data/notes", json={"text": "pasted synthetic notes"}).json()
    assert saved["saved"] is True
    assert client.get("/local/data/list").json()["count"] == 2  # folder file + notes.md

    # Settings persisted (path only, never secrets) and echoed by /status.
    status = client.get("/local/status").json()
    assert status["settings"]["data_dir"] == str(data_dir)
    assert status["data_files"] == 2


def test_compare_endpoint_writes_reflection(client: TestClient) -> None:
    class CompareStub:
        name = "Stub AI"
        model = "stub-1"

        def chat(self, messages, system=None):  # noqa: ANN001 - test stub
            assert "NON-SCORING" in system
            assert "CARD A (me)" in messages[0]["content"]
            return "You share honesty; discuss weekends in person."

    _set_backend(client, CompareStub())
    # No saved self-model yet -> 400
    missing = client.post(
        "/local/ai/compare", json={"their_card": PROFILE, "counterpart_consent_confirmed": True}
    )
    assert missing.status_code == 400

    client.post("/local/profile/save", json={"profile": PROFILE})
    result = client.post(
        "/local/ai/compare", json={"their_card": PROFILE, "counterpart_consent_confirmed": True}
    ).json()
    assert "honesty" in result["reflection"]


def test_deep_analysis_writes_portrait_and_report_endpoint(client: TestClient) -> None:
    portrait_json = {
        "schema_version": "0.2",
        "generated_at": "<ISO-8601>",  # model placeholder; server must overwrite
        "data_coverage": {"sources_read": ["notes.md"], "covered": ["values"], "not_covered": []},
        "claims": [
            {
                "topic": "values",
                "claim": "synthetic",
                "evidence": [{"quote": "synthetic", "source": "imports/notes.md"}],
                "type": "observation",
                "confidence": "low",
            }
        ],
        "consistency_findings": [],
        "open_questions": [],
        "caveats": ["synthetic test"],
    }

    class AnalyzeStub:
        name = "Stub AI"
        model = "stub-1"

        def chat(self, messages, system=None):  # noqa: ANN001 - test stub
            assert "Chat-Analysis Module" in system
            assert "Disclosure-volume guard" in system
            # Transport addendum: fully separated language sections, never mixed.
            assert "SOCIAL_SELF_PORTRAIT_MD_EN" in system
            assert "never mixed" in system
            return (
                "===SOCIAL_SELF_PORTRAIT_MD_EN===\n# Portrait\nsynthetic body\n"
                "===SOCIAL_SELF_PORTRAIT_MD_ZH===\n# 画像\n合成正文\n"
                "===SOCIAL_SELF_PORTRAIT_JSON===\n" + json.dumps(portrait_json) + "\n===END==="
            )

    # No data yet -> evidence-bound refusal even with a backend connected.
    _set_backend(client, AnalyzeStub())
    assert client.post("/local/ai/analyze", json={"messages": []}).status_code == 400

    client.post("/local/data/notes", json={"text": "synthetic notes"})
    result = client.post("/local/ai/analyze", json={"messages": []}).json()
    assert result["claims"] == 1
    assert result["generated_at"] != "<ISO-8601>"  # server stamped a real timestamp
    assert "synthetic body" in result["md_en"]
    assert "合成正文" in result["md_zh"]

    stored = client.get("/local/report").json()
    assert stored["exists"] is True
    assert "synthetic body" in stored["md"]  # legacy fallback = English copy
    assert "synthetic body" in stored["md_en"]
    assert "合成正文" in stored["md_zh"]
    assert stored["generated_at"] == result["generated_at"]
    assert routes_local_ai.PORTRAIT_EN_PATH.exists()
    assert routes_local_ai.PORTRAIT_ZH_PATH.exists()

    on_disk = json.loads(routes_local_ai.PORTRAIT_JSON_PATH.read_text(encoding="utf-8"))
    assert on_disk["claims"][0]["confidence"] == "low"


def test_parse_delimited_reports_missing_sections() -> None:
    from anti_dating_scam.ai.chat_backends import BackendError

    with pytest.raises(BackendError, match="SOCIAL_SELF_PORTRAIT_JSON"):
        routes_local_ai.parse_delimited(
            "===SOCIAL_SELF_PORTRAIT_MD===\nonly md\n===END===",
            ["SOCIAL_SELF_PORTRAIT_MD", "SOCIAL_SELF_PORTRAIT_JSON"],
        )


def test_openai_compat_backend() -> None:
    from anti_dating_scam.ai.chat_backends import BackendError, OpenAICompatChatBackend
    from anti_dating_scam.ai.privacy import build_reviewed_request

    seen: dict = {}

    def fake_http(url, payload, headers, timeout):  # noqa: ANN001 - test stub
        seen.update(url=url, payload=payload, headers=headers)
        return {"choices": [{"message": {"content": "compat reply"}}]}

    backend = OpenAICompatChatBackend(
        base_url="https://ark.example.test/api/v3",
        api_key="k",
        model="doubao-x",
        transport=fake_http,
    )
    ok, _ = backend.check()
    assert ok
    reply = backend.chat(
        build_reviewed_request(
            [{"role": "user", "content": "hi"}], system="SYS", recipient=backend.recipient
        )
    )
    assert reply == "compat reply"
    assert seen["url"].endswith("/chat/completions")
    assert seen["headers"]["Authorization"] == "Bearer k"
    assert seen["payload"]["messages"][0] == {"role": "system", "content": "SYS"}

    keyless = OpenAICompatChatBackend(base_url="https://x.test", model="m")
    ok, detail = keyless.check()
    assert not ok and "key" in detail.lower()
    with pytest.raises(BackendError):
        keyless.chat([{"role": "user", "content": "hi"}])


def test_gemini_cli_preset_requires_verified_isolation() -> None:
    from anti_dating_scam.ai.chat_backends import BackendError, CliAgentBackend
    from anti_dating_scam.ai.privacy import build_reviewed_request

    calls = []
    gemini = CliAgentBackend(cli="gemini", runner=lambda *args: calls.append(args))
    request = build_reviewed_request(
        [{"role": "user", "content": "reviewed"}],
        recipient=gemini.recipient,
    )
    with pytest.raises(BackendError, match="verified data-only"):
        gemini.chat(request)
    assert calls == []


def test_nearby_precision_param() -> None:
    from anti_dating_scam.main import create_app
    from anti_dating_scam.matchmaking.geo import encode_geohash

    routes_matchmaking.reset_service()
    api_client = TestClient(create_app())
    tokens = {}
    # Same precision-3 cell (wtw…) but different precision-4 buckets (wtw3 / wtw6).
    spots = {"near": (31.2304, 121.4737), "far": (31.4304, 121.4737)}
    for name, (lat, lon) in spots.items():
        response = api_client.post(
            "/matchmaking/register",
            json={
                "pseudonym": name,
                "geohash": encode_geohash(lat, lon),
                "contact": f"{name}@example.test",
                "consent_confirmed": True,
                "age": 25,
            },
        )
        tokens[name] = response.json()["token"]
        api_client.post(
            "/matchmaking/attest",
            json={"pseudonym": name, "token": tokens[name], "fingerprint": document_hash(PROFILE)},
        )
    default = api_client.get(
        "/matchmaking/nearby/near", headers={"Authorization": "Bearer " + tokens["near"]}
    ).json()
    wide = api_client.get(
        "/matchmaking/nearby/near?precision=3",
        headers={"Authorization": "Bearer " + tokens["near"]},
    ).json()
    assert [c["pseudonym"] for c in default["candidates"]] == []
    assert [c["pseudonym"] for c in wide["candidates"]] == ["far"]
    assert (
        api_client.get(
            "/matchmaking/nearby/near?precision=9",
            headers={"Authorization": "Bearer " + tokens["near"]},
        ).status_code
        == 400
    )


def test_cli_agent_backend_claude_and_codex() -> None:
    from anti_dating_scam.ai.chat_backends import BackendError, CliAgentBackend
    from anti_dating_scam.ai.privacy import build_reviewed_request

    calls = []

    def runner(argv, cwd, timeout, input_text=None):
        calls.append((argv, input_text))
        return 0, json.dumps({"result": "claude says hi"}), ""

    claude = CliAgentBackend(runner=runner, which=lambda name: "claude")
    ok, detail = claude.check()
    assert ok and "no model call" in detail
    assert calls == [(["claude", "--version"], None)]
    for content in ("hello", "again"):
        request = build_reviewed_request(
            [{"role": "user", "content": content}],
            system="CONTRACT",
            recipient=claude.recipient,
        )
        assert claude.chat(request) == "claude says hi"
        assert "--resume" not in calls[-1][0]
        assert content in calls[-1][1]

    codex = CliAgentBackend(cli="codex", runner=runner, which=lambda name: "codex")
    assert codex.check()[0] is False
    with pytest.raises(BackendError):
        CliAgentBackend(cli="unknown-cli")
