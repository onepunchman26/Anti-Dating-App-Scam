"""Local-only observations, reflections, scoped materials and candidate choices.

The existing Work store supplies locking, guarded reads and atomic replacement.
Only current private content is retained: history stores timestamps and revision
numbers, so corrections/deletion cannot leave raw copies in immutable snapshots.
This module cannot publish, record a microphone, call a model or send messages.
"""

from __future__ import annotations

import io
import os
import re
import stat
import wave
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from anti_dating_scam.models.relationship_support import (
    CandidateFilterRequest,
    CandidateRuleRequest,
    EmptyRequest,
    MaterialConsentRequest,
    MaterialImportRequest,
    MaterialLifecycleRequest,
    MaterialReadRequest,
    MaterialTranscribeRequest,
    ObservationSaveRequest,
    RecordDeleteRequest,
    RecordReadRequest,
    ReflectionSaveRequest,
    SupportContextRequest,
    SupportState,
    TranscriptCorrectRequest,
)
from anti_dating_scam.services.report_review import (
    ReportReviewService,
    _decode,
    _encode,
    _hash,
    _unsafe,
)
from anti_dating_scam.services.work_profile import (
    MAX_STATE_BYTES,
    WorkProfileError,
    WorkProfileService,
    _destination,
    now,
    safe_operation,
)

MAX_TEXT_BYTES = 100_000
MAX_AUDIO_BYTES = 1_000_000
MAX_RECORDS = 500
MAX_MATERIALS = 100


def _stamp(entry, change):
    return [
        *entry.get("history", []),
        {
            "revision": entry["revision"],
            "updated_at": now(),
            "change": change,
        },
    ][-100:]


def _material_digest(entry):
    return _hash(
        _encode(
            {
                key: entry.get(key)
                for key in (
                    "kind",
                    "origin",
                    "text",
                    "audio_digest",
                    "transcript",
                    "transcript_source",
                    "retained_summary",
                )
            }
        )
    )


def _metadata(entry):
    # CLI tool outputs reach the native session. Do not reveal source/transcript
    # content until support-context has checked the distinct cloud scope.
    result = {
        key: value
        for key, value in entry.items()
        if key
        not in {
            "text",
            "audio_digest",
            "transcript",
            "retained_summary",
        }
    }
    result["has_text"] = entry.get("text") is not None
    result["has_audio"] = entry.get("audio_digest") is not None
    result["has_transcript"] = entry.get("transcript") is not None
    result["has_summary"] = entry.get("retained_summary") is not None
    return result


def _wav_pcm(raw):
    try:
        with wave.open(io.BytesIO(raw), "rb") as audio:
            if (
                audio.getnchannels(),
                audio.getsampwidth(),
                audio.getframerate(),
                audio.getcomptype(),
            ) != (1, 2, 16_000, "NONE"):
                raise WorkProfileError("unsupported_audio_format")
            if not 1600 <= audio.getnframes() <= 480_000:
                raise WorkProfileError("audio_duration_limit")
            pcm = audio.readframes(audio.getnframes())
            if len(pcm) != audio.getnframes() * 2:
                raise WorkProfileError("invalid_audio")
            return pcm
    except (wave.Error, EOFError):
        raise WorkProfileError("invalid_audio") from None


def _read_selected(selected, kind):
    path = Path(selected)
    if not path.is_absolute() or ".." in path.parts or path.drive.startswith("\\\\"):
        raise WorkProfileError("selected_local_file_required")
    if ":" in path.name or path.suffix.lower() not in (
        {".txt", ".md"} if kind == "text" else {".wav"}
    ):
        raise WorkProfileError("unsupported_material_type")
    for ancestor in [path, *path.parents]:
        info = ancestor.lstat()
        if _unsafe(info) or (ancestor != path and not stat.S_ISDIR(info.st_mode)):
            raise WorkProfileError("selected_local_file_required")
    path = path.resolve(strict=True)
    reader = ReportReviewService(path.parent)
    return reader._read(path, MAX_TEXT_BYTES if kind == "text" else MAX_AUDIO_BYTES)


class RelationshipSupportService:
    @safe_operation
    def __init__(self, data_dir: Path | None = None):
        self.base = WorkProfileService(data_dir)
        self.root = self.base.root
        self.store = self.base.store
        self.directory = self.root / "relationship-support"
        self.store._mkdir(self.directory)
        self.store._mkdir(self.directory / "audio")
        self.store._mkdir(self.directory / "previews")
        self.state_path = self.directory / "state.json"

    def _commit(self, state):
        validated = SupportState.model_validate(state).model_dump(mode="json")
        self.base._atomic(self.state_path, validated)

    def _load(self):
        try:
            raw = self.store._read(self.state_path, MAX_STATE_BYTES)
        except FileNotFoundError:
            state = SupportState().model_dump(mode="json")
        else:
            state = SupportState.model_validate(_decode(raw)).model_dump(mode="json")
        # References are IDs, never filenames supplied by source material.
        for group in ("observations", "reflections", "materials"):
            id_field = "material_id" if group == "materials" else "record_id"
            for key, entry in state[group].items():
                if key != entry[id_field]:
                    raise WorkProfileError("support_integrity_error")
                if group == "materials" and entry["content_digest"] != _material_digest(entry):
                    raise WorkProfileError("material_integrity_error")
        for key, rule in state["candidate_rules"].items():
            if key != _hash(_encode(rule["candidate"])):
                raise WorkProfileError("support_integrity_error")
        changed = False
        for material in state["materials"].values():
            if material["status"] in {"active", "summary_only"} and self._expired(material):
                self._purge(state, material, "expired")
                changed = True
        if changed:
            self._commit(state)  # Revoke access before removing files; fail closed.
        self._cleanup(state)
        return state

    @staticmethod
    def _expired(material):
        return datetime.fromisoformat(material["consent"]["expires_at"]) <= datetime.now(UTC)

    def _cleanup(self, state):
        # Recover only this module's reserved managed names under the same lock.
        # A killed atomic write/import must not strand a raw private temporary.
        # Previews are short lived and removed on the next operation, including
        # expiry, correction and deletion. No background deletion is claimed.
        locations = (
            (self.directory, r"[a-f0-9]{32}\.tmp"),
            (self.directory / "previews", r"[a-f0-9]{32}\.txt"),
            (self.directory / "audio", r"[a-f0-9]{32}\.wav"),
        )
        retained_audio = {
            item["material_id"]
            for item in state["materials"].values()
            if item["audio_digest"] and not item["cleanup_pending"]
        }
        for directory, pattern in locations:
            self.store._check(directory, directory=True)
            with os.scandir(directory) as children:
                for index, child in enumerate(children):
                    if index >= 1000:
                        raise WorkProfileError("storage_limit")
                    if not re.fullmatch(pattern, child.name):
                        continue
                    path = directory / child.name
                    if directory.name == "audio" and path.stem in retained_audio:
                        continue
                    self.store._check(path, directory=False)
                    path.unlink()
        changed = False
        for material in state["materials"].values():
            if material["cleanup_pending"]:
                target = self.directory / "audio" / (material["material_id"] + ".wav")
                try:
                    self.store._check(target, directory=False)
                except FileNotFoundError:
                    pass
                else:
                    target.unlink()
                material["cleanup_pending"] = False
                changed = True
        if changed:
            self._commit(state)

    @staticmethod
    def _invalidate(state, material_id):
        for group in ("observations", "reflections"):
            for entry in state[group].values():
                content = entry["content"]
                if content and any(
                    event["material_id"] == material_id for event in content["events"]
                ):
                    entry["revision"] += 1
                    entry["status"] = "source_changed"
                    entry["content"] = None
                    entry["history"] = _stamp(entry, "source_changed")

    def _purge(self, state, material, status, summary=None):
        self._invalidate(state, material["material_id"])
        material["revision"] += 1
        material["cleanup_pending"] = material["cleanup_pending"] or bool(material["audio_digest"])
        material.update(
            status=status,
            text=None,
            audio_digest=None,
            transcript=None,
            transcript_source="none",
            retained_summary=summary,
        )
        material["content_digest"] = _material_digest(material)
        material["consent"]["owner"] = dict.fromkeys(material["consent"]["owner"], False)
        material["consent"]["participants_reported_by_owner"] = dict.fromkeys(
            material["consent"]["participants_reported_by_owner"],
            False,
        )
        material["consent_revision"] = material["revision"]
        material["consent_digest"] = material["content_digest"]
        material["history"] = _stamp(material, status)

    @staticmethod
    def _get(state, group, identifier):
        if identifier not in state[group]:
            raise WorkProfileError("record_not_found")
        return state[group][identifier]

    @staticmethod
    def _version(entry, request):
        if entry["revision"] != request.expected_revision:
            raise WorkProfileError("revision_conflict")
        if hasattr(request, "content_digest") and entry["content_digest"] != request.content_digest:
            raise WorkProfileError("content_changed")

    @staticmethod
    def _require_scope(material, scope):
        if material["status"] not in {"active", "summary_only"}:
            raise WorkProfileError("material_unavailable")
        if (
            material["consent_revision"] != material["revision"]
            or material["consent_digest"] != material["content_digest"]
        ):
            raise WorkProfileError("consent_version_conflict")
        if not material["consent"]["owner"][scope]:
            raise WorkProfileError("material_scope_required")
        if (
            material["origin"] == "joint_recording"
            and not material["consent"]["participants_reported_by_owner"][scope]
        ):
            raise WorkProfileError("participant_scope_required")

    @staticmethod
    def _check_consent(consent, origin, kind):
        if datetime.fromisoformat(consent["expires_at"]) <= datetime.now(UTC):
            raise WorkProfileError("consent_expired")
        if not consent["owner"]["retain_source"]:
            raise WorkProfileError("retention_scope_required")
        if kind == "audio" and origin == "selected_conversation":
            raise WorkProfileError("joint_recording_origin_required")
        if origin == "joint_recording":
            owner = consent["owner"]
            peer = consent["participants_reported_by_owner"]
            if not owner["recording"] or not peer["recording"]:
                raise WorkProfileError("recording_scope_required")
            for scope, approved in owner.items():
                if approved and not peer[scope]:
                    raise WorkProfileError("participant_scope_required")
            if kind == "text" and not owner["transcription"]:
                raise WorkProfileError("transcription_scope_required")

    def _check_sources(self, state, content):
        for event in content["events"]:
            if event["material_id"]:
                material = self._get(state, "materials", event["material_id"])
                self._require_scope(material, "cloud_analysis")

    def _save_record(self, request, group):
        with self.store._writer(self.root):
            state = self._load()
            if request.record_id is None:
                if request.expected_revision != 0:
                    raise WorkProfileError("revision_conflict")
                if len(state[group]) >= MAX_RECORDS:
                    raise WorkProfileError("storage_limit")
                identifier = uuid4().hex
                previous = {"history": []}
            else:
                identifier = request.record_id
                previous = self._get(state, group, identifier)
                self._version(previous, request)
            content = request.content.model_dump(mode="json")
            self._check_sources(state, content)
            entry = {
                "record_id": identifier,
                "revision": request.expected_revision + 1,
                "status": "active",
                "content": content,
                "history": previous["history"],
            }
            change = "created" if request.record_id is None else "corrected"
            entry["history"] = _stamp(entry, change)
            state[group][identifier] = entry
            self._commit(state)
            return entry

    @safe_operation
    def save_observation(self, request):
        return self._save_record(ObservationSaveRequest.model_validate(request), "observations")

    @safe_operation
    def save_reflection(self, request):
        return self._save_record(ReflectionSaveRequest.model_validate(request), "reflections")

    def _read_record(self, request, group):
        request = RecordReadRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, group, request.record_id)
            if entry["content"]:
                self._check_sources(state, entry["content"])
            return entry

    @safe_operation
    def read_observation(self, request):
        return self._read_record(request, "observations")

    @safe_operation
    def read_reflection(self, request):
        return self._read_record(request, "reflections")

    def _list_records(self, request, group):
        EmptyRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            return {
                "records": [
                    {key: entry[key] for key in ("record_id", "revision", "status")}
                    for entry in state[group].values()
                ]
            }

    @safe_operation
    def list_observations(self, request):
        return self._list_records(request, "observations")

    @safe_operation
    def list_reflections(self, request):
        return self._list_records(request, "reflections")

    def _delete_record(self, request, group):
        request = RecordDeleteRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, group, request.record_id)
            self._version(entry, request)
            entry.update(revision=entry["revision"] + 1, status="deleted", content=None)
            entry["history"] = _stamp(entry, "deleted")
            self._commit(state)
            return entry

    @safe_operation
    def delete_observation(self, request):
        return self._delete_record(request, "observations")

    @safe_operation
    def delete_reflection(self, request):
        return self._delete_record(request, "reflections")

    @safe_operation
    def import_material(self, request):
        request = MaterialImportRequest.model_validate(request)
        consent = request.consent.model_dump(mode="json")
        self._check_consent(consent, request.origin, request.kind)
        raw = _read_selected(request.selected_path, request.kind)
        text = raw.decode("utf-8-sig") if request.kind == "text" else None
        if request.kind == "audio":
            _wav_pcm(raw)
        with self.store._writer(self.root):
            state = self._load()
            if len(state["materials"]) >= MAX_MATERIALS:
                raise WorkProfileError("storage_limit")
            identifier = uuid4().hex
            entry = {
                "material_id": identifier,
                "revision": 1,
                "kind": request.kind,
                "origin": request.origin,
                "status": "active",
                "consent": consent,
                "consent_revision": 1,
                "text": text,
                "audio_digest": _hash(raw) if request.kind == "audio" else None,
                "transcript": None,
                "transcript_source": "none",
                "speaker_attribution": "unverified",
                "retained_summary": None,
                "cleanup_pending": False,
            }
            entry["content_digest"] = _material_digest(entry)
            entry["consent_digest"] = entry["content_digest"]
            entry["history"] = _stamp(entry, "created")
            state["materials"][identifier] = entry
            SupportState.model_validate(state)
            target = self.directory / "audio" / (identifier + ".wav")
            try:
                if request.kind == "audio":
                    self.store._write_new(target, raw)
                self._commit(state)
            except Exception:
                # No saved receipt when state commit failed. Remove our new blob.
                if request.kind == "audio" and target.exists():
                    self.store._check(target, directory=False)
                    target.unlink()
                raise
            return _metadata(entry)

    @safe_operation
    def read_material(self, request):
        request = MaterialReadRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            return _metadata(self._get(state, "materials", request.material_id))

    @safe_operation
    def list_materials(self, request):
        EmptyRequest.model_validate(request)
        with self.store._writer(self.root):
            return {"materials": [_metadata(item) for item in self._load()["materials"].values()]}

    @safe_operation
    def preview_material(self, request):
        """Create a local plain-text review file; return its path, never its body.

        The owner can open the returned file locally before authorizing a cloud
        context. The UI must not read it back through another model tool without
        that authorization. This operation opens no app and invokes no model.
        """
        request = MaterialReadRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, "materials", request.material_id)
            if entry["status"] not in {"active", "summary_only"}:
                raise WorkProfileError("material_unavailable")
            text = "\n\n".join(
                value
                for value in (
                    entry["text"],
                    entry["transcript"],
                    entry["retained_summary"],
                )
                if value
            )
            if not text:
                raise WorkProfileError("text_preview_unavailable")
            target = self.directory / "previews" / (entry["material_id"] + ".txt")
            self.store._write_new(target, text.encode("utf-8"))
            return {
                "local_preview_path": str(target),
                "material_id": entry["material_id"],
                "revision": entry["revision"],
                "content_digest": entry["content_digest"],
                "scope": "owner_local_review_only",
                "body_returned": False,
            }

    @safe_operation
    def set_material_consent(self, request):
        request = MaterialConsentRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, "materials", request.material_id)
            self._version(entry, request)
            if entry["status"] not in {"active", "summary_only"}:
                raise WorkProfileError("material_unavailable")
            consent = request.consent.model_dump(mode="json")
            if entry["status"] == "summary_only":
                if datetime.fromisoformat(consent["expires_at"]) <= datetime.now(UTC):
                    raise WorkProfileError("consent_expired")
                if not consent["owner"]["retain_source"]:
                    raise WorkProfileError("retention_scope_required")
                if entry["origin"] == "joint_recording":
                    for scope, approved in consent["owner"].items():
                        if approved and not consent["participants_reported_by_owner"][scope]:
                            raise WorkProfileError("participant_scope_required")
            else:
                self._check_consent(consent, entry["origin"], entry["kind"])
            # Stop use of cached derivatives whenever permissions change.
            self._invalidate(state, entry["material_id"])
            entry.update(consent=consent, revision=entry["revision"] + 1)
            entry["consent_revision"] = entry["revision"]
            entry["consent_digest"] = entry["content_digest"]
            entry["history"] = _stamp(entry, "consent")
            self._commit(state)
            return _metadata(entry)

    def _set_transcript(self, state, entry, transcript, source):
        self._invalidate(state, entry["material_id"])
        entry.update(
            transcript=transcript, transcript_source=source, revision=entry["revision"] + 1
        )
        entry["content_digest"] = _material_digest(entry)
        # Previous approval does not include the newly transcribed/corrected text.
        for who in ("owner", "participants_reported_by_owner"):
            entry["consent"][who]["cloud_analysis"] = False
            entry["consent"][who]["shared_feedback"] = False
        entry["consent_revision"] = entry["revision"]
        entry["consent_digest"] = entry["content_digest"]
        entry["history"] = _stamp(entry, "transcribed" if source == "local_vosk" else "corrected")
        self._commit(state)
        return _metadata(entry)

    @safe_operation
    def transcribe_material(self, request):
        request = MaterialTranscribeRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, "materials", request.material_id)
            self._version(entry, request)
            self._require_scope(entry, "transcription")
            if entry["kind"] != "audio" or not entry["audio_digest"]:
                raise WorkProfileError("audio_source_required")
            raw = self.store._read(
                self.directory / "audio" / (entry["material_id"] + ".wav"), MAX_AUDIO_BYTES
            )
            if _hash(raw) != entry["audio_digest"]:
                raise WorkProfileError("material_integrity_error")
            from anti_dating_scam.services.voice_input import VoiceInputError, transcribe_pcm

            try:
                transcript = transcribe_pcm(_wav_pcm(raw), language=request.language)
            except VoiceInputError:
                raise WorkProfileError("local_transcription_unavailable") from None
            return self._set_transcript(state, entry, transcript, "local_vosk")

    @safe_operation
    def correct_transcript(self, request):
        request = TranscriptCorrectRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, "materials", request.material_id)
            self._version(entry, request)
            self._require_scope(entry, "transcription")
            if entry["status"] != "active":
                raise WorkProfileError("material_unavailable")
            return self._set_transcript(state, entry, request.transcript, request.source)

    @safe_operation
    def material_lifecycle(self, request):
        request = MaterialLifecycleRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            entry = self._get(state, "materials", request.material_id)
            self._version(entry, request)
            if request.action == "summary_only" and entry["status"] != "active":
                raise WorkProfileError("material_unavailable")
            status = {"delete": "deleted", "revoke": "revoked", "summary_only": "summary_only"}
            self._purge(state, entry, status[request.action], request.retained_summary)
            self._commit(state)
            self._cleanup(state)
            return _metadata(entry)

    @safe_operation
    def sweep(self, request):
        EmptyRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            return {
                "materials": [
                    {"material_id": entry["material_id"], "status": entry["status"]}
                    for entry in state["materials"].values()
                ],
                "scope": "managed_local_copies_only",
            }

    @staticmethod
    def _candidate(candidate):
        value = candidate.model_dump(mode="json")
        value["origin"] = _destination(value["origin"])
        return value

    @safe_operation
    def set_candidate_rule(self, request):
        request = CandidateRuleRequest.model_validate(request)
        candidate = self._candidate(request.candidate)
        key = _hash(_encode(candidate))
        with self.store._writer(self.root):
            state = self._load()
            previous = state["candidate_rules"].get(key)
            if request.expected_revision != (previous["revision"] if previous else 0):
                raise WorkProfileError("revision_conflict")
            if previous is None and len(state["candidate_rules"]) >= MAX_RECORDS:
                raise WorkProfileError("storage_limit")
            entry = {
                "candidate": candidate,
                "revision": request.expected_revision + 1,
                "state": request.state,
                "private_reason": request.private_reason,
                "updated_at": now(),
            }
            state["candidate_rules"][key] = entry
            self._commit(state)
            return entry

    @safe_operation
    def list_candidate_rules(self, request):
        EmptyRequest.model_validate(request)
        with self.store._writer(self.root):
            return {"private_rules": list(self._load()["candidate_rules"].values())}

    @safe_operation
    def filter_candidates(self, request):
        request = CandidateFilterRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            visible = []
            for item in request.candidates:
                candidate = self._candidate(item)
                rule = state["candidate_rules"].get(_hash(_encode(candidate)))
                if rule is None or rule["state"] == "visible":
                    visible.append(candidate)
            # Never return private reasons or create a global score/ranking.
            return {
                "visible_candidates": visible,
                "hidden_count": len(request.candidates) - len(visible),
                "local_only": True,
            }

    @safe_operation
    def prepare_context(self, request):
        request = SupportContextRequest.model_validate(request)
        with self.store._writer(self.root):
            state = self._load()
            result = {
                "purpose": request.purpose,
                "observations": [],
                "reflections": [],
                "materials": [],
                "source_content_is_untrusted": True,
                "audience": "owner_private_session",
                "publishable": False,
            }
            for group, identifiers in (
                ("observations", request.observation_ids),
                ("reflections", request.reflection_ids),
            ):
                for identifier in identifiers:
                    entry = self._get(state, group, identifier)
                    if entry["status"] != "active" or entry["content"] is None:
                        raise WorkProfileError("record_unavailable")
                    self._check_sources(state, entry["content"])
                    result[group].append(entry)
            for identifier in request.material_ids:
                entry = self._get(state, "materials", identifier)
                self._require_scope(entry, "cloud_analysis")
                result["materials"].append(
                    {
                        key: entry[key]
                        for key in (
                            "material_id",
                            "revision",
                            "content_digest",
                            "text",
                            "transcript",
                            "transcript_source",
                            "speaker_attribution",
                            "retained_summary",
                        )
                    }
                )
            return result


SUPPORT_OPERATIONS = {
    "observation-save": ("save_observation", ObservationSaveRequest),
    "observation-read": ("read_observation", RecordReadRequest),
    "observation-list": ("list_observations", EmptyRequest),
    "observation-delete": ("delete_observation", RecordDeleteRequest),
    "reflection-save": ("save_reflection", ReflectionSaveRequest),
    "reflection-read": ("read_reflection", RecordReadRequest),
    "reflection-list": ("list_reflections", EmptyRequest),
    "reflection-delete": ("delete_reflection", RecordDeleteRequest),
    "candidate-rule-set": ("set_candidate_rule", CandidateRuleRequest),
    "candidate-rule-list": ("list_candidate_rules", EmptyRequest),
    "candidate-filter": ("filter_candidates", CandidateFilterRequest),
    "material-import": ("import_material", MaterialImportRequest),
    "material-read": ("read_material", MaterialReadRequest),
    "material-list": ("list_materials", EmptyRequest),
    "material-preview": ("preview_material", MaterialReadRequest),
    "material-consent": ("set_material_consent", MaterialConsentRequest),
    "material-transcribe": ("transcribe_material", MaterialTranscribeRequest),
    "material-transcript-correct": ("correct_transcript", TranscriptCorrectRequest),
    "material-lifecycle": ("material_lifecycle", MaterialLifecycleRequest),
    "support-context": ("prepare_context", SupportContextRequest),
    "support-sweep": ("sweep", EmptyRequest),
}
