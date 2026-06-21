from fastapi.testclient import TestClient

from anti_dating_scam.main import app

client = TestClient(app)


def test_boundary_violation_recommends_slow_down() -> None:
    response = client.post(
        "/trust-ladder/evaluate",
        json={
            "current_stage": "LOW_PRESSURE_CHAT",
            "observed_events": [
                "They ignored my boundary and kept asking to move to WhatsApp immediately."
            ],
            "consent_confirmed": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "slow_down" in body["recommended_actions"]
    assert body["recommended_stage"] == "LOW_PRESSURE_CHAT"


def test_high_risk_event_recommends_stop_interaction() -> None:
    response = client.post(
        "/trust-ladder/evaluate",
        json={
            "current_stage": "REPEATED_CONSISTENT_INTERACTION",
            "observed_events": ["Asked for money and suggested crypto investment."],
            "consent_confirmed": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "stop_interaction" in body["recommended_actions"]
    assert body["recommended_stage"] == "UNKNOWN_STRANGER"
