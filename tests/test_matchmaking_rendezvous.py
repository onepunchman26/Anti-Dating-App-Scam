import pytest

from anti_dating_scam.matchmaking.attestation import AttestationService, card_fingerprint
from anti_dating_scam.matchmaking.geo import encode_geohash, same_bucket
from anti_dating_scam.matchmaking.rendezvous import MatchmakingError, RendezvousService
from anti_dating_scam.services.consent_manager import ConsentRequiredError

# Synthetic cards only (no real user data in tests).
CARD_A = {"schema_version": "0.1", "tier2_summary": {"values": ["honesty", "autonomy"]}}
CARD_B = {"schema_version": "0.1", "tier2_summary": {"values": ["care", "stability"]}}

# Same metro bucket (precision 4) vs. a far-away city.
GH_CITY_1 = encode_geohash(49.2827, -123.1207)  # synthetic city A
GH_CITY_1B = encode_geohash(49.2830, -123.1300)  # a few hundred meters away
GH_CITY_2 = encode_geohash(31.2304, 121.4737)  # synthetic city B


def _service_with_pair() -> RendezvousService:
    service = RendezvousService()
    service.register(
        pseudonym="alpha", geohash=GH_CITY_1, contact="alpha@example.test",
        consent_confirmed=True, age=30, seeking_age_min=25, seeking_age_max=40,
    )
    service.register(
        pseudonym="beta", geohash=GH_CITY_1B, contact="beta@example.test",
        consent_confirmed=True, age=32, seeking_age_min=25, seeking_age_max=40,
    )
    return service


def test_geohash_matches_known_vector() -> None:
    assert encode_geohash(57.64911, 10.40744, precision=11) == "u4pruydqqvj"


def test_same_bucket_for_nearby_points_only() -> None:
    assert same_bucket(GH_CITY_1, GH_CITY_1B) is True
    assert same_bucket(GH_CITY_1, GH_CITY_2) is False


def test_attestation_verifies_and_detects_token_tamper() -> None:
    attestations = AttestationService()
    attestation = attestations.attest("alpha", card_fingerprint(CARD_A), version=1)
    assert attestations.verify(attestation) is True

    from dataclasses import replace

    forged = replace(attestation, fingerprint=card_fingerprint(CARD_B))
    assert attestations.verify(forged) is False


def test_register_requires_consent_and_valid_geohash() -> None:
    service = RendezvousService()
    with pytest.raises(ConsentRequiredError):
        service.register(
            pseudonym="x", geohash=GH_CITY_1, contact="x@example.test", consent_confirmed=False
        )
    with pytest.raises(MatchmakingError):
        service.register(
            pseudonym="x", geohash="49.28,-123.12",  # raw coordinates are rejected
            contact="x@example.test", consent_confirmed=True,
        )


def test_nearby_requires_own_attested_card_and_hides_contact() -> None:
    service = _service_with_pair()
    with pytest.raises(MatchmakingError):
        service.nearby("alpha")  # no skin in the game yet

    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    candidates = service.nearby("alpha")

    assert [candidate["pseudonym"] for candidate in candidates] == ["beta"]
    assert "contact" not in candidates[0]
    assert candidates[0]["attestation_summary"]["version_count"] == 1


def test_nearby_filters_by_bucket_and_mutual_age_gate() -> None:
    service = _service_with_pair()
    service.register(
        pseudonym="faraway", geohash=GH_CITY_2, contact="far@example.test",
        consent_confirmed=True, age=31, seeking_age_min=25, seeking_age_max=40,
    )
    service.register(
        pseudonym="gate-fails", geohash=GH_CITY_1, contact="gate@example.test",
        consent_confirmed=True, age=31, seeking_age_min=50, seeking_age_max=60,
    )
    for name, card in [("alpha", CARD_A), ("beta", CARD_B),
                       ("faraway", CARD_B), ("gate-fails", CARD_B)]:
        service.attest_card(name, card)

    names = [candidate["pseudonym"] for candidate in service.nearby("alpha")]
    assert names == ["beta"]  # faraway: wrong bucket; gate-fails: mutual gate fails


def test_full_double_blind_match_flow_and_card_verification() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)

    introduction = service.request_introduction("alpha", "beta")
    assert introduction.status == "pending"
    with pytest.raises(MatchmakingError):
        service.match_packet("alpha", introduction.introduction_id)  # not matched yet

    service.respond("beta", introduction.introduction_id, accept=True)
    packet = service.match_packet("alpha", introduction.introduction_id)
    assert packet["counterpart_contact"] == "beta@example.test"
    assert packet["locked_fingerprint"] == card_fingerprint(CARD_B)
    assert "disclaimer" in packet

    # Received card matches the locked fingerprint.
    result = service.verify_card_for_match("alpha", introduction.introduction_id, CARD_B)
    assert result["valid"] is True

    # A card edited after the match is detected.
    edited = {**CARD_B, "tier2_summary": {"values": ["a perfect persona"]}}
    result = service.verify_card_for_match("alpha", introduction.introduction_id, edited)
    assert result["valid"] is False


def test_post_match_reattestation_does_not_move_locked_fingerprint() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")
    service.respond("beta", introduction.introduction_id, accept=True)

    # beta rewrites their card after matching; the lock stays on the old version.
    edited = {**CARD_B, "tier2_summary": {"values": ["rewritten"]}}
    service.attest_card("beta", edited)
    packet = service.match_packet("alpha", introduction.introduction_id)
    assert packet["locked_fingerprint"] == card_fingerprint(CARD_B)
    assert packet["attestation_summary"]["version_count"] == 2  # churn visible as fact


def test_nearby_filters_by_mutual_gender_gate() -> None:
    service = RendezvousService()
    service.register(
        pseudonym="ava", geohash=GH_CITY_1, contact="ava@example.test",
        consent_confirmed=True, age=30, gender="woman", seeking_genders=["man"],
    )
    service.register(  # mutual: seeks women, is a man
        pseudonym="ben", geohash=GH_CITY_1, contact="ben@example.test",
        consent_confirmed=True, age=30, gender="man", seeking_genders=["woman"],
    )
    service.register(  # one-directional: ava seeks men, but cam seeks men too
        pseudonym="cam", geohash=GH_CITY_1, contact="cam@example.test",
        consent_confirmed=True, age=30, gender="man", seeking_genders=["man"],
    )
    service.register(  # no gender stated: passes only seekers with no filter
        pseudonym="drew", geohash=GH_CITY_1, contact="drew@example.test",
        consent_confirmed=True, age=30, gender=None, seeking_genders=None,
    )
    for name in ("ava", "ben", "cam", "drew"):
        service.attest_card(name, CARD_A)

    assert [c["pseudonym"] for c in service.nearby("ava")] == ["ben"]
    # drew has no filter, so drew sees everyone whose own filter admits drew —
    # nobody, because drew stated no gender and all others filter by gender.
    assert [c["pseudonym"] for c in service.nearby("drew")] == []
    # cam seeks men: ben matches cam's filter but cam is not sought by ben.
    assert [c["pseudonym"] for c in service.nearby("cam")] == []


def test_gender_normalization_and_validation() -> None:
    service = RendezvousService()
    registration = service.register(
        pseudonym="eve", geohash=GH_CITY_1, contact="eve@example.test",
        consent_confirmed=True, age=30, gender="  Woman ",
        seeking_genders=["woman", "man", "nonbinary"],
    )
    assert registration.gender == "woman"
    assert registration.seeking_genders is None  # seeking-everyone collapses to no filter

    with pytest.raises(MatchmakingError):
        service.register(
            pseudonym="bad", geohash=GH_CITY_1, contact="bad@example.test",
            consent_confirmed=True, age=30, gender="unknown-value",
        )
    with pytest.raises(MatchmakingError):
        service.register(
            pseudonym="bad2", geohash=GH_CITY_1, contact="bad2@example.test",
            consent_confirmed=True, age=30, seeking_genders=["women"],  # plural typo rejected
        )


def test_introduction_inbox_shows_both_directions() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")

    sent = service.introductions_for("alpha")
    assert len(sent) == 1
    assert sent[0]["direction"] == "sent"
    assert sent[0]["counterpart_pseudonym"] == "beta"
    assert sent[0]["awaiting_you"] is False  # initiator already accepted implicitly

    received = service.introductions_for("beta")
    assert received[0]["direction"] == "received"
    assert received[0]["awaiting_you"] is True

    service.respond("beta", introduction.introduction_id, accept=True)
    assert service.introductions_for("beta")[0]["status"] == "matched"
    assert service.introductions_for("beta")[0]["awaiting_you"] is False


def test_declined_pair_cannot_be_reintroduced() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")
    service.respond("beta", introduction.introduction_id, accept=False)

    with pytest.raises(MatchmakingError):
        service.request_introduction("alpha", "beta")


def test_unregister_deletes_registration_and_open_introductions() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")

    service.unregister("beta")
    with pytest.raises(MatchmakingError):
        service.match_packet("alpha", introduction.introduction_id)
    with pytest.raises(MatchmakingError):
        service.nearby("beta")


def test_initiator_decline_is_withdrawal_not_poison() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")

    withdrawn = service.respond("alpha", introduction.introduction_id, accept=False)
    assert withdrawn.status == "withdrawn"
    assert service.introductions_for("beta") == []  # gone from the recipient's inbox too

    # The pair is NOT poisoned: a genuine attempt later still works.
    retry = service.request_introduction("beta", "alpha")
    assert retry.status == "pending"


def test_matched_pair_cannot_get_second_introduction() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")
    service.respond("beta", introduction.introduction_id, accept=True)

    with pytest.raises(MatchmakingError, match="already matched"):
        service.request_introduction("alpha", "beta")


def test_nearby_excludes_declined_and_live_pairs() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)

    introduction = service.request_introduction("alpha", "beta")
    assert service.nearby("alpha") == []  # pending pair lives in the inbox, not nearby

    service.respond("beta", introduction.introduction_id, accept=False)
    assert service.nearby("alpha") == []  # declined pair would be a guaranteed-error button
    assert service.nearby("beta") == []


def test_unregister_purges_declined_pairs() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")
    service.respond("beta", introduction.introduction_id, accept=False)

    service.unregister("beta")
    # A different person later registering the freed pseudonym must not inherit blocks.
    service.register(
        pseudonym="beta", geohash=GH_CITY_1B, contact="new-beta@example.test",
        consent_confirmed=True, age=30,
    )
    service.attest_card("beta", CARD_B)
    assert service.request_introduction("alpha", "beta").status == "pending"


def test_geohash_length_bounds() -> None:
    service = RendezvousService()
    for bad in ("wtw", "wtw3wtw"):  # shorter than precision 4 / coordinate-grade
        with pytest.raises(MatchmakingError, match="geohash"):
            service.register(
                pseudonym="x", geohash=bad, contact="x@example.test", consent_confirmed=True
            )


def test_adults_only_and_clean_text_validation() -> None:
    service = RendezvousService()
    with pytest.raises(MatchmakingError, match="adults-only"):
        service.register(
            pseudonym="kid", geohash=GH_CITY_1, contact="kid@example.test",
            consent_confirmed=True, age=12,
        )
    with pytest.raises(MatchmakingError, match="seeking_age_min"):
        service.register(
            pseudonym="range", geohash=GH_CITY_1, contact="range@example.test",
            consent_confirmed=True, age=30, seeking_age_min=40, seeking_age_max=25,
        )
    with pytest.raises(MatchmakingError, match="pseudonym"):
        service.register(
            pseudonym="<script>x</script>", geohash=GH_CITY_1,
            contact="x@example.test", consent_confirmed=True,
        )


def test_attest_by_fingerprint_matches_card_hash() -> None:
    service = _service_with_pair()
    fingerprint = card_fingerprint(CARD_A)
    attestation = service.attest_card("alpha", fingerprint=fingerprint)
    assert attestation.fingerprint == fingerprint

    with pytest.raises(MatchmakingError, match="exactly one"):
        service.attest_card("alpha")
    with pytest.raises(MatchmakingError, match="exactly one"):
        service.attest_card("alpha", CARD_A, fingerprint=fingerprint)
    with pytest.raises(MatchmakingError, match="64-character"):
        service.attest_card("alpha", fingerprint="nope")


def test_verify_card_requires_matched_state() -> None:
    service = _service_with_pair()
    service.attest_card("alpha", CARD_A)
    service.attest_card("beta", CARD_B)
    introduction = service.request_introduction("alpha", "beta")
    with pytest.raises(MatchmakingError, match="after both sides accept"):
        service.verify_card_for_match("alpha", introduction.introduction_id, CARD_B)


def test_authenticate_rejects_wrong_or_missing_token() -> None:
    service = RendezvousService()
    registration = service.register(
        pseudonym="alpha", geohash=GH_CITY_1, contact="alpha@example.test",
        consent_confirmed=True, age=30,
    )
    assert service.authenticate("alpha", registration.token) is registration
    with pytest.raises(MatchmakingError, match="access token"):
        service.authenticate("alpha", "")
    with pytest.raises(MatchmakingError, match="access token"):
        service.authenticate("alpha", "wrong-token")
