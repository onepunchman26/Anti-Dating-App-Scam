"""Known generated artifacts must not be promoted into owner evidence."""

import json

import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.ai.privacy import BackendError
from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.services.local_client_state import LocalClientState

MODEL = {
    "values": ["Unknown; needs confirmation"], "life_goals": "Unknown; needs confirmation",
    "communication_style": "Unknown; needs confirmation", "boundaries": "No money requests.",
    "uncertainty_notes": "Sparse synthetic source.", "evidence_notes": "Synthetic notes only.",
}


class RecordingBackend:
    name = "Synthetic provenance recorder"

    def __init__(self):
        self.calls = []

    def chat(self, messages, system=None):
        self.calls.append(messages)
        if "Chat-Analysis Module" in system:
            raise BackendError("Synthetic analysis stopped after recording inputs.")
        return json.dumps(MODEL)


@pytest.fixture
def provenance_client(tmp_path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "self_model.json").write_text('{"boundaries":"PRIOR_CARD_HALLUCINATION"}')
    (tmp_path / "reports" / "social_self_portrait.md").write_text("PRIOR_REPORT_HALLUCINATION")
    imports = tmp_path / "imports" / "interview"
    imports.mkdir(parents=True)
    (imports / "criteria_interview_transcript.md").write_text("MIXED_TRANSCRIPT_ASSISTANT")
    (imports / "criteria_interview_user_notes.md").write_text("OWNER_INTERVIEW_ANSWER")
    (tmp_path / "imports" / "notes.md").write_text("OWNER_ORIGINAL_NOTE")
    # Configured root imports must not accidentally include known generated outputs/settings.
    (tmp_path / "client_settings.json").write_text(json.dumps({"data_dir": str(tmp_path)}))
    backend = RecordingBackend()
    app = create_client_app()
    app.state.local_client_state = LocalClientState(tmp_path, tmp_path / "app.json", backend)
    return TestClient(app, base_url="http://127.0.0.1:8471"), backend, tmp_path


@pytest.mark.parametrize("endpoint,history", [
    ("chat", True), ("coach", True), ("refine", True), ("refine", False), ("analyze", False),
])
def test_original_data_and_generated_references_keep_distinct_roles(
    provenance_client, endpoint, history,
):
    client, backend, root = provenance_client
    messages = ([
        {"role": "user", "content": "OWNER_CURRENT_ANSWER"},
        {"role": "assistant", "content": "ASSISTANT_CURRENT_HYPOTHESIS"},
    ] if history else [])
    response = client.post("/local/ai/" + endpoint, json={"messages": messages})
    assert response.status_code == (400 if endpoint == "analyze" else 200), response.text
    sent = backend.calls[0]
    owner = "\n".join(message["content"] for message in sent if message["role"] == "user")
    assistants = "\n".join(
        message["content"] for message in sent if message["role"] == "assistant"
    )
    assert "OWNER_ORIGINAL_NOTE" in owner and "OWNER_INTERVIEW_ANSWER" in owner
    assert "PRIOR_CARD_HALLUCINATION" not in owner
    assert "PRIOR_REPORT_HALLUCINATION" not in owner
    assert "MIXED_TRANSCRIPT_ASSISTANT" not in str(sent)
    assert "client_settings.json" not in owner
    if history:
        assert "OWNER_CURRENT_ANSWER" in owner
        assert "ASSISTANT_CURRENT_HYPOTHESIS" not in owner
        assert "ASSISTANT_CURRENT_HYPOTHESIS" in assistants
        assert "PRIOR_CARD_HALLUCINATION" in assistants
        assert "PRIOR_REPORT_HALLUCINATION" in assistants
        assert "not owner evidence" in assistants
    else:
        assert "PRIOR_CARD_HALLUCINATION" not in str(sent)
        assert "PRIOR_REPORT_HALLUCINATION" not in str(sent)
    assert "PRIOR_CARD_HALLUCINATION" in (root / "self_model.json").read_text()


@pytest.mark.parametrize("endpoint", ["analyze", "refine"])
def test_old_reports_alone_cannot_support_fresh_generation(provenance_client, endpoint):
    client, backend, root = provenance_client
    (root / "imports" / "notes.md").unlink()
    (root / "imports" / "interview" / "criteria_interview_user_notes.md").unlink()
    result = client.post("/local/ai/" + endpoint, json={"messages": []})
    assert result.status_code == 400
    assert backend.calls == []
