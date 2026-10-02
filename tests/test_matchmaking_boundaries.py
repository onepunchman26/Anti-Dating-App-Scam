"""Synthetic negative cases for the local matching experiment's protocol boundary."""

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.api.rendezvous_app import create_rendezvous_app
from anti_dating_scam.matchmaking.beacon import BeaconError, create_beacon, parse_beacon
from anti_dating_scam.matchmaking.rendezvous import MatchmakingError, RendezvousService
from anti_dating_scam.reports.canonical_json import canonical_json, sha256_text
from anti_dating_scam.services.consent_manager import ConsentRequiredError


def registration(**overrides):
    data = {
        "pseudonym": "synthetic", "geohash": "wtw3", "contact": "synthetic@example.test",
        "consent_confirmed": True, "age": 30,
    }
    return data | overrides


def beacon_payload(**overrides):
    return {
        "version": 1, "pseudonym": "synthetic", "bucket": "wtw3",
        "card_fingerprint": "a" * 64, "created_at": "2026-01-01T00:00:00+00:00", "age": 30,
    } | overrides


def armor(payload):
    if isinstance(payload, dict):
        payload = payload | {"checksum": sha256_text(canonical_json(payload))}
    data = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"-----BEGIN AI-SLOWMATCH BEACON-----\n{data}\n-----END AI-SLOWMATCH BEACON-----"


@pytest.mark.parametrize("age", [None, False, True, "30", 30.0, 17, 121, [], {}])
def test_adult_eligibility_cannot_be_omitted_or_coerced(age):
    service = RendezvousService()
    with pytest.raises(MatchmakingError, match="adult"):
        service.register(**registration(age=age))
    assert not service._registry
    client = TestClient(create_rendezvous_app(web_dir=None))
    assert client.post("/matchmaking/register", json=registration(age=age)).status_code == 422
    payload = registration()
    del payload["age"]
    assert client.post("/matchmaking/register", json=payload).status_code == 422


@pytest.mark.parametrize("consent", [False, 1, "yes", "false", [], None])
def test_domain_consent_requires_exact_true(consent):
    with pytest.raises(ConsentRequiredError):
        RendezvousService().register(**registration(consent_confirmed=consent))
    with pytest.raises(BeaconError, match="consent"):
        create_beacon(
            pseudonym="synthetic", bucket="wtw3", card_fingerprint="a" * 64,
            age=30, consent_confirmed=consent,
        )


@pytest.mark.parametrize("pseudonym", ["a/b", "a\\b", "a?b", "a#b", "a%b", ".", ".."])
def test_registration_rejects_pseudonyms_that_cannot_roundtrip_through_routes(pseudonym):
    with pytest.raises(MatchmakingError, match="pseudonym"):
        RendezvousService().register(**registration(pseudonym=pseudonym))


@pytest.mark.parametrize("patch", [
    {"age": None}, {"age": 17}, {"age": "30"}, {"age": True},
    {"seeking_age_min": 40, "seeking_age_max": 25}, {"seeking_age_min": "18"},
    {"version": True}, {"version": 2}, {"pseudonym": []}, {"pseudonym": "<script>"},
    {"pseudonym": "x" * 41}, {"bucket": "wtw3ab"}, {"bucket": "w"},
    {"bucket": 123}, {"card_fingerprint": "not-a-hash"}, {"contact_hint": "x" * 121},
    {"created_at": "yesterday"}, {"created_at": "2026-01-01"}, {"unknown": "secret"},
])
def test_even_correctly_checksummed_beacons_require_valid_fields(patch):
    with pytest.raises(BeaconError):
        parse_beacon(armor(beacon_payload(**patch)))


@pytest.mark.parametrize("payload", [None, [], "text", 123, {}])
def test_beacon_parser_rejects_non_objects_and_missing_fields(payload):
    with pytest.raises(BeaconError):
        parse_beacon(armor(payload))


def test_beacon_limits_and_duplicate_keys():
    with pytest.raises(BeaconError, match="size"):
        parse_beacon("a" * 8193)
    text = create_beacon(
        pseudonym="synthetic", bucket="wtw3", card_fingerprint="a" * 64,
        age=30, consent_confirmed=True,
    )
    with pytest.raises(BeaconError, match="exactly one"):
        parse_beacon(text + text)
    duplicate = base64.b64encode(b'{"age":30,"age":17}').decode()
    with pytest.raises(BeaconError, match="duplicate"):
        parse_beacon(
            f"-----BEGIN AI-SLOWMATCH BEACON-----\n{duplicate}\n"
            "-----END AI-SLOWMATCH BEACON-----"
        )


@pytest.mark.parametrize("other", [
    {"age": 50}, {"seeking_age_min": 40}, {"gender": "man", "seeking_genders": ["man"]},
    {"geohash": "u4pr"},
])
def test_direct_introduction_cannot_bypass_discovery_gates(other):
    service = RendezvousService()
    service.register(**registration(
        pseudonym="alpha", gender="woman", seeking_age_max=40, seeking_genders=["man"]
    ))
    service.register(**registration(pseudonym="beta", gender="man", **{
        key: value for key, value in other.items() if key != "gender"
    }))
    for name in ("alpha", "beta"):
        service.attest_card(name, fingerprint="a" * 64)
    with pytest.raises(MatchmakingError):
        service.request_introduction("alpha", "beta")


def test_concurrent_duplicate_registrations_issue_only_one_token():
    service = RendezvousService()

    def attempt(_):
        try:
            return service.register(**registration()).token
        except MatchmakingError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(attempt, range(20)))
    assert len([token for token in tokens if token]) == 1


def test_authenticated_operation_cannot_transfer_to_a_reused_pseudonym():
    service = RendezvousService()
    original = service.register(**registration())
    attempted = Event()

    def recreate():
        attempted.set()
        service.unregister("synthetic")
        return service.register(**registration(contact="replacement@example.test"))

    with ThreadPoolExecutor(max_workers=1) as pool:
        with service.authenticated_operation("synthetic", original.token):
            pending = pool.submit(recreate)
            assert attempted.wait(timeout=2)
            assert not pending.done()
            assert service.authenticate("synthetic", original.token) is original
        replacement = pending.result(timeout=2)
    assert replacement.token != original.token
    with pytest.raises(MatchmakingError, match="token"):
        service.authenticate("synthetic", original.token)


def test_header_auth_fingerprint_only_private_errors_and_state_isolation():
    client = TestClient(create_rendezvous_app(web_dir=None))
    token = client.post("/matchmaking/register", json=registration()).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    body = {"pseudonym": "synthetic", "fingerprint": "a" * 64}
    response = client.post("/matchmaking/attest", json=body, headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/matchmaking/nearby/synthetic", headers=headers).status_code == 200
    assert client.get(f"/matchmaking/nearby/synthetic?token={token}").status_code == 400
    assert client.post(
        "/matchmaking/attest", json=body | {"token": "different"}, headers=headers
    ).status_code == 400
    secret_card = {"private_note": "synthetic-private-marker"}
    invalid = client.post(
        "/matchmaking/attest", json=body | {"card": secret_card}, headers=headers
    )
    assert invalid.status_code == 422
    assert "synthetic-private-marker" not in invalid.text
    assert token not in invalid.text
    separate = TestClient(create_rendezvous_app(web_dir=None))
    assert separate.get("/matchmaking/nearby/synthetic", headers=headers).status_code == 400
    assert client.delete("/matchmaking/register/synthetic", headers=headers).status_code == 200
    assert client.get("/matchmaking/nearby/synthetic", headers=headers).status_code == 400


def test_request_size_bound_and_authorization_cors():
    client = TestClient(create_rendezvous_app(web_dir=None))
    oversized = client.post("/matchmaking/register", content=b"x" * 16385)
    assert oversized.status_code == 413
    preflight = client.options("/matchmaking/attest", headers={
        "Origin": "https://synthetic.example.test",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    })
    assert preflight.status_code == 200
