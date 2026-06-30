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


def test_engine_trust_ladder_stops_for_investment_pattern_phrased_naturally() -> None:
    # Same taxonomy as the risk analyzer's HIGH-severity investment rule, but phrased
    # the way a real user would write it rather than a hardcoded legacy substring.
    result = TrustLadderEngine().evaluate(
        current_stage="REPEATED_CONSISTENT_INTERACTION",
        recent_events="They told me about a trading platform with guaranteed profit.",
        consent_confirmed=True,
    )

    assert "stop_interaction" in result["recommended_actions"]
    assert result["recommended_stage"] == "UNKNOWN_STRANGER"


def test_engine_trust_ladder_slows_down_for_isolation_pressure() -> None:
    result = TrustLadderEngine().evaluate(
        current_stage="LOW_PRESSURE_CHAT",
        recent_events="They said keep this between us and your friends don't understand.",
        consent_confirmed=True,
    )

    assert "slow_down" in result["recommended_actions"]


def test_engine_trust_ladder_slows_down_for_guilt_or_fear_pressure() -> None:
    result = TrustLadderEngine().evaluate(
        current_stage="LOW_PRESSURE_CHAT",
        recent_events="They said if you loved me you would do this right now.",
        consent_confirmed=True,
    )

    assert "slow_down" in result["recommended_actions"]
