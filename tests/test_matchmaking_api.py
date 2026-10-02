import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.api import routes_matchmaking
from anti_dating_scam.main import create_app
from anti_dating_scam.matchmaking.attestation import card_fingerprint
from anti_dating_scam.matchmaking.geo import encode_geohash

CARD = {"schema_version": "0.1", "tier2_summary": {"values": ["honesty"]}}
GH = encode_geohash(49.2827, -123.1207)


@pytest.fixture()
def client() -> TestClient:
    routes_matchmaking.reset_service()
    return TestClient(create_app())


def _register(client: TestClient, pseudonym: str, contact: str, **extra) -> str:
    """Register and return the per-registration access token."""
    payload = {
        "pseudonym": pseudonym,
        "geohash": GH,
        "contact": contact,
        "consent_confirmed": True,
        "age": 30,
        "seeking_age_min": 25,
        "seeking_age_max": 40,
    }
    payload.update(extra)
    response = client.post("/matchmaking/register", json=payload)
    assert response.status_code == 200
    return response.json()["token"]


def test_register_without_consent_is_403(client: TestClient) -> None:
    response = client.post(
        "/matchmaking/register",
        json={"pseudonym": "x", "geohash": GH, "contact": "x@example.test", "age": 30},
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "consent_required"


def test_full_flow_over_http(client: TestClient) -> None:
    tokens = {
        "alpha": _register(client, "alpha", "alpha@example.test"),
        "beta": _register(client, "beta", "beta@example.test"),
    }

    for name in ("alpha", "beta"):
        response = client.post(
            "/matchmaking/attest",
            json={"pseudonym": name, "token": tokens[name], "fingerprint": card_fingerprint(CARD)},
        )
        assert response.status_code == 200
        assert "disclaimer" in response.json()

    nearby = client.get(
        "/matchmaking/nearby/alpha", headers={"Authorization": f"Bearer {tokens['alpha']}"}
    ).json()["candidates"]
    assert [candidate["pseudonym"] for candidate in nearby] == ["beta"]
    assert "contact" not in nearby[0]

    introduction = client.post(
        "/matchmaking/introduce",
        json={"initiator": "alpha", "token": tokens["alpha"], "recipient": "beta"},
    ).json()
    assert introduction["status"] == "pending"
    intro_id = introduction["introduction_id"]

    # Contact stays hidden until beta accepts.
    packet = client.get(
        f"/matchmaking/match/{intro_id}/alpha",
        headers={"Authorization": f"Bearer {tokens['alpha']}"},
    )
    assert packet.status_code == 400

    accepted = client.post(
        "/matchmaking/respond",
        json={
            "pseudonym": "beta",
            "token": tokens["beta"],
            "introduction_id": intro_id,
            "accept": True,
        },
    ).json()
    assert accepted["status"] == "matched"

    packet = client.get(
        f"/matchmaking/match/{intro_id}/alpha",
        headers={"Authorization": f"Bearer {tokens['alpha']}"},
    ).json()
    assert packet["counterpart_contact"] == "beta@example.test"

    verified = client.post(
        "/matchmaking/verify-card",
        json={
            "pseudonym": "alpha",
            "token": tokens["alpha"],
            "introduction_id": intro_id,
            "fingerprint": card_fingerprint(CARD),
        },
    ).json()
    assert verified["valid"] is True

    tampered = client.post(
        "/matchmaking/verify-card",
        json={
            "pseudonym": "alpha",
            "token": tokens["alpha"],
            "introduction_id": intro_id,
            "fingerprint": card_fingerprint({**CARD, "tier2_summary": {"values": ["changed"]}}),
        },
    ).json()
    assert tampered["valid"] is False


def test_endpoints_reject_missing_or_wrong_token(client: TestClient) -> None:
    token = _register(client, "alpha", "alpha@example.test")

    # No token / wrong token → 400 with an access-token message, no data out.
    assert client.get("/matchmaking/nearby/alpha").status_code == 400
    assert client.get("/matchmaking/introductions/alpha").status_code == 400
    assert client.delete("/matchmaking/register/alpha?token=wrong").status_code == 400
    attest = client.post(
        "/matchmaking/attest", json={"pseudonym": "alpha", "fingerprint": card_fingerprint(CARD)}
    )
    assert attest.status_code == 400
    assert "token" in attest.json()["detail"]

    # The right token works.
    ok = client.post(
        "/matchmaking/attest",
        json={"pseudonym": "alpha", "token": token, "fingerprint": card_fingerprint(CARD)},
    )
    assert ok.status_code == 200


def test_attest_by_fingerprint_over_http(client: TestClient) -> None:
    tokens = {
        "alpha": _register(client, "alpha", "alpha@example.test"),
        "beta": _register(client, "beta", "beta@example.test"),
    }
    # Both clients hash cards locally; no card content is sent to the node.
    fingerprint = card_fingerprint(CARD)
    response = client.post(
        "/matchmaking/attest",
        json={"pseudonym": "alpha", "token": tokens["alpha"], "fingerprint": fingerprint},
    )
    assert response.status_code == 200
    assert response.json()["fingerprint"] == fingerprint

    client.post(
        "/matchmaking/attest",
        json={"pseudonym": "beta", "token": tokens["beta"], "fingerprint": card_fingerprint(CARD)},
    )
    intro = client.post(
        "/matchmaking/introduce",
        json={"initiator": "beta", "token": tokens["beta"], "recipient": "alpha"},
    ).json()
    client.post(
        "/matchmaking/respond",
        json={
            "pseudonym": "alpha",
            "token": tokens["alpha"],
            "introduction_id": intro["introduction_id"],
            "accept": True,
        },
    )
    # beta verifies the card alpha "sent" against alpha's fingerprint-attested lock.
    verified = client.post(
        "/matchmaking/verify-card",
        json={
            "pseudonym": "beta",
            "token": tokens["beta"],
            "introduction_id": intro["introduction_id"],
            "fingerprint": card_fingerprint(CARD),
        },
    ).json()
    assert verified["valid"] is True


def test_unregister_deletes_over_http(client: TestClient) -> None:
    token = _register(client, "alpha", "alpha@example.test")
    assert (
        client.delete(
            "/matchmaking/register/alpha", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 200
    )
    assert (
        client.delete(
            "/matchmaking/register/alpha", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 400
    )


def test_register_with_orientation_and_inbox_flow(client: TestClient) -> None:
    tokens = {}
    for pseudonym, gender, seeking in [
        ("ava", "woman", ["man"]),
        ("ben", "man", ["woman"]),
        ("cam", "man", ["man"]),
    ]:
        tokens[pseudonym] = _register(
            client,
            pseudonym,
            f"{pseudonym}@example.test",
            gender=gender,
            seeking_genders=seeking,
        )
        attested = client.post(
            "/matchmaking/attest",
            json={
                "pseudonym": pseudonym,
                "token": tokens[pseudonym],
                "fingerprint": card_fingerprint(CARD),
            },
        )
        assert attested.status_code == 200

    nearby = client.get(
        "/matchmaking/nearby/ava", headers={"Authorization": f"Bearer {tokens['ava']}"}
    ).json()["candidates"]
    assert [candidate["pseudonym"] for candidate in nearby] == ["ben"]

    intro = client.post(
        "/matchmaking/introduce",
        json={"initiator": "ava", "token": tokens["ava"], "recipient": "ben"},
    ).json()

    inbox = client.get(
        "/matchmaking/introductions/ben", headers={"Authorization": f"Bearer {tokens['ben']}"}
    ).json()["introductions"]
    assert len(inbox) == 1
    assert inbox[0]["direction"] == "received"
    assert inbox[0]["counterpart_pseudonym"] == "ava"
    assert inbox[0]["awaiting_you"] is True
    assert inbox[0]["introduction_id"] == intro["introduction_id"]

    assert client.get("/matchmaking/introductions/nobody?token=x").status_code == 400


def test_invalid_gender_is_rejected_over_http(client: TestClient) -> None:
    response = client.post(
        "/matchmaking/register",
        json={
            "pseudonym": "x",
            "geohash": GH,
            "contact": "x@example.test",
            "consent_confirmed": True,
            "gender": "unknown-value",
            "age": 30,
        },
    )
    assert response.status_code == 400


def test_rendezvous_app_serves_ui_and_api() -> None:
    from anti_dating_scam.api.rendezvous_app import DEFAULT_WEB_DIR, create_rendezvous_app

    routes_matchmaking.reset_service()
    app_client = TestClient(create_rendezvous_app(web_dir=DEFAULT_WEB_DIR))

    page = app_client.get("/")
    assert page.status_code == 200
    assert "AI-SlowMatch" in page.text

    # Consent handler is wired in the lean app too (403, not 500).
    response = app_client.post(
        "/matchmaking/register",
        json={"pseudonym": "x", "geohash": GH, "contact": "x@example.test", "age": 30},
    )
    assert response.status_code == 403

    # API-only mode works without the static mount.
    routes_matchmaking.reset_service()
    api_only = TestClient(create_rendezvous_app(web_dir=None))
    assert api_only.get("/").status_code == 404
