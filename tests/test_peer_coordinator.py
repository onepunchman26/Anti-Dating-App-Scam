"""Synthetic adult profiles only; real database transactions, no network AI."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient
from pydantic import ValidationError

from anti_dating_scam.api.rendezvous_app import create_rendezvous_app
from anti_dating_scam.matchmaking.peer_client import invitation_link, parse_invitation
from anti_dating_scam.matchmaking.peer_coordinator import PeerCoordinator, PeerError
from anti_dating_scam.matchmaking.peer_models import (
    Attribute,
    InviteAction,
    InviteCreate,
    MatchingProfile,
    ProfileUpdate,
    PublicUpdate,
    Registration,
)


def profile(alias="Synthetic adult", **changes):
    data = dict(
        alias=alias,
        age=30,
        adult_confirmed=True,
        city="Toronto",
        areas=["Toronto"],
        process_matching=True,
        discoverable=True,
        attributes={
            "intention": Attribute(values=["long_term"], disclose=True),
            "availability": Attribute(values=["weekends"], disclose=True),
            "smoking": Attribute(values=["no"], disclose=False),
        },
    )
    return MatchingProfile(**(data | changes))


@pytest.fixture
def node(tmp_path):
    return PeerCoordinator(tmp_path / "node", key=AESGCM.generate_key(bit_length=256))


def member(node, name, **changes):
    result = node.register(Registration(alias=name, age=30, adult_confirmed=True))
    node.update_profile(
        result["token"],
        ProfileUpdate(expected_version=0, profile=profile(name, **changes), approved=True),
    )
    return result


def invitation(node, a, b):
    invite = node.create_invitation(a["token"], InviteCreate(request_id=uuid4().hex))["invitation"]
    node.act(b["token"], InviteAction(invitation=invite, action="claim"))
    versions = node.preview_pair(a["token"], invite)["versions"]
    for person in (a, b):
        node.act(
            person["token"],
            InviteAction(
                invitation=invite, action="approve", expected_versions=versions, allow_cloud_ai=True
            ),
        )
    return invite


@pytest.mark.parametrize("age", [0, 17, True, 121])
def test_adult_registration_and_matching_gates(age):
    with pytest.raises(ValidationError):
        Registration(alias="Synthetic", age=age, adult_confirmed=True)
    with pytest.raises(ValidationError):
        profile(age=age)


def test_approval_must_be_explicit_boolean():
    with pytest.raises(ValidationError):
        Registration(alias="Synthetic", age=30, adult_confirmed=1)
    with pytest.raises(ValidationError):
        ProfileUpdate(expected_version=0, profile=profile(), approved=1)


def test_browser_boundary_and_exact_control_confirmation(tmp_path):
    app = create_rendezvous_app(peer_directory=tmp_path / "node", peer_key=AESGCM.generate_key(256))
    with TestClient(app, base_url="http://127.0.0.1") as client:
        data = {"alias": "Synthetic", "age": 30, "adult_confirmed": True}
        assert (
            client.post(
                "/peer/register", json=data, headers={"Origin": "https://foreign.invalid"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/peer/register", json=data, headers={"Host": "foreign.invalid"}
            ).status_code
            == 403
        )
        identity = client.post("/peer/register", json=data).json()["data"]
        headers = {"Authorization": "Bearer " + identity["token"]}
        assert (
            client.post(
                "/peer/control", headers=headers, json={"action": "delete", "confirmed": 1}
            ).status_code
            == 422
        )
        assert client.get("/peer/me", headers=headers).status_code == 200


def test_public_alias_does_not_silently_follow_matching_changes(node):
    a = member(node, "Approved public alias")
    node.public_update(
        a["token"],
        PublicUpdate(expected_version=0, text="Approved text", publish=True, approved=True),
    )
    node.update_profile(
        a["token"],
        ProfileUpdate(expected_version=1, profile=profile("Private new alias"), approved=True),
    )
    assert node.public_read(a["member_id"])["alias"] == "Approved public alias"


def test_encrypted_persistence_and_auth(tmp_path):
    key = AESGCM.generate_key(bit_length=256)
    n = PeerCoordinator(tmp_path / "node", key=key)
    a = member(n, "Synthetic secret alias")
    raw = (tmp_path / "node/approved-matching.sqlite3").read_bytes()
    assert b"Synthetic secret alias" not in raw and a["token"].encode() not in raw
    restored = PeerCoordinator(tmp_path / "node", key=key)
    assert restored.me(a["token"])["version"] == 1
    with pytest.raises(PeerError, match="unauthorized"):
        restored.me("x" * 43)


def test_reciprocal_city_age_and_hard_requirements(node):
    a = member(node, "Synthetic A")
    b = member(node, "Synthetic B")
    assert len(node.discover(a["token"])["candidates"]) == 1
    node.update_profile(
        b["token"],
        ProfileUpdate(
            expected_version=1, approved=True, profile=profile("Synthetic B", areas=["Ottawa"])
        ),
    )
    assert not node.discover(a["token"])["candidates"]
    node.update_profile(
        b["token"],
        ProfileUpdate(
            expected_version=2, approved=True, profile=profile("Synthetic B", age_min=35)
        ),
    )
    assert not node.discover(a["token"])["candidates"]
    node.update_profile(
        b["token"],
        ProfileUpdate(
            expected_version=3,
            approved=True,
            profile=profile("Synthetic B", required={"intention": ["casual"]}),
        ),
    )
    assert not node.discover(a["token"])["candidates"]


def test_hidden_attributes_never_enter_explanations_or_ai(node):
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    row = node.discover(a["token"])["candidates"][0]
    assert row["city"] is None and "smoking" not in row["attributes"]
    identity = invitation(node, a, b)
    prepared = node.prepare_comparison(a["token"], identity)
    assert "smoking" not in str(prepared) and "Toronto" not in str(prepared)
    assert "Synthetic" not in str(prepared) and a["member_id"] not in str(prepared)


def test_forwarded_claim_requires_sender_confirmation_and_single_recipient(node):
    a, b, c = (member(node, "Synthetic " + x) for x in "ABC")
    identity = node.create_invitation(a["token"], InviteCreate(request_id=uuid4().hex))[
        "invitation"
    ]
    node.act(b["token"], InviteAction(invitation=identity, action="claim"))
    with pytest.raises(PeerError, match="already_used"):
        node.act(c["token"], InviteAction(invitation=identity, action="claim"))
    with pytest.raises(PeerError, match="consent_required"):
        node.prepare_comparison(b["token"], identity)
    with pytest.raises(PeerError, match="stale"):
        node.act(
            a["token"], InviteAction(invitation=identity, action="approve", allow_cloud_ai=True)
        )
    assert len(node.invitations(c["token"])["invitations"]) == 0


def test_targeted_invitation_cannot_be_forwarded(node):
    a, b, c = (member(node, "Synthetic " + x) for x in "ABC")
    identity = node.create_invitation(
        a["token"], InviteCreate(request_id=uuid4().hex, intended_member=b["member_id"])
    )["invitation"]
    with pytest.raises(PeerError, match="wrong_recipient"):
        node.act(c["token"], InviteAction(invitation=identity, action="claim"))


@pytest.mark.parametrize("action", ["revoke", "decline"])
def test_revoke_and_decline_disable_comparison(node, action):
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    identity = invitation(node, a, b)
    node.act(b["token"], InviteAction(invitation=identity, action=action))
    with pytest.raises(PeerError):
        node.prepare_comparison(a["token"], identity)
    if action == "decline":
        assert not node.discover(a["token"])["candidates"]


def test_expired_link(node):
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    identity = invitation(node, a, b)
    now = node.clock()
    node.clock = lambda: now + 7 * 86400 + 1
    with pytest.raises(PeerError):
        node.prepare_comparison(a["token"], identity)
    assert node.invitations(a["token"])["invitations"][0]["status"] == "expired"


def test_withdraw_correction_and_block_invalidate_both_sides(node):
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    identity = invitation(node, a, b)
    node.update_profile(
        b["token"], ProfileUpdate(expected_version=1, profile=profile("Synthetic B"), approved=True)
    )
    with pytest.raises(PeerError, match="consent_required"):
        node.prepare_comparison(a["token"], identity)
    node.control(b["token"], "block", a["member_id"])
    assert not node.discover(a["token"])["candidates"]
    node.control(a["token"], "withdraw")
    with pytest.raises(PeerError, match="consent_required"):
        node.discover(a["token"])


def test_concurrent_claims_and_profile_revisions(node):
    a, b, c = (member(node, "Synthetic " + x) for x in "ABC")
    identity = node.create_invitation(a["token"], InviteCreate(request_id=uuid4().hex))[
        "invitation"
    ]

    def claim(member):
        try:
            node.act(member["token"], InviteAction(invitation=identity, action="claim"))
            return True
        except PeerError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(claim, [b, c])) == 1

    def update(_):
        try:
            node.update_profile(
                a["token"],
                ProfileUpdate(expected_version=1, approved=True, profile=profile("Synthetic A")),
            )
            return True
        except PeerError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(update, range(2))) == 1


def test_retry_invitation_is_idempotent_and_empty_pool_is_honest(node):
    a = member(node, "Synthetic A")
    assert node.discover(a["token"])["candidates"] == []
    request = InviteCreate(request_id=uuid4().hex)
    assert node.create_invitation(a["token"], request) == node.create_invitation(
        a["token"], request
    )


def test_low_information_unranked_and_priorities_change_order(node):
    a = member(node, "Synthetic A")
    b = member(
        node,
        "Synthetic B",
        attributes={"intention": Attribute(values=["long_term"], disclose=True)},
    )
    assert node.discover(a["token"])["candidates"][0]["order"] is None
    assert node.discover(a["token"])["candidates"][0]["missing"] == ["availability"]
    assert b["member_id"]


def test_worker_due_only_and_no_duplicate_notice(node):
    a = member(node, "Synthetic A", automatic_minutes=15, notifications=True)
    member(node, "Synthetic B")
    assert node.run_due() == 0
    now = node.clock()
    node.clock = lambda: now + 901
    assert node.run_due() == 1 and node.me(a["token"])["notice"]
    assert node.run_due() == 0
    node.discover(a["token"])
    node.clock = lambda: now + 1802
    assert node.run_due() == 1 and not node.me(a["token"])["notice"]


def test_links_do_not_fetch_unrelated_urls():
    origin = "http://127.0.0.1:8766"
    link = invitation_link(origin, "a" * 43)
    assert parse_invitation(link, origin) == "a" * 43
    for value in [
        "https://evil.invalid/invite#" + "a" * 43,
        link + "?token=bad",
        origin + "/private#" + "a" * 43,
        "file:///private",
    ]:
        with pytest.raises(ValueError):
            parse_invitation(value, origin)


def test_publication_is_separate_and_delete_revokes_everything(node):
    a, b = member(node, "Synthetic A"), member(node, "Synthetic B")
    identity = invitation(node, a, b)
    with pytest.raises(PeerError):
        node.public_read(a["member_id"])
    node.public_update(
        a["token"],
        PublicUpdate(
            expected_version=0, text="Approved synthetic intro", publish=True, approved=True
        ),
    )
    assert node.public_read(a["member_id"])["text"] == "Approved synthetic intro"
    node.control(a["token"], "delete")
    with pytest.raises(PeerError):
        node.public_read(a["member_id"])
    with pytest.raises(PeerError):
        node.prepare_comparison(b["token"], identity)


def test_real_api_boundaries_landing_and_private_validation(tmp_path):
    app = create_rendezvous_app(peer_directory=tmp_path / "node", peer_key=AESGCM.generate_key(256))
    with TestClient(app, base_url="http://127.0.0.1") as client:
        response = client.post(
            "/peer/register", json={"alias": "PRIVATE SENTINEL", "age": 17, "adult_confirmed": True}
        )
        assert response.status_code == 422 and "PRIVATE SENTINEL" not in response.text
        assert client.get("/invite").status_code == 200
        assert client.get("/matchmaking/nearby/anyone").status_code == 404
        assert client.get("/peer/me?token=secret").status_code == 400
        assert client.post("/peer/profile", content=b"x" * 17000).status_code == 413
        assert client.get("/peer/me").headers["cache-control"] == "no-store"
