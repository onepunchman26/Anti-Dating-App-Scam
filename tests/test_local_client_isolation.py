"""Synthetic app/session races: no providers, network, or personal vault access."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.api import routes_local_ai as local
from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.services.local_client_state import LocalClientState


def make_client(root, backend=None):
    root.mkdir(parents=True, exist_ok=True)
    app = create_client_app()
    app.state.local_client_state = LocalClientState(root, root / "device" / "app.json", backend)
    return TestClient(app, base_url="http://127.0.0.1:8471")


class RecordingBackend:
    model = "synthetic"

    def __init__(self, name):
        self.name = name
        self.calls = []

    def chat(self, messages, system=None):
        self.calls.append(messages)
        return "Synthetic reflection with uncertainty."


def test_two_apps_do_not_share_backend_vault_notes_or_switches(tmp_path, monkeypatch):
    backend_a, backend_b = RecordingBackend("A"), RecordingBackend("B")
    a, b = make_client(tmp_path / "a", backend_a), make_client(tmp_path / "b", backend_b)
    # Legacy direct-call injection must not override either factory-owned session.
    monkeypatch.setattr(local, "_backend", RecordingBackend("legacy"))
    for client, marker in [(a, "synthetic alpha notes"), (b, "synthetic beta notes")]:
        assert client.post("/local/data/notes", json={"text": marker}).status_code == 200
        response = client.post(
            "/local/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Reflect on my synthetic notes.",
                    }
                ]
            },
        )
        assert response.status_code == 200
    assert "alpha" in str(backend_a.calls) and "beta" not in str(backend_a.calls)
    assert "beta" in str(backend_b.calls) and "alpha" not in str(backend_b.calls)
    other = tmp_path / "other"
    other.mkdir()
    assert a.post("/local/vault/config", json={"path": str(other)}).status_code == 200
    assert a.app.state.local_client_state.snapshot().backend is None
    assert b.app.state.local_client_state.snapshot().backend is backend_b
    assert b.get("/local/status").json()["vault_dir"] == str(tmp_path / "b")
    assert (tmp_path / "a" / "imports" / "notes.md").read_text() == "synthetic alpha notes"
    assert not (other / "imports" / "notes.md").exists()


def test_analysis_keeps_original_destination_and_backend_during_vault_switch(tmp_path):
    entered, release = Event(), Event()
    portrait = {
        "schema_version": "0.2",
        "data_coverage": {"sources_read": ["notes.md"], "covered": ["values"], "not_covered": []},
        "claims": [
            {
                "topic": "values",
                "claim": "Synthetic patience preference.",
                "evidence": [{"quote": "synthetic alpha notes", "source": "notes.md"}],
                "type": "observation",
                "confidence": "low",
            }
        ],
        "consistency_findings": [],
        "open_questions": [],
        "caveats": ["A synthetic sample."],
    }

    class SlowBackend(RecordingBackend):
        def chat(self, messages, system=None):
            self.calls.append(messages)
            entered.set()
            assert release.wait(10), "test must release synthetic backend"
            return (
                "===SOCIAL_SELF_PORTRAIT_MD_EN===\nSynthetic alpha portrait.\n"
                "===SOCIAL_SELF_PORTRAIT_MD_ZH===\n合成甲档案。\n"
                "===SOCIAL_SELF_PORTRAIT_JSON===\n" + json.dumps(portrait) + "\n===END==="
            )

    backend = SlowBackend("A")
    a, b = tmp_path / "a", tmp_path / "b"
    client = make_client(a, backend)
    b.mkdir()
    client.post("/local/data/notes", json={"text": "synthetic alpha notes"})
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(client.post, "/local/ai/analyze", json={"messages": []})
        try:
            assert entered.wait(5)
            switched = client.post("/local/vault/config", json={"path": str(b)})
            assert switched.status_code == 200
            assert client.get("/local/report").json()["exists"] is False
        finally:
            release.set()
        response = result.result(timeout=10)
    assert response.status_code == 200, response.text
    assert response.json()["backend"] == "A"
    assert response.headers["x-slowmatch-generation"] == "0"
    assert switched.headers["x-slowmatch-generation"] == "1"
    assert (a / "reports" / "social_self_portrait.json").is_file()
    assert "alpha" in str(backend.calls)
    assert list(b.iterdir()) == []


def test_stale_browser_generation_cannot_save_into_new_vault(tmp_path):
    client = make_client(tmp_path / "a")
    initial = client.get("/local/status")
    stale = {"X-Slowmatch-Generation": initial.headers["x-slowmatch-generation"]}
    b = tmp_path / "b"
    b.mkdir()
    assert (
        client.post("/local/vault/config", json={"path": str(b)}, headers=stale).status_code == 200
    )
    rejected = client.post("/local/data/notes", json={"text": "old tab data"}, headers=stale)
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "local_selection_changed"
    assert list(b.iterdir()) == []
    current = client.get("/local/status", headers=stale)
    assert current.status_code == 200
    assert current.headers["x-slowmatch-generation"] == "1"


def test_slow_backend_connect_cannot_install_credentials_after_vault_switch(tmp_path, monkeypatch):
    entered, release = Event(), Event()

    class ConnectingBackend:
        name = "Synthetic connection"

        def __init__(self, **kwargs):
            self.model = kwargs["model"]

        def check(self):
            entered.set()
            assert release.wait(10)
            return True, "connected"

    monkeypatch.setattr(local, "OllamaChatBackend", ConnectingBackend)
    client = make_client(tmp_path / "a")
    b = tmp_path / "b"
    b.mkdir()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(
            client.post, "/local/ai/config", json={"backend": "ollama", "model": "synthetic"}
        )
        try:
            assert entered.wait(5)
            assert client.post("/local/vault/config", json={"path": str(b)}).status_code == 200
        finally:
            release.set()
        assert result.result(timeout=10).status_code == 409
    assert client.app.state.local_client_state.snapshot().backend is None
    assert not (b / "client_settings.json").exists()


@pytest.mark.parametrize("endpoint", ["synthesize", "refine"])
def test_unknown_fields_are_explicit_in_both_self_model_prompts_and_preserved(tmp_path, endpoint):
    unknown = "未提供，需进一步确认"
    model = {
        "values": ["耐心"],
        "life_goals": unknown,
        "communication_style": unknown,
        "boundaries": "不向网络联系人汇款。",
        "uncertainty_notes": "人生目标与冲突处理方式未提供。",
        "evidence_notes": "合成用户只直接表达重视耐心和不汇款；其他字段没有证据。",
    }

    class UnknownBackend:
        name = "Synthetic unknown-preserving backend"

        def chat(self, messages, system=None):
            assert 'value MUST be "Unknown;' in system
            assert "do not infer life goals or conflict-handling style" in system.lower()
            assert "Required schema fields are not permission to invent" in system
            assert "Schema validity does not establish factual truth" in system
            return json.dumps(model)

    client = make_client(tmp_path / endpoint, UnknownBackend())
    notes = "Synthetic: I value patience; no money requests."
    client.post("/local/data/notes", json={"text": notes})
    payload = (
        {"source_text": notes}
        if endpoint == "synthesize"
        else {
            "messages": [{"role": "user", "content": "Please reflect only these synthetic notes."}],
        }
    )
    response = client.post(
        "/local/ai/" + endpoint,
        json={
            **payload,
            "language": "Simplified Chinese",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["model"] == model


@pytest.mark.parametrize("chosen", ["", " ", "missing-explicit-model"])
def test_ollama_default_uses_installed_chat_models_without_overriding_explicit_choice(
    tmp_path,
    monkeypatch,
    chosen,
):
    seen = []

    class LocalModelStub:
        name = "Synthetic local model selector"

        def __init__(self, *, base_url, model):
            self.model = model

        def installed_chat_models(self):
            assert not chosen.strip(), "explicit choices must not trigger automatic substitution"
            seen.append("list")
            return ["synthetic-small:latest", "synthetic-large:latest"]

        def check(self):
            seen.append(self.model)
            return (self.model == "synthetic-small:latest", "Synthetic availability result.")

    monkeypatch.setattr(local, "OllamaChatBackend", LocalModelStub)
    client = make_client(tmp_path / "vault")
    result = client.post("/local/ai/config", json={"backend": "ollama", "model": chosen})
    assert result.status_code == 200
    active = client.app.state.local_client_state.snapshot().backend
    if chosen.strip():
        assert not result.json()["ok"]
        assert active is None
        assert seen == [chosen]
    else:
        assert result.json()["ok"]
        assert active.model == "synthetic-small:latest"
        settings = json.loads((tmp_path / "vault" / "client_settings.json").read_text())
        assert settings["model"] == "synthetic-small:latest"
        assert seen == ["list", "synthetic-small:latest"]


def test_ollama_empty_safe_model_list_fails_without_download_or_remote_fallback(
    tmp_path, monkeypatch
):
    class EmptyLocalStub:
        name = "Synthetic empty local selector"

        def __init__(self, *, base_url, model):
            self.model = model

        def installed_chat_models(self):
            return []

        def check(self):
            pytest.fail("No model should be checked or used after an empty safe list.")

    monkeypatch.setattr(local, "OllamaChatBackend", EmptyLocalStub)
    client = make_client(tmp_path / "vault")
    response = client.post("/local/ai/config", json={"backend": "ollama"})
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "nothing was downloaded" in response.json()["detail"]
    assert "未下载" in response.json()["detail"]
    assert client.app.state.local_client_state.snapshot().backend is None
    assert not (tmp_path / "vault" / "client_settings.json").exists()
