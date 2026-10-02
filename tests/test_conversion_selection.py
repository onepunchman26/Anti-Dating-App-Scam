"""Synthetic versioned selection and recovery for preserved legacy conversions."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from anti_dating_scam_desktop import agent_handoff, ai_backend
from anti_dating_scam_desktop.profile_store import ProfileStore
from fastapi.testclient import TestClient
from test_active_reports import _seed

from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.services import active_reports as module
from anti_dating_scam.services.active_reports import (
    ActiveReportError,
    ActiveReportService,
    LegacyReviewOnlyError,
)
from anti_dating_scam.services.legacy_conversions import LegacyConversionService
from anti_dating_scam.services.legacy_reports import LegacyReportService
from anti_dating_scam.services.local_client_state import LocalClientState
from anti_dating_scam.services.report_review import ReportReviewService, _encode, _hash


def _legacy_conversion(tmp_path, kind="self_portrait"):
    store = ProfileStore(tmp_path / "vault", config_path=tmp_path / "device.json")
    store.create_default_directories()
    store.save_import_text("SYNTHETIC_OWNER_ORIGINAL_ONLY", "notes.md")
    claim = {
        "topic": "communication",
        "claim" if kind == "self_portrait" else "criterion": {
            "en": "May prefer quiet time.", "zh": "可能偏好安静时间。",
        },
        "type": "inference", "confidence": "low",
        "evidence": [{"quote": "I need quiet time.", "source": "synthetic-note"}],
    }
    if kind == "self_portrait":
        payload = {"schema_version": "0.3", "claims": [claim]}
    else:
        payload = {"schema_version": "0.1", "stated_criteria": [claim], "revealed_criteria": []}
    payload.update({
        "caveats": [{"en": "Synthetic and uncertain.", "zh": "合成且不确定。"}],
        "unmapped_legacy_field": "PRESERVED_ARCHIVE_ONLY",
    })
    source = store.reports_dir / f"{kind}.json"
    source.write_bytes(_encode(payload))
    (store.reports_dir / f"{kind}.md").write_text(
        "RAW_LEGACY_MUST_NOT_RETURN", encoding="utf-8",
    )
    archives = LegacyReportService(store.base_dir)
    archived = archives.save_archive(archives.preview_archive(
        kind, expected_digest=archives.inspect(kind).source_digest,
    ), confirmed=True)
    conversions = LegacyConversionService(store.base_dir)
    saved = conversions.save_conversion(
        conversions.preview_conversion(kind, archived.id), confirmed=True,
    )
    return store, ActiveReportService(store.base_dir), saved, archived


def _conversion_preview(service, identifier, kind="self_portrait"):
    return service.preview_conversion_selection(
        kind, identifier,
        expected_selection_version=service.get_selection(kind).selection_version,
    )


def _disabled_preview(service, kind="self_portrait"):
    return service.preview_legacy_review_only(
        kind, expected_selection_version=service.get_selection(kind).selection_version,
    )


def _original_preview(service, kind="self_portrait", revision_id=None):
    return service.preview_selection(
        kind, revision_id,
        expected_selection_version=service.get_selection(kind).selection_version,
    )


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_disable_is_explicit_persistent_and_can_restore_strict_current_original(tmp_path, kind):
    service, source, copy = _seed(tmp_path, kind)
    service.select(_original_preview(service, kind, copy.id), confirmed=True)
    original_journal = {
        path: path.read_bytes() for path in source.parent.rglob("selection.json")
    }
    preview = _disabled_preview(service, kind)
    assert "disabled" in preview.markdown and "停用" in preview.markdown
    selected = service.select_review_only(preview, confirmed=True)
    assert selected.target_kind == "legacy_review_only"
    fresh = ActiveReportService(source.parent.parent)
    assert fresh.get_selection(kind) == selected
    with pytest.raises(LegacyReviewOnlyError, match="disabled"):
        fresh.resolve(kind)
    # The old 0.1 transaction is byte-for-byte unchanged inside the mixed chain.
    assert all(path.read_bytes() == raw for path, raw in original_journal.items())
    fresh.select(_original_preview(fresh, kind), confirmed=True)
    resolved = fresh.resolve(kind)
    assert resolved.revision_id is None and not hasattr(resolved, "target_kind")
    assert [event.schema_version for event, _ in fresh._history(kind)[0]] == ["0.1", "0.2", "0.1"]


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true", [], {}])
def test_disable_requires_exact_confirmation_without_creating_journal(tmp_path, confirmed):
    service = ActiveReportService(tmp_path)
    preview = _disabled_preview(service)
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(ActiveReportError):
        service.select_review_only(preview, confirmed=confirmed)
    assert list(tmp_path.iterdir()) == []


def test_disable_recovery_reads_neither_damaged_selected_target_nor_original(tmp_path, monkeypatch):
    service, source, _copy = _seed(tmp_path)
    service.select(_original_preview(service), confirmed=True)
    source.write_bytes(b"SYNTHETIC_DAMAGED_PRIVATE_ORIGINAL")

    def forbidden(*args, **kwargs):
        raise AssertionError("A disabled-reference selection must not read report targets.")

    monkeypatch.setattr(ActiveReportService, "_target", forbidden)
    monkeypatch.setattr(ActiveReportService, "_conversion_target", forbidden)
    service.select_review_only(_disabled_preview(service), confirmed=True)
    with pytest.raises(LegacyReviewOnlyError) as error:
        service.resolve("self_portrait")
    assert "SYNTHETIC_DAMAGED" not in str(error.value)


def test_disable_never_makes_invalid_original_selectable(tmp_path):
    service, source, _copy = _seed(tmp_path)
    source.write_bytes(b'{"schema_version":"0.3","headline":"Legacy narrative"}')
    service.select_review_only(_disabled_preview(service), confirmed=True)
    with pytest.raises(ActiveReportError):
        _original_preview(service)
    with pytest.raises(LegacyReviewOnlyError):
        service.resolve("self_portrait")


@pytest.mark.parametrize("change", ["markdown", "kind", "previous_selection_version"])
def test_modified_disable_preview_is_rejected(tmp_path, change):
    service = ActiveReportService(tmp_path)
    preview = _disabled_preview(service)
    value = {"markdown": "Invented preview", "kind": "mate_criteria",
             "previous_selection_version": "f" * 64}[change]
    with pytest.raises(ActiveReportError):
        service.select_review_only(preview.model_copy(update={change: value}), confirmed=True)
    assert service.resolve("self_portrait") is None


def test_concurrent_disable_same_preview_has_one_commit(tmp_path):
    service = ActiveReportService(tmp_path)
    preview = _disabled_preview(service)

    def commit(_):
        try:
            return ActiveReportService(tmp_path).select_review_only(preview, confirmed=True)
        except ActiveReportError:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(commit, range(4)))
    assert sum(result is not None for result in results) == 1
    assert len(list(tmp_path.rglob("selection.json"))) == 1
    with pytest.raises(ActiveReportError):
        service.select_review_only(preview, confirmed=True)


@pytest.mark.parametrize("damage", [
    "extra", "kind", "schema_version", "target_kind", "preview_digest",
])
def test_new_event_rejects_unknown_fields_versions_and_invalid_derivation(tmp_path, damage):
    service = ActiveReportService(tmp_path)
    service.select_review_only(_disabled_preview(service), confirmed=True)
    path = next(tmp_path.rglob("selection.json"))
    payload = json.loads(path.read_bytes())
    payload[damage] = {
        "extra": "unexpected", "kind": "mate_criteria", "schema_version": "9.9",
        "target_kind": "unselected", "preview_digest": "1" * 64,
    }[damage]
    payload["event_digest"] = _hash(_encode({
        key: value for key, value in payload.items() if key != "event_digest"
    }))
    path.write_bytes(_encode(payload))
    with pytest.raises(ActiveReportError) as error:
        service.resolve("self_portrait")
    assert not isinstance(error.value, LegacyReviewOnlyError)


def test_failed_disable_write_leaves_old_selection_and_pending_inert(tmp_path, monkeypatch):
    service, source, _copy = _seed(tmp_path)
    prior = service.select(_original_preview(service), confirmed=True)
    original = ReportReviewService._write_new

    def fail(self, path, data):
        original(self, path, data)
        raise OSError("Synthetic write failure")

    monkeypatch.setattr(ReportReviewService, "_write_new", fail)
    with pytest.raises(ActiveReportError):
        service.select_review_only(_disabled_preview(service), confirmed=True)
    assert service.get_selection("self_portrait") == prior
    assert service.resolve("self_portrait").revision_id is None
    journal = source.parent / "active_selections" / "self_portrait"
    assert len(list(journal.glob(".pending-*"))) == 1


def test_final_journal_slot_allows_disabling(tmp_path, monkeypatch):
    service, _source, _copy = _seed(tmp_path)
    monkeypatch.setattr(module, "MAX_SELECTIONS", 2)
    service.select(_original_preview(service), confirmed=True)
    service.select_review_only(_disabled_preview(service), confirmed=True)
    with pytest.raises(LegacyReviewOnlyError):
        service.resolve("self_portrait")
    with pytest.raises(ActiveReportError):
        service.select(_original_preview(service), confirmed=True)


class _Recorder:
    name = "Synthetic test recorder"

    def __init__(self):
        self.messages = []

    def chat(self, messages, system=None):
        self.messages = messages
        return "Synthetic response."


def test_disabled_selection_stops_desktop_handoff_and_browser_fallback(tmp_path):
    store = ProfileStore(tmp_path / "vault", config_path=tmp_path / "device.json")
    store.create_default_directories()
    for path in (store.self_portrait_path, store.self_portrait_detailed_path):
        path.write_text("RAW_LEGACY_MUST_NOT_RETURN", encoding="utf-8")
    service = ActiveReportService(store.base_dir)
    service.select_review_only(_disabled_preview(service), confirmed=True)
    for consumer in (
        store.load_self_portrait, store.load_self_portrait_json,
        lambda: ai_backend.build_interview_reference(store),
        lambda: ai_backend.interview_reference_version(store),
        lambda: agent_handoff.build_criteria_interview_request(store.base_dir),
    ):
        with pytest.raises(LegacyReviewOnlyError):
            consumer()
    backend = _Recorder()
    app = create_client_app()
    app.state.local_client_state = LocalClientState(
        store.base_dir, tmp_path / "browser.json", backend,
    )
    client = TestClient(app, base_url="http://127.0.0.1:8471")
    assert client.get("/local/report").status_code == 409
    assert client.post("/local/ai/chat", json={
        "messages": [{"role": "user", "content": "Synthetic question"}],
    }).status_code == 409
    assert backend.messages == []


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
def test_real_conversion_select_reopen_disable_preserves_originals_and_archives(tmp_path, kind):
    store, service, saved, _archived = _legacy_conversion(tmp_path, kind)
    before = {path: path.read_bytes() for path in store.base_dir.rglob("*") if path.is_file()}
    with pytest.raises(ActiveReportError):
        _original_preview(service, kind)
    preview = _conversion_preview(service, saved.id, kind)
    assert "May prefer quiet time" in preview.markdown
    assert "PRESERVED_ARCHIVE_ONLY" not in preview.markdown
    selected = service.select_conversion(preview, confirmed=True)
    assert selected.target_kind == "legacy_conversion" and selected.conversion_id == saved.id
    reopened = ActiveReportService(store.base_dir).resolve(kind)
    assert reopened.target_kind == "legacy_conversion" and reopened.conversion_id == saved.id
    assert reopened.content_digest == preview.target_bundle_digest
    assert reopened.markdown == preview.markdown
    assert all(path.read_bytes() == raw for path, raw in before.items())
    service.select_review_only(_disabled_preview(service, kind), confirmed=True)
    with pytest.raises(LegacyReviewOnlyError):
        service.resolve(kind)
    service.select_conversion(_conversion_preview(service, saved.id, kind), confirmed=True)
    assert service.resolve(kind).conversion_id == saved.id


@pytest.mark.parametrize("change", [
    "json", "markdown", "missing_companion", "conversion", "archive",
])
def test_conversion_preview_rejects_changed_source_presence_archive_or_target(tmp_path, change):
    store, service, saved, archived = _legacy_conversion(tmp_path)
    preview = _conversion_preview(service, saved.id)
    path = {
        "json": store.self_portrait_json_path,
        "markdown": store.self_portrait_path,
        "missing_companion": store.self_portrait_detailed_path,
        "conversion": store.reports_dir / "converted_reports" / "self_portrait"
        / saved.id / "report.md",
        "archive": store.reports_dir / "legacy_archives" / "self_portrait"
        / archived.id / "preview.json",
    }[change]
    path.write_bytes((path.read_bytes() if path.exists() else b"") + b" \n")
    with pytest.raises(ActiveReportError):
        service.select_conversion(preview, confirmed=True)
    assert service.resolve("self_portrait") is None


@pytest.mark.parametrize("change", ["source", "conversion", "archive"])
def test_stale_or_damaged_conversion_fails_closed_but_can_be_disabled(tmp_path, change):
    store, service, saved, archived = _legacy_conversion(tmp_path)
    service.select_conversion(_conversion_preview(service, saved.id), confirmed=True)
    path = {
        "source": store.self_portrait_json_path,
        "conversion": store.reports_dir / "converted_reports" / "self_portrait"
        / saved.id / "manifest.json",
        "archive": store.reports_dir / "legacy_archives" / "self_portrait"
        / archived.id / "manifest.json",
    }[change]
    path.write_bytes(b"SYNTHETIC_DAMAGED_MEMBER")
    with pytest.raises(ActiveReportError):
        service.resolve("self_portrait")
    service.select_review_only(_disabled_preview(service), confirmed=True)
    with pytest.raises(LegacyReviewOnlyError):
        service.resolve("self_portrait")


@pytest.mark.parametrize("confirmed", [False, None, 1, "true"])
def test_conversion_consent_is_strict(tmp_path, confirmed):
    _store, service, saved, _archived = _legacy_conversion(tmp_path)
    with pytest.raises(ActiveReportError):
        service.select_conversion(_conversion_preview(service, saved.id), confirmed=confirmed)
    assert service.get_selection("self_portrait").selection_version == "0" * 64


@pytest.mark.parametrize("field", [
    "conversion_id", "markdown", "source_digest", "integrity_digest",
])
def test_conversion_shallow_model_copy_tampering_is_rejected(tmp_path, field):
    _store, service, saved, _archived = _legacy_conversion(tmp_path)
    preview = _conversion_preview(service, saved.id)
    value = "f" * (32 if field == "conversion_id" else 64)
    with pytest.raises(ActiveReportError):
        service.select_conversion(preview.model_copy(update={field: value}), confirmed=True)
    assert service.get_selection("self_portrait").selection_version == "0" * 64


@pytest.mark.parametrize("changed_member", ["source", "archive"])
def test_conversion_change_during_selection_commit_leaves_disabled_state(
    tmp_path, monkeypatch, changed_member,
):
    store, service, saved, archived = _legacy_conversion(tmp_path)
    prior = service.select_review_only(_disabled_preview(service), confirmed=True)
    preview = _conversion_preview(service, saved.id)
    path = (
        store.self_portrait_json_path if changed_member == "source"
        else store.reports_dir / "legacy_archives" / "self_portrait"
        / archived.id / "preview.json"
    )
    original_write = ReportReviewService._write_new

    def interfere(self, target, data):
        original_write(self, target, data)
        if target.name == "selection.json":
            path.write_bytes(path.read_bytes() + b"\n")

    monkeypatch.setattr(ReportReviewService, "_write_new", interfere)
    with pytest.raises(ActiveReportError):
        service.select_conversion(preview, confirmed=True)
    assert service.get_selection("self_portrait") == prior
    with pytest.raises(LegacyReviewOnlyError):
        service.resolve("self_portrait")


@pytest.mark.parametrize("use_revision", [False, True])
def test_original_selection_http_metadata_keeps_legacy_shape(tmp_path, use_revision):
    service, source, copy = _seed(tmp_path)
    revision_id = copy.id if use_revision else None
    state = service.select(_original_preview(service, revision_id=revision_id), confirmed=True)
    app = create_client_app()
    app.state.local_client_state = LocalClientState(
        source.parent.parent, tmp_path / "browser.json", _Recorder(),
    )
    client = TestClient(app, base_url="http://127.0.0.1:8471")
    response = client.get("/local/report")
    assert response.status_code == 200
    assert response.json()["desktop_selection"] == {
        "revision_id": revision_id, "selection_version": state.selection_version,
    }


def test_conversion_then_current_regeneration_requires_explicit_valid_original_selection(tmp_path):
    store, service, saved, _archived = _legacy_conversion(tmp_path)
    service.select_conversion(_conversion_preview(service, saved.id), confirmed=True)
    canonical = LegacyConversionService(store.base_dir).read_verified_bundle(
        "self_portrait", saved.id,
    )
    store.self_portrait_json_path.write_bytes(_encode(canonical.canonical["report"]))
    (store.reports_dir / "self_portrait_localization.json").write_bytes(_encode({
        "schema_version": "0.1", "localized_text": canonical.localized_text,
    }))
    with pytest.raises(ActiveReportError):
        service.resolve("self_portrait")
    service.select(_original_preview(service), confirmed=True)
    resolved = service.resolve("self_portrait")
    assert resolved.revision_id is None and not hasattr(resolved, "conversion_id")
    assert [event.schema_version for event, _ in service._history("self_portrait")[0]] == [
        "0.2", "0.1",
    ]


def test_conversion_consumer_reference_is_assistant_only_and_archive_is_inert(tmp_path):
    store, service, saved, _archived = _legacy_conversion(tmp_path)
    before = ai_backend.interview_reference_version(store)
    service.select_conversion(_conversion_preview(service, saved.id), confirmed=True)
    reference, version = ai_backend.interview_reference_snapshot(store)
    assert before != version and "May prefer quiet time" in reference
    assert "PRESERVED_ARCHIVE_ONLY" not in reference
    assert store.load_self_portrait() == service.resolve("self_portrait").markdown
    for builder in (agent_handoff.build_criteria_interview_request,
                    agent_handoff.build_criteria_interview_prompt):
        manual = builder(store.base_dir)
        assert "May prefer quiet time" in manual
        assert "PRESERVED_ARCHIVE_ONLY" not in manual and "RAW_LEGACY" not in manual
    backend = _Recorder()
    app = create_client_app()
    app.state.local_client_state = LocalClientState(
        store.base_dir, tmp_path / "browser.json", backend,
    )
    client = TestClient(app, base_url="http://127.0.0.1:8471")
    shown = client.get("/local/report")
    assert shown.status_code == 200 and "May prefer quiet time" in shown.json()["md"]
    assert shown.json()["desktop_selection"] == {
        "revision_id": None,
        "selection_version": service.get_selection("self_portrait").selection_version,
        "target_kind": "legacy_conversion", "conversion_id": saved.id,
    }
    assert client.post("/local/ai/chat", json={
        "messages": [{"role": "user", "content": "Synthetic current question"}],
    }).status_code == 200
    owner_text = str([message for message in backend.messages if message["role"] == "user"])
    assistant_text = str([
        message for message in backend.messages if message["role"] == "assistant"
    ])
    assert "SYNTHETIC_OWNER_ORIGINAL_ONLY" in owner_text
    assert "May prefer quiet time" not in owner_text and "May prefer quiet time" in assistant_text
    assert "PRESERVED_ARCHIVE_ONLY" not in str(backend.messages)
    assert "RAW_LEGACY_MUST_NOT_RETURN" not in str(backend.messages)
