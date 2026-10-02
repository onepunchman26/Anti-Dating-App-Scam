"""Synthetic, local encrypted attachments; no messages, accounts or model calls."""

import copy
import json
import os

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from anti_dating_scam.services.reflection_chat import ReflectionChatService
from anti_dating_scam.services.relationship_exchange import (
    _HEADER,
    _MAGIC,
    _N,
    _P,
    _R,
    _VERSION,
    MAX_FILE_BYTES,
    PreparedRelationshipExport,
    RelationshipExchangeError,
    RelationshipExchangeService,
    SharedRelationshipProfile,
    _password_key,
    import_relationship_file,
    preview_relationship_profile,
    profile_digest,
)
from anti_dating_scam.services.report_review import _encode

_PASSWORD = "synthetic unique passphrase only"
_USER_TEXT = "SYNTHETIC_RAW_TRANSCRIPT_NEVER_SHARED: I prefer a calm conversation."


def _saved_reflection(tmp_path):
    vault = tmp_path / "synthetic-vault"
    vault.mkdir()
    service = ReflectionChatService()
    start = service.begin()
    question = {
        "question": {"en": "What makes a conversation comfortable?", "zh": "什么能让对话更舒服？"}
    }
    service.accept_turn(start.request_id, json.dumps(question, ensure_ascii=False))
    turn = service.propose_turn(_USER_TEXT)
    service.accept_turn(turn.request_id, json.dumps(question, ensure_ascii=False))
    service.stop()
    request = service.portrait_request()
    wire = {
        "report": {
            "schema_version": "0.2",
            "report_type": "self_portrait",
            "data_coverage": {
                "sources_read": ["S001"],
                "covered": [
                    {
                        "en": "The user's stated communication preference was considered.",
                        "zh": "已考虑用户自述的沟通偏好。",
                    }
                ],
                "not_covered": [
                    {"en": "Actual repeated behavior is unknown.", "zh": "实际重复行为尚不清楚。"}
                ],
            },
            "claims": [
                {
                    "topic": "communication",
                    "type": "speculation",
                    "confidence": "low",
                    "claim": {
                        "en": "The user may prefer calm communication.",
                        "zh": "用户可能偏好平静沟通。",
                    },
                    "evidence": [{"source": "S001", "quote": _USER_TEXT}],
                }
            ],
            "consistency_findings": [],
            "open_questions": [
                {"en": "How might both people arrange a pause?", "zh": "双方可以怎样商量暂停？"}
            ],
            "caveats": [
                {
                    "en": "A provisional interpretation of self-report only.",
                    "zh": "仅为自述的暂定解读。",
                }
            ],
        }
    }
    service.accept_portrait(request.request_id, json.dumps(wire, ensure_ascii=False))
    saved = service.save(vault, confirmed=True)
    return vault, saved


def _export(tmp_path):
    vault, saved = _saved_reflection(tmp_path)
    service = RelationshipExchangeService(vault)
    prepared = service.prepare_export(saved.session_id)
    path = tmp_path / "synthetic-attachment.slowmatch"
    exported = service.export_file(prepared, path, _PASSWORD, confirmed=True)
    return service, prepared, exported, vault, saved


def _encrypted_packet(data):
    salt, nonce = os.urandom(16), os.urandom(12)
    header = _HEADER.pack(_MAGIC, _VERSION, _N, _R, _P, salt, nonce)
    return header + AESGCM(_password_key(_PASSWORD, salt)).encrypt(nonce, data, header)


def test_selected_summary_preview_excludes_transcript_quotes_credentials_and_history(tmp_path):
    vault, saved = _saved_reflection(tmp_path)
    (vault / "synthetic-private-file.txt").write_text("SYNTHETIC_PRIVATE_FILE_NOT_SELECTED")
    service = RelationshipExchangeService(vault)
    prepared = service.prepare_export(saved.session_id)
    encoded = prepared.packet.model_dump_json()
    assert _USER_TEXT not in encoded
    for text in (_USER_TEXT, "SYNTHETIC_PRIVATE_FILE_NOT_SELECTED", saved.session_id, "S001"):
        assert (
            text not in encoded
            and text not in prepared.preview_en
            and text not in prepared.preview_zh
        )
    assert "original quotations" in prepared.preview_en and "原文引证" in prepared.preview_zh
    assert "identity" in prepared.preview_en.lower() and "未经核实" in prepared.preview_zh
    for pair in (
        [item.text for item in prepared.packet.items]
        + prepared.packet.open_questions
        + prepared.packet.unknowns
        + prepared.packet.caveats
    ):
        assert pair.en in prepared.preview_en and pair.zh in prepared.preview_zh
    assert prepared.packet.authorship == "unverified"
    assert prepared.packet.share_permission == "recipient_private_comparison_only"
    assert not (tmp_path / "attachment.slowmatch").exists()


def test_encrypted_attachment_roundtrip_is_portable_in_memory_and_preserves_source(tmp_path):
    service, prepared, exported, vault, saved = _export(tmp_path)
    before = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    raw = exported.path.read_bytes()
    for plaintext in (
        _USER_TEXT,
        prepared.packet.profile_id,
        "The user may prefer calm communication.",
        "用户可能偏好平静沟通。",
        "ai_reflection_self_report",
        saved.session_id,
    ):
        assert plaintext.encode() not in raw
    relocated = tmp_path / "received-on-another-computer.slowmatch"
    relocated.write_bytes(raw)
    imported = import_relationship_file(relocated, _PASSWORD, confirmed=True)
    assert imported == prepared.packet
    assert profile_digest(imported) == exported.packet_digest
    assert {path: path.read_bytes() for path in before} == before
    assert not any(path.name.startswith(".pending-relationship-") for path in tmp_path.iterdir())


def test_same_profile_and_password_produce_fresh_ciphertext(tmp_path):
    service, prepared, exported, _, _ = _export(tmp_path)
    second = service.export_file(prepared, tmp_path / "second.slowmatch", _PASSWORD, confirmed=True)
    assert exported.file_digest != second.file_digest
    assert import_relationship_file(second.path, _PASSWORD, confirmed=True) == prepared.packet


@pytest.mark.parametrize("confirmed", [False, None, 1, "yes"])
def test_explicit_export_consent_is_exact_boolean_and_creates_nothing(tmp_path, confirmed):
    vault, saved = _saved_reflection(tmp_path)
    service = RelationshipExchangeService(vault)
    prepared = service.prepare_export(saved.session_id)
    target = tmp_path / "rejected.slowmatch"
    with pytest.raises(RelationshipExchangeError):
        service.export_file(prepared, target, _PASSWORD, confirmed=confirmed)
    assert not target.exists()


@pytest.mark.parametrize("confirmed", [False, None, 1, "yes"])
def test_explicit_import_consent_is_exact_boolean_before_file_read(
    tmp_path, confirmed, monkeypatch
):
    from anti_dating_scam.services.report_review import ReportReviewService

    def forbidden(*args):
        raise AssertionError("Selected file must not be read before consent")

    monkeypatch.setattr(ReportReviewService, "_read", forbidden)
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(tmp_path / "not-read.slowmatch", _PASSWORD, confirmed=confirmed)


@pytest.mark.parametrize("password", [None, 3, "", "too-short", " " * 14, "x" * 257])
def test_password_bound_rejects_without_exporting(tmp_path, password):
    vault, saved = _saved_reflection(tmp_path)
    service = RelationshipExchangeService(vault)
    prepared = service.prepare_export(saved.session_id)
    target = tmp_path / "rejected.slowmatch"
    with pytest.raises(RelationshipExchangeError) as exc:
        service.export_file(prepared, target, password, confirmed=True)
    assert not target.exists()
    assert "too-short" not in str(exc.value)


def test_incorrect_password_has_safe_error_and_never_mutates_imported_file(tmp_path):
    _, _, exported, _, _ = _export(tmp_path)
    before = exported.path.read_bytes()
    with pytest.raises(RelationshipExchangeError) as exc:
        import_relationship_file(exported.path, "synthetic wrong passphrase", confirmed=True)
    assert "wrong passphrase" not in str(exc.value)
    assert str(exported.path) not in str(exc.value)
    assert exported.path.read_bytes() == before


@pytest.mark.parametrize("index", [0, 8, 10, 16, 22, -1, -20])
def test_authenticated_file_rejects_header_salt_nonce_ciphertext_or_tag_tampering(tmp_path, index):
    _, _, exported, _, _ = _export(tmp_path)
    damaged = bytearray(exported.path.read_bytes())
    damaged[index] ^= 1
    corrupted = tmp_path / "synthetic-damaged.slowmatch"
    corrupted.write_bytes(damaged)
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(corrupted, _PASSWORD, confirmed=True)


@pytest.mark.parametrize("n,r,p", [(2, 8, 1), (2**30, 8, 1), (32768, 1, 1), (32768, 8, 200)])
def test_weak_or_resource_exhausting_kdf_parameters_rejected_before_key_derivation(
    tmp_path, monkeypatch, n, r, p
):
    import anti_dating_scam.services.relationship_exchange as module

    raw = _HEADER.pack(_MAGIC, _VERSION, n, r, p, b"s" * 16, b"n" * 12) + b"x" * 30
    path = tmp_path / "synthetic-weak-params.slowmatch"
    path.write_bytes(raw)

    def forbidden(*args):
        raise AssertionError("Untrusted KDF cost must be rejected before derivation")

    monkeypatch.setattr(module, "_password_key", forbidden)
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(path, _PASSWORD, confirmed=True)


@pytest.mark.parametrize(
    "raw",
    [b"", b"SLWMATCH", b"x" * 200, b"x" * (MAX_FILE_BYTES + 1)],
    ids=["empty", "truncated", "unknown", "oversize"],
)
def test_bounded_parser_rejects_incomplete_unknown_or_oversized_container(tmp_path, raw):
    path = tmp_path / "synthetic-invalid.slowmatch"
    path.write_bytes(raw)
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(path, _PASSWORD, confirmed=True)


def test_authenticated_malicious_payload_cannot_extract_paths_or_add_transcript(tmp_path):
    _, prepared, _, _, _ = _export(tmp_path)
    payload = prepared.packet.model_dump(mode="json")
    payload["files"] = {"../../escape.txt": "Synthetic escape content"}
    payload["transcript"] = _USER_TEXT
    malformed = tmp_path / "synthetic-malicious.slowmatch"
    malformed.write_bytes(_encrypted_packet(_encode(payload)))
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(malformed, _PASSWORD, confirmed=True)
    assert not (tmp_path / "escape.txt").exists()


@pytest.mark.parametrize(
    "data",
    [
        b'{"schema_version":"1.0","schema_version":"1.0"}',
        b'{"score":NaN}',
        b"[]",
        b'"plain text"',
    ],
)
def test_authenticated_plaintext_still_needs_strict_json_and_packet_schema(tmp_path, data):
    path = tmp_path / "synthetic-malformed-plaintext.slowmatch"
    path.write_bytes(_encrypted_packet(data))
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(path, _PASSWORD, confirmed=True)


def test_existing_export_target_is_never_overwritten(tmp_path):
    service, prepared, exported, _, _ = _export(tmp_path)
    before = exported.path.read_bytes()
    with pytest.raises(RelationshipExchangeError):
        service.export_file(prepared, exported.path, _PASSWORD, confirmed=True)
    assert exported.path.read_bytes() == before


def test_changed_prepared_summary_is_rejected_against_selected_saved_reflection(tmp_path):
    vault, saved = _saved_reflection(tmp_path)
    service = RelationshipExchangeService(vault)
    prepared = service.prepare_export(saved.session_id)
    data = prepared.model_dump()
    data["packet"]["items"][0]["text"]["en"] = "Synthetic changed interpretation."
    changed = PreparedRelationshipExport.model_validate(data)
    target = tmp_path / "not-created.slowmatch"
    with pytest.raises(RelationshipExchangeError):
        service.export_file(changed, target, _PASSWORD, confirmed=True)
    assert not target.exists()


def test_changed_selected_history_is_rejected_before_export(tmp_path):
    vault, saved = _saved_reflection(tmp_path)
    service = RelationshipExchangeService(vault)
    prepared = service.prepare_export(saved.session_id)
    report = saved.directory / "self_portrait.json"
    report.write_bytes(report.read_bytes() + b" ")
    with pytest.raises(RelationshipExchangeError):
        service.export_file(prepared, tmp_path / "not-created.slowmatch", _PASSWORD, confirmed=True)


def test_import_rejects_symlink_or_hardlink_file(tmp_path):
    _, _, exported, _, _ = _export(tmp_path)
    hardlinked = tmp_path / "synthetic-hardlink.slowmatch"
    try:
        os.link(exported.path, hardlinked)
    except OSError:
        pytest.skip("This filesystem cannot create hard links.")
    with pytest.raises(RelationshipExchangeError):
        import_relationship_file(hardlinked, _PASSWORD, confirmed=True)


def test_export_rejects_symlink_parent_without_writing_outside(tmp_path):
    service, prepared, _, _, _ = _export(tmp_path)
    outside = tmp_path / "synthetic-other-folder"
    outside.mkdir()
    link = tmp_path / "synthetic-parent-link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("This Windows session cannot create symlinks.")
    with pytest.raises(RelationshipExchangeError):
        service.export_file(prepared, link / "attachment.slowmatch", _PASSWORD, confirmed=True)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize(
    "filename", ["synthetic.slowmatch:stream", "synthetic.slowmatch.", "synthetic.slowmatch "]
)
def test_export_rejects_windows_alias_filenames(tmp_path, filename):
    service, prepared, _, _, _ = _export(tmp_path)
    with pytest.raises(RelationshipExchangeError):
        service.export_file(prepared, tmp_path / filename, _PASSWORD, confirmed=True)


def test_failed_atomic_publication_exposes_no_partial_file_or_plaintext(tmp_path, monkeypatch):
    service, prepared, _, _, _ = _export(tmp_path)
    target = tmp_path / "never-published.slowmatch"

    def fail(*args, **kwargs):
        raise OSError("SYNTHETIC_PRIVATE_PUBLISH_FAILURE")

    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(RelationshipExchangeError) as exc:
        service.export_file(prepared, target, _PASSWORD, confirmed=True)
    assert "SYNTHETIC_PRIVATE" not in str(exc.value)
    assert not target.exists()
    assert not any(path.name.startswith(".pending-relationship-") for path in tmp_path.iterdir())


def test_packet_models_reject_scores_and_missing_bilingual_uncertainty(tmp_path):
    _, prepared, _, _, _ = _export(tmp_path)
    for change in ("score", "zh", "unknowns"):
        data = copy.deepcopy(prepared.packet.model_dump())
        if change == "score":
            data["public_score"] = 90
        elif change == "zh":
            del data["items"][0]["text"]["zh"]
        else:
            data["unknowns"] = []
        with pytest.raises(ValueError):
            SharedRelationshipProfile.model_validate(data)


def test_prepare_only_reads_explicitly_selected_history_not_other_vault_files(
    tmp_path, monkeypatch
):
    vault, saved = _saved_reflection(tmp_path)
    from anti_dating_scam.services.report_review import ReportReviewService

    original = ReportReviewService._read
    reads = []

    def scoped(self, path, limit):
        reads.append(path)
        assert path.parent == saved.directory
        return original(self, path, limit)

    monkeypatch.setattr(ReportReviewService, "_read", scoped)
    prepared = RelationshipExchangeService(vault).prepare_export(saved.session_id)
    assert len(reads) == 4
    assert prepared.packet.items
    assert preview_relationship_profile(prepared.packet, "zh")
