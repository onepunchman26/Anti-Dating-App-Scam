from fastapi.testclient import TestClient

from anti_dating_scam.main import app

client = TestClient(app)


def test_money_request_returns_high_risk() -> None:
    response = client.post(
        "/risk/analyze",
        json={
            "conversation_text": (
                "I love you already. Please send me money by wire transfer for my "
                "hospital emergency today."
            ),
            "consent_confirmed": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "HIGH"
    assert any(signal["name"] == "money_or_payment_request" for signal in body["risk_signals"])
    assert any("Do not send money" in step for step in body["recommended_next_steps"])


def test_ambiguous_conversation_returns_unknown_with_uncertainty() -> None:
    response = client.post(
        "/risk/analyze",
        json={
            "conversation_text": "Hey, how are you?",
            "consent_confirmed": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "UNKNOWN"
    assert body["uncertainty"]


def test_normal_respectful_chat_returns_low_risk() -> None:
    response = client.post(
        "/risk/analyze",
        json={
            "conversation_text": (
                "I enjoyed talking with you. No pressure if you prefer to keep chatting "
                "here until you feel comfortable planning anything else."
            ),
            "consent_confirmed": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "LOW"
    assert body["risk_signals"] == []


def test_no_consent_rejects_analysis() -> None:
    response = client.post(
        "/risk/analyze",
        json={
            "conversation_text": "Please analyze this conversation.",
            "consent_confirmed": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["error_type"] == "consent_required"
