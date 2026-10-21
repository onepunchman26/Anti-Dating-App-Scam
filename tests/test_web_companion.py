from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.ai.privacy import BackendError, outbound_messages
from anti_dating_scam.api.web_companion import SITE_ORIGIN, create_companion_app
from anti_dating_scam.services.web_companion import CompanionError, WebCompanion
from anti_dating_scam.services.work_profile import WorkProfileError


class Connection:
    identity = "synthetic-registration-a"
    requests = None
    fail = False

    def status(self):
        return SimpleNamespace(
            connected=True, sharing=True, client_id=self.identity, label="Synthetic"
        )

    def diagnostic(self):
        return SimpleNamespace(phase="connected")

    def list_models(self):
        return [
            SimpleNamespace(model_dump=lambda: {"slug": "synthetic", "display_name": "Synthetic"})
        ]

    def create_backend(self, model, included_plan_confirmed):
        assert model == "synthetic" and included_plan_confirmed
        owner = self

        class Backend:
            recipient = "https://api.openai.com/v1/responses#synthetic"

            def set_cancel_event(self, event):
                self.cancel = event

            def chat_result(self, request):
                owner.requests = outbound_messages(request, recipient=self.recipient, local=False)
                if owner.fail:
                    raise BackendError("synthetic outage", category="network")
                return SimpleNamespace(text="What makes that activity feel comfortable for you?")

        return Backend()


def setup(tmp_path):
    connection = Connection()
    service = WebCompanion(tmp_path / "state", connection)
    service.initialize({"confirmed": True})
    session = service.create_session({"topic": "friendship"})
    request = {
        "session_id": session["id"],
        "expected_revision": 0,
        "text": "I enjoy reading.",
        "language": "en",
        "model": "synthetic",
        "cloud_consent": True,
        "included_plan_confirmed": True,
    }
    return service, connection, request


def test_durable_restart_account_and_revision(tmp_path):
    service, connection, request = setup(tmp_path)
    reply = service.send(request)
    assert reply["revision"] == 2
    recovered = WebCompanion(tmp_path / "state", connection)
    assert not recovered.status()["vault_ready"]
    recovered.initialize({"confirmed": True})
    assert (
        recovered.read_session({"session_id": request["session_id"]}).messages == reply["messages"]
    )
    assert not recovered.status()["inference_passed"]
    with pytest.raises(CompanionError, match="revision_conflict"):
        recovered.send(request)
    connection.identity = "synthetic-b"
    with pytest.raises(CompanionError, match="account_changed"):
        recovered.sessions()


@pytest.mark.parametrize("field", ["cloud_consent", "included_plan_confirmed"])
@pytest.mark.parametrize("bad", [False, 1, "true", None])
def test_consent_does_not_coerce(tmp_path, field, bad):
    service, connection, request = setup(tmp_path)
    request[field] = bad
    with pytest.raises(ValueError):
        service.send(request)
    assert connection.requests is None
    assert service.read_session({"session_id": request["session_id"]}).revision == 0


def test_failure_preserves_words_without_fake_reply(tmp_path):
    service, connection, request = setup(tmp_path)
    connection.fail = True
    with pytest.raises(BackendError):
        service.send(request)
    saved = service.read_session({"session_id": request["session_id"]})
    assert saved.revision == 1 and len(saved.messages) == 1
    assert not service.status()["inference_passed"]
    assert service._ready().read_profile().revision == 0
    connection.fail = False
    result = service.send({**request, "expected_revision": 1})
    assert result["revision"] == 2 and len(result["messages"]) == 2


def test_vault_cannot_adopt_other_or_cloud_folder(tmp_path):
    service, connection, _ = setup(tmp_path)
    root = service.vault.root
    connection.identity = "synthetic-b"
    with pytest.raises(CompanionError, match="vault_account_mismatch"):
        service.initialize({"confirmed": True, "path": str(root)})
    with pytest.raises(WorkProfileError):
        service.initialize({"confirmed": True, "path": str(tmp_path / "OneDrive" / "private")})
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "existing.txt").write_text("synthetic unrelated data")
    with pytest.raises(CompanionError, match="existing_vault"):
        service.initialize({"confirmed": True, "path": str(occupied)})


def test_bridge_enforces_origin_secret_host_and_input(tmp_path):
    service, _, _ = setup(tmp_path)
    with TestClient(
        create_companion_app(service, pairing_token="synthetic-test-capability"),
        base_url="http://127.0.0.1:8911",
    ) as client:
        payload = {"operation": "status", "arguments": {}}
        headers = {"Origin": SITE_ORIGIN, "Authorization": "Bearer synthetic-test-capability"}
        assert client.post("/v1", json=payload).status_code == 403
        assert (
            client.post(
                "/v1", json=payload, headers={**headers, "Origin": "https://untrusted.invalid"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/v1", json=payload, headers={**headers, "Host": "attacker.invalid"}
            ).status_code
            == 403
        )
        ok = client.post("/v1", json=payload, headers=headers)
        assert ok.status_code == 200 and ok.headers["access-control-allow-origin"] == SITE_ORIGIN
        assert ok.headers["cache-control"] == "no-store"
        assert client.get("/", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
        assert (
            client.get(
                "/",
                headers={
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-User": "?1",
                },
            ).status_code
            == 200
        )
        assert (
            client.get(
                "/",
                headers={
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "iframe",
                    "Sec-Fetch-User": "?1",
                },
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/v1",
                json={"operation": "read-file", "arguments": {"path": "private"}},
                headers=headers,
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/v1", content="x" * 64001, headers={**headers, "Content-Type": "application/json"}
            ).status_code
            == 413
        )


def test_private_profile_not_implicitly_in_inference(tmp_path):
    service, connection, request = setup(tmp_path)
    service.apply_profile(
        {
            "expected_revision": 0,
            "confirmed": True,
            "changes": [
                {
                    "action": "upsert",
                    "claim": {
                        "topic": "values",
                        "text": "SYNTHETIC_PRIVATE_MARKER",
                        "source": {"source_type": "self_report", "reference": "synthetic"},
                        "confirmation": "confirmed",
                        "uncertainty": "Unverified self report",
                    },
                }
            ],
        }
    )
    service.send(request)
    assert "SYNTHETIC_PRIVATE_MARKER" not in str(connection.requests)
    service.send(
        {
            **request,
            "expected_revision": 2,
            "text": "Use my confirmed preferences this time.",
            "include_profile": True,
        }
    )
    assert "SYNTHETIC_PRIVATE_MARKER" in str(connection.requests)


def test_vault_uses_guarded_canonical_root_after_windows_redirection(tmp_path, monkeypatch):
    import anti_dating_scam.services.web_companion as module

    original = module.WorkProfileService
    selected = tmp_path / "selected-spelling"
    canonical = tmp_path / "canonical-storage"
    service = WebCompanion(tmp_path / "state", Connection())

    def redirected(root):
        return original(canonical if root == selected else root)

    monkeypatch.setattr(module, "WorkProfileService", redirected)
    status = service.initialize({"confirmed": True, "path": str(selected)})
    assert status["vault_ready"] and Path(status["vault_path"]) == canonical.resolve()
    assert (canonical / "web-owner.json").is_file()
    assert (canonical / "web-storage-check.json").is_file()
    assert not selected.exists()
    session = service.create_session({"topic": "friendship"})
    assert service.read_session({"session_id": session["id"]}).topic == "friendship"
