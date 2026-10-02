import json
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.screens.beacon_exchange_screen import BeaconExchangeScreen
from PySide6.QtWidgets import QApplication

from anti_dating_scam.matchmaking.attestation import card_fingerprint
from anti_dating_scam.matchmaking.beacon import parse_beacon


@pytest.fixture()
def beacon_screen(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = SimpleNamespace(json_path=tmp_path / "profile.json")
    screen = BeaconExchangeScreen(None, store, lambda: None)
    yield screen
    screen.close()
    screen.deleteLater()
    app.processEvents()


def _valid_card():
    return {
        "schema_version": "0.1", "source": "self_model_from_ai_analysis_of_own_data",
        "tier2_summary": {
            "values": ["patience"], "life_goals": "A shared routine.",
            "communication_style": "Ask clearly.", "boundaries": "No money requests.",
            "uncertainty_notes": "A limited fictional sample.",
            "evidence_notes": "Synthetic note says to slow down.",
        },
    }


def test_beacon_uses_canonical_reviewed_card_and_requires_consent(beacon_screen):
    screen = beacon_screen
    card = _valid_card()
    screen.profile_store.json_path.write_text(json.dumps(card, indent=4), encoding="utf-8")
    assert screen._card_fingerprint() == card_fingerprint(card)
    screen.pseudonym.setText("synthetic")
    screen.latitude.setText("49.28")
    screen.longitude.setText("-123.12")
    screen.age.setText("30")
    screen._generate()
    assert screen._my_beacon_text == ""
    screen.disclosure_consent.setChecked(True)
    screen._generate()
    parsed = parse_beacon(screen._my_beacon_text)
    assert parsed.age == 30
    assert parsed.card_fingerprint == card_fingerprint(card)
    screen.age.clear()
    screen._generate()
    assert screen._my_beacon_text == ""
    assert screen.my_beacon.toPlainText() == ""


def test_private_profile_cannot_be_advertised_as_a_shareable_card(beacon_screen):
    beacon_screen.profile_store.json_path.write_text(
        json.dumps({"private_notes": "synthetic personal details"}), encoding="utf-8"
    )
    assert beacon_screen._card_fingerprint() == ""
