import json

import pytest
from fastapi import HTTPException

from anti_dating_scam.api import routes_local_ai as mod


class FakeBackend:
    name = "Fake"
    model = "fake"

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.last_system: str | None = None

    def chat(self, messages, system=None):
        self.last_system = system
        self.last_messages = messages
        return self.reply


@pytest.fixture()
def sandbox(monkeypatch, tmp_path):
    """Point every vault/skill path at tmp so the real home is never touched."""
    for attr in (
        "VAULT_DIR",
        "SELF_MODEL_PATH",
        "SETTINGS_PATH",
        "NOTES_PATH",
        "PORTRAIT_MD_PATH",
        "PORTRAIT_JSON_PATH",
        "PLAN_MD_PATH",
        "PLAN_JSON_PATH",
    ):
        monkeypatch.setattr(mod, attr, tmp_path / attr.lower())
    monkeypatch.setattr(mod, "SKILL_DIRS", [tmp_path / "skillpack"])
    monkeypatch.setattr(mod, "_backend", None)
    return tmp_path


def _install_fake_skill(tmp_path) -> None:
    knowledge = tmp_path / "skillpack" / "references" / "knowledge"
    knowledge.mkdir(parents=True)
    for name in mod.COACH_KNOWLEDGE_FILES[:2]:
        (knowledge / name).write_text("KNOWLEDGE_MARKER " + name, encoding="utf-8")


def test_ollama_list_models_via_fake_transport() -> None:
    from anti_dating_scam.ai.chat_backends import OllamaChatBackend

    def transport(url, payload, headers, timeout):
        assert url.endswith("/api/tags")
        return {"models": [{"name": "qwen3.6:latest"}, {"name": "gemma4:latest"}, {}]}

    backend = OllamaChatBackend(transport=transport)
    assert backend.list_models() == ["qwen3.6:latest", "gemma4:latest"]


def test_models_endpoint_live_for_ollama_static_for_cli(sandbox, monkeypatch) -> None:
    class StubOllama:
        def __init__(self, base_url="", **_kwargs):
            pass

        def installed_chat_models(self):
            return ["qwen3.6:latest"]

    monkeypatch.setattr(mod, "OllamaChatBackend", StubOllama)

    live = mod.list_models(backend="ollama")
    assert live["source"] == "live"
    assert live["models"] == ["qwen3.6:latest"]

    static = mod.list_models(backend="claude")
    assert static["source"] == "static"
    assert "claude-haiku-4-5" in static["models"]
    assert mod.list_models(backend="unknown")["models"] == []


def test_coach_status_reports_skill_pack(sandbox) -> None:
    assert mod.coach_status()["skill_installed"] is False
    _install_fake_skill(sandbox)
    status = mod.coach_status()
    assert status["skill_installed"] is True
    assert "goutoujunshi" in status["install_hint"]


def test_coach_chat_grounds_in_knowledge_and_forbids_manipulation(sandbox, monkeypatch) -> None:
    _install_fake_skill(sandbox)
    backend = FakeBackend("coach reply")
    monkeypatch.setattr(mod, "_backend", backend)

    result = mod.coach_chat(mod.ChatRequest(messages=[{"role": "user", "content": "help"}]))

    assert result["reply"] == "coach reply"
    assert "KNOWLEDGE_MARKER" not in backend.last_system
    assert "KNOWLEDGE_MARKER" not in backend.last_messages[0]["content"]
    assert "Do not assign MBTI" in backend.last_messages[0]["content"]
    assert "no PUA tactics" in backend.last_system
    assert "Consent-first" in backend.last_system


def test_coach_chat_works_without_skill_pack(sandbox, monkeypatch) -> None:
    backend = FakeBackend("still helpful")
    monkeypatch.setattr(mod, "_backend", backend)

    result = mod.coach_chat(mod.ChatRequest(messages=[{"role": "user", "content": "hi"}]))

    assert result["reply"] == "still helpful"
    assert "Do not assign MBTI" in backend.last_messages[0]["content"]


def test_generate_plan_saves_files_and_rejects_empty(sandbox, monkeypatch) -> None:
    good = (
        "===RELATIONSHIP_PLAN_MD===\n# My Plan\n"
        "===RELATIONSHIP_PLAN_JSON===\n"
        '{"stages": [{"name": "meet", "goal": "g", "actions": ["a"],'
        ' "example_lines": [], "cautions": ["Slow down"], "ready_when": "r"}],'
        ' "uncertainty_notes":"Synthetic notes only"}\n===END==='
    )
    monkeypatch.setattr(mod, "_backend", FakeBackend(good))
    result = mod.generate_plan(mod.CoachPlanRequest())
    assert result["plan"]["stages"][0]["name"] == "meet"
    assert mod.PLAN_MD_PATH.read_text(encoding="utf-8").startswith("# My Plan")
    assert json.loads(mod.PLAN_JSON_PATH.read_text(encoding="utf-8"))["stages"]
    assert mod.get_plan()["exists"] is True

    empty = '===RELATIONSHIP_PLAN_MD===\nx\n===RELATIONSHIP_PLAN_JSON===\n{"stages": []}\n===END==='
    monkeypatch.setattr(mod, "_backend", FakeBackend(empty))
    with pytest.raises(HTTPException, match="empty plan"):
        mod.generate_plan(mod.CoachPlanRequest())


def test_outreach_mandates_manual_posting(sandbox, monkeypatch) -> None:
    backend = FakeBackend("post drafts")
    monkeypatch.setattr(mod, "_backend", backend)

    result = mod.outreach(mod.OutreachRequest(platform="Xiaohongshu"))

    assert result["drafts"] == "post drafts"
    assert "THEMSELVES" in backend.last_system  # humans post; never bots
    assert "Never suggest automation" in backend.last_system
    assert "Xiaohongshu" in backend.last_system


def test_simulate_requires_self_model_and_is_nonscoring(sandbox, monkeypatch) -> None:
    backend = FakeBackend("simulated dialogue")
    monkeypatch.setattr(mod, "_backend", backend)

    with pytest.raises(HTTPException, match="self-model"):
        mod.simulate(mod.SimulateRequest(their_card={"values": ["care"]}))

    mod.SELF_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    card = {
        "schema_version": "0.1",
        "source": "self_model_from_ai_analysis_of_own_data",
        "tier2_summary": {
            "values": ["honesty"],
            "life_goals": "synthetic",
            "communication_style": "patient",
            "boundaries": "slow pace",
            "uncertainty_notes": "Unverified synthetic note",
            "evidence_notes": "Synthetic self-report",
        },
    }
    mod.SELF_MODEL_PATH.write_text(json.dumps(card), encoding="utf-8")
    result = mod.simulate(mod.SimulateRequest(their_card=card, counterpart_consent_confirmed=True))

    assert result["simulation"] == "simulated dialogue"
    assert "never a score" in backend.last_system
    assert "rehearsal aid" in backend.last_system
