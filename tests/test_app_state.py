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


def test_sync_from_legacy_dict_does_not_wipe_a_profile_loaded_outside_legacy_state() -> None:
    # Regression test for an onboarding rough edge: ProfileDetectionScreen and
    # ProfileGenerationScreen write directly to AppState.current_profile_json and
    # never touch legacy_state. MainWindow._go_home still calls
    # sync_from_legacy_dict() afterwards (shared with screens that DO use
    # legacy_state), so a stale legacy dict where "profile" was never set must not
    # overwrite the profile that was just loaded/created.
    state = AppState()
    state.current_profile_json = {"name": "onepuchman"}

    stale_legacy_state = state.as_legacy_dict()
    # Simulate the stale snapshot taken at app startup, before the profile existed.
    stale_legacy_state["profile"] = None

    state.sync_from_legacy_dict(stale_legacy_state)

    assert state.current_profile_json == {"name": "onepuchman"}


def test_sync_from_legacy_dict_still_pulls_real_legacy_updates() -> None:
    # A screen that genuinely writes a new profile into legacy_state (e.g. via an
    # import flow) must still be able to update AppState.
    state = AppState()
    legacy = state.as_legacy_dict()
    legacy["profile"] = {"name": "updated"}

    state.sync_from_legacy_dict(legacy)

    assert state.current_profile_json == {"name": "updated"}
