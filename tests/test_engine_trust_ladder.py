from anti_dating_scam.engine.trust_ladder_engine import TrustLadderEngine


def test_engine_trust_ladder_recommends_slow_down_for_boundary_violation() -> None:
    result = TrustLadderEngine().evaluate(
        current_stage="LOW_PRESSURE_CHAT",
        boundary_concerns="They ignored my boundary and kept asking.",
        consent_confirmed=True,
    )

    assert "slow_down" in result["recommended_actions"]


def test_engine_trust_ladder_stops_for_money_or_sensitive_request() -> None:
    result = TrustLadderEngine().evaluate(
        current_stage="REPEATED_CONSISTENT_INTERACTION",
        money_or_sensitive_requested=True,
        consent_confirmed=True,
    )

    assert "stop_interaction" in result["recommended_actions"]
