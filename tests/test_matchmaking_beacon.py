import pytest

from anti_dating_scam.matchmaking.beacon import (
    BeaconError,
    create_beacon,
    mutual_match,
    parse_beacon,
)
from anti_dating_scam.matchmaking.geo import encode_geohash

BUCKET = encode_geohash(49.2827, -123.1207)[:4]
FAR_BUCKET = encode_geohash(31.2304, 121.4737)[:4]
FINGERPRINT = "a" * 64


def _beacon_text(**overrides) -> str:
    values = {
        "consent_confirmed": True,
        "pseudonym": "mirage",
        "bucket": BUCKET,
        "card_fingerprint": FINGERPRINT,
        "age": 30,
        "seeking_age_min": 25,
        "seeking_age_max": 40,
        "contact_hint": "DM me in this group",
    }
    values.update(overrides)
    return create_beacon(**values)


def test_beacon_roundtrip_preserves_fields() -> None:
    text = _beacon_text()
    assert "BEGIN AI-SLOWMATCH BEACON" in text

    beacon = parse_beacon(text)

    assert beacon.pseudonym == "mirage"
    assert beacon.bucket == BUCKET
    assert beacon.card_fingerprint == FINGERPRINT
    assert beacon.contact_hint == "DM me in this group"


def test_beacon_survives_platform_style_rewrapping() -> None:
    # Platforms often re-wrap lines; parsing must tolerate that.
    text = _beacon_text().replace("\n", " \n ")
    assert parse_beacon(text).pseudonym == "mirage"


def test_tampered_beacon_fails_integrity_check() -> None:
    text = _beacon_text()
    lines = text.splitlines()
    # Flip a character inside the base64 body (not the armor lines).
    body_index = 1
    line = lines[body_index]
    swapped = ("A" if line[0] != "A" else "B") + line[1:]
    tampered = "\n".join([lines[0], swapped, *lines[2:]])

    with pytest.raises(BeaconError):
        parse_beacon(tampered)


def test_beacon_requires_pseudonym_and_valid_bucket() -> None:
    with pytest.raises(BeaconError):
        create_beacon(pseudonym="  ", bucket=BUCKET, card_fingerprint=FINGERPRINT)
    with pytest.raises(BeaconError):
        create_beacon(
            pseudonym="x", bucket="49.28,-123.1", card_fingerprint=FINGERPRINT
        )  # raw coordinates rejected


def test_mutual_match_same_bucket_and_gates() -> None:
    mine = parse_beacon(_beacon_text())
    theirs = parse_beacon(_beacon_text(pseudonym="harbor", age=32))

    matched, reasons = mutual_match(mine, theirs)

    assert matched is True
    assert any("same coarse area" in reason for reason in reasons)


def test_mutual_match_fails_on_distance_and_gates() -> None:
    mine = parse_beacon(_beacon_text())
    far = parse_beacon(_beacon_text(pseudonym="far", bucket=FAR_BUCKET))
    matched, reasons = mutual_match(mine, far)
    assert matched is False
    assert any("different coarse location" in reason for reason in reasons)

    too_young_for_them = parse_beacon(
        _beacon_text(pseudonym="gate", seeking_age_min=50, seeking_age_max=60)
    )
    matched, reasons = mutual_match(mine, too_young_for_them)
    assert matched is False
    assert any("your profile does not fit" in reason for reason in reasons)


def test_no_score_in_match_output() -> None:
    mine = parse_beacon(_beacon_text())
    theirs = parse_beacon(_beacon_text(pseudonym="harbor"))
    _matched, reasons = mutual_match(mine, theirs)
    joined = " ".join(reasons).lower()
    assert "%" not in joined and "score" not in joined
