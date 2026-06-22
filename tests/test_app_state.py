from anti_dating_scam_desktop.app_state import AppState


def test_app_state_stores_selected_mode() -> None:
    state = AppState()

    state.analysis_mode = "agent"

    assert state.analysis_mode == "agent"


def test_app_state_legacy_bridge_round_trips_mode_related_values() -> None:
    state = AppState(consent_accepted=True, manual_notes="hello")
    legacy = state.as_legacy_dict()
    legacy["provider_name"] = "Mock"
    legacy["risk_report"] = {"risk_level": "LOW"}

    state.sync_from_legacy_dict(legacy)

    assert state.consent_accepted is True
    assert state.manual_notes == "hello"
    assert state.risk_report == {"risk_level": "LOW"}
