import base64

import pytest
from fastapi.testclient import TestClient
from test_web_companion import setup

from anti_dating_scam.api.web_companion import SITE_ORIGIN, create_companion_app
from anti_dating_scam.services import voice_input
from anti_dating_scam.services.web_companion import CompanionError


def audio():
    return {
        "language": "en",
        "confirmed": True,
        "pcm_base64": base64.b64encode(b"\0\0" * 16000).decode(),
    }


def test_dictation_is_ephemeral_without_ai_or_session_mutation(tmp_path, monkeypatch):
    service, connection, request = setup(tmp_path)
    before = {p: p.read_bytes() for p in service.vault.root.rglob("*.json")}
    monkeypatch.setattr(voice_input, "recognizer_available", lambda: True)
    seen = []

    def recognize(pcm, **kwargs):
        seen.append((pcm, kwargs))
        return "I enjoy quiet walks."

    monkeypatch.setattr(voice_input, "transcribe_pcm", recognize)
    assert service.dispatch("voice-transcribe", audio()) == {
        "text": "I enjoy quiet walks.",
        "stored": False,
        "cloud": False,
    }
    assert seen[0][1]["root"] == service.state.root.parent / "speech-models"
    assert connection.requests is None
    assert service.read_session({"session_id": request["session_id"]}).revision == 0
    assert before == {p: p.read_bytes() for p in service.vault.root.rglob("*.json")}


@pytest.mark.parametrize("bad", [1, False, "true", None])
@pytest.mark.parametrize("op", ["voice-install", "voice-transcribe"])
def test_explicit_consent_never_coerced(tmp_path, bad, op):
    service, _, _ = setup(tmp_path)
    data = audio() if op == "voice-transcribe" else {"language": "en"}
    with pytest.raises(ValueError):
        service.dispatch(op, {**data, "confirmed": bad})


@pytest.mark.parametrize("mutation", ["cancel", "account"])
def test_late_result_discarded(tmp_path, monkeypatch, mutation):
    service, connection, _ = setup(tmp_path)
    monkeypatch.setattr(voice_input, "recognizer_available", lambda: True)

    def recognize(*_, **__):
        if mutation == "cancel":
            service.dispatch("stop", {})
        else:
            connection.identity = "synthetic-other"
        return "Never return this stale text."

    monkeypatch.setattr(voice_input, "transcribe_pcm", recognize)
    with pytest.raises(CompanionError, match="cancelled|account_changed"):
        service.dispatch("voice-transcribe", audio())
    assert not service.lock.locked()


def test_recording_boundaries_and_existing_api_limit(tmp_path, monkeypatch):
    service, _, _ = setup(tmp_path)
    monkeypatch.setattr(voice_input, "recognizer_available", lambda: True)
    monkeypatch.setattr(voice_input, "transcribe_pcm", lambda *a, **k: "Synthetic dictation")
    with TestClient(
        create_companion_app(service, pairing_token="synthetic"), base_url="http://127.0.0.1:8911"
    ) as client:
        headers = {"Origin": SITE_ORIGIN, "Authorization": "Bearer synthetic"}
        payload = {"operation": "voice-transcribe", "arguments": audio()}
        payload["arguments"]["pcm_base64"] = base64.b64encode(b"\0\0" * 480000).decode()
        assert client.post("/voice/v1", json=payload).status_code == 403
        assert client.post("/v1", json=payload, headers=headers).status_code == 413
        result = client.post("/voice/v1", json=payload, headers=headers)
        assert result.status_code == 200 and result.json()["result"]["stored"] is False
        assert (
            client.post(
                "/voice/v1", json={"operation": "send", "arguments": {}}, headers=headers
            ).status_code
            == 409
        )
        payload["arguments"]["pcm_base64"] += "AAAA"
        assert client.post("/voice/v1", json=payload, headers=headers).status_code == 400
        payload["arguments"]["pcm_base64"] = "!" * 5000
        assert client.post("/voice/v1", json=payload, headers=headers).status_code == 409


def test_install_requires_idle_and_reports_only_safe_failure(tmp_path, monkeypatch):
    service, _, _ = setup(tmp_path)
    monkeypatch.setattr(voice_input, "recognizer_available", lambda: True)
    service.lock.acquire()
    with pytest.raises(CompanionError, match="request_in_progress"):
        service.dispatch("voice-install", {"language": "zh", "confirmed": True})
    service.lock.release()

    def fail(*args, **kwargs):
        raise voice_input.VoiceInputError("synthetic sensitive internal details")

    monkeypatch.setattr(voice_input, "install_model", fail)
    with pytest.raises(CompanionError, match="^voice_unavailable$"):
        service.dispatch("voice-install", {"language": "zh", "confirmed": True})
