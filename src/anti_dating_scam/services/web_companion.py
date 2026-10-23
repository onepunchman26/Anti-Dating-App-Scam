"""Account-owned web conversations; no remote storage or implicit vault discovery."""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionService
from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.services.coaching_policy import COACHING_POLICY
from anti_dating_scam.services.relationship_interview import (
    InterviewControl,
    InterviewState,
    accept_reply,
    control,
    interview_policy,
)
from anti_dating_scam.services.work_profile import WorkProfileService


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("*", mode="before")
    @classmethod
    def exact_consent(cls, value, info):
        if (
            info.field_name in {"confirmed", "cloud_consent", "included_plan_confirmed"}
            and value is not True
        ):
            raise ValueError("explicit_consent_required")
        return value


class VaultInput(Input):
    confirmed: Literal[True]
    path: str = Field(default="", max_length=500)


class TurnInput(Input):
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    expected_revision: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=4000)
    language: Literal["en", "zh-CN"]
    model: str = Field(min_length=1, max_length=200)
    cloud_consent: Literal[True]
    included_plan_confirmed: Literal[True]
    include_profile: bool = False


ConversationTopic = Literal[
    "self",
    "dating",
    "friendship",
    "reflection",
    "support",
    "preparation",
    "in_meeting",
    "direction",
]


class SessionInput(Input):
    topic: ConversationTopic
    guided: bool = False
    language: Literal["en", "zh-CN"] = "en"
    reuse_session_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


class ReadInput(Input):
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")


class Session(Input):
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    topic: ConversationTopic
    revision: int = 0
    messages: list[dict] = Field(default_factory=list, max_length=200)
    interview: InterviewState | None = None


class CompanionError(ValueError):
    pass


class WebCompanion:
    def __init__(self, state_root: Path, connection=None):
        self.connection = connection or ChatGPTConnectionService()
        self.state = WorkProfileService(state_root)
        self.vault = None
        self.account = ""
        self.lock = threading.Lock()
        self.cancel = threading.Event()
        self.inference_passed = False
        self.models = []

    def _identity(self):
        status = self.connection.status()
        if not status.connected or not status.client_id:
            raise CompanionError("sign_in_required")
        return hashlib.sha256(status.client_id.encode()).hexdigest()[:32]

    def _ready(self):
        if not self.vault:
            raise CompanionError("vault_required")
        if self._identity() != self.account:
            self.cancel.set()
            self.vault = None
            self.models = []
            self.inference_passed = False
            raise CompanionError("account_changed")
        return self.vault

    def status(self):
        status = self.connection.status()
        if self.vault:
            self._ready()
        return {
            "protocol": "1.0",
            "capabilities": [
                "private-chat",
                "group-suggest",
                "relationship-interview-v1",
                "private-candidate-review",
                "summary-draft",
                "private-reflection-v1",
                "local-voice-v1",
            ],
            "account_label": status.label,
            "connected": status.connected,
            "plan_permission": status.sharing,
            "vault_ready": bool(self.vault),
            "vault_path": str(self.vault.root) if self.vault else "",
            "inference_passed": self.inference_passed,
            "models": self.models,
            "busy": self.lock.locked(),
            "login_phase": self.connection.diagnostic().phase,
        }

    def catalog(self):
        self.models = [m.model_dump() for m in self.connection.list_models()]
        return self.models

    def initialize(self, data):
        request = VaultInput.model_validate(data)
        account = self._identity()
        pointer = self.state.root / (account + ".json")
        saved = self.state._read(pointer, VaultInput) if pointer.exists() else None
        root = Path(
            request.path
            or (
                saved.path if saved else str(self.state.root.parent / "accounts" / account / "work")
            )
        )
        # Only the explicit current selection is inspected; no old-vault scan.
        from anti_dating_scam.services.work_profile import _check_location

        root = root.absolute()
        _check_location(root)
        marker = root / "web-owner.json"
        if root.exists() and any(root.iterdir()) and not marker.exists():
            raise CompanionError("existing_vault_needs_explicit_migration")
        vault = WorkProfileService(root)
        # Windows packaged apps can resolve AppData to their per-app location.
        # The guarded store is bound to that verified canonical root; never
        # mix the original spelling with paths used for its atomic writes.
        root = vault.root
        marker = root / "web-owner.json"

        class Owner(Input):
            account: str

        if marker.exists() and vault._read(marker, Owner).account != account:
            raise CompanionError("vault_account_mismatch")
        vault._atomic(marker, Owner(account=account).model_dump())
        vault.store._mkdir(root / "sessions")
        # A real guarded write/read, never claimed as a restart test.
        probe = root / "web-storage-check.json"
        vault._atomic(probe, Owner(account=account).model_dump())
        if vault._read(probe, Owner).account != account:
            raise CompanionError("storage_check_failed")
        self.state._atomic(pointer, {"confirmed": True, "path": str(vault.root)})
        self.vault, self.account = vault, account
        return self.status()

    def sessions(self):
        vault = self._ready()
        result = []
        for path in sorted((vault.root / "sessions").glob("*.json"))[:100]:
            session = vault._read(path, Session)
            result.append(
                {
                    "id": session.id,
                    "topic": session.topic,
                    "revision": session.revision,
                    "interview": bool(session.interview),
                }
            )
        return result

    def create_session(self, data):
        request = SessionInput.model_validate(data)
        vault = self._ready()
        if len(self.sessions()) >= 100:
            raise CompanionError("session_limit")
        session = Session(id=uuid4().hex, topic=request.topic)
        if request.guided:
            if request.topic not in {"dating", "friendship"}:
                raise CompanionError("interview_topic_required")
            session.interview = InterviewState()
        if request.reuse_session_id:
            previous = self.read_session({"session_id": request.reuse_session_id})
            if not request.guided or previous.topic != request.topic or not previous.interview:
                raise CompanionError("interview_reuse_mismatch")
            # Explicitly selected, same account/topic; no transcript or vault scan.
            session.interview = previous.interview.model_copy(deep=True)
            session.interview.awaiting = None
        elif request.guided:
            question = {
                "dating": (
                    "If you met someone suitable, how would you like the relationship to develop?",
                    "如果遇到合适的人，你希望关系怎样发展？",
                ),
                "friendship": (
                    "What would you enjoy sharing with a friend?",
                    "你希望和朋友一起分享怎样的时光？",
                ),
            }[request.topic][request.language == "zh-CN"]
            session.messages = [{"role": "assistant", "content": question}]
            session.interview.question_count = 1
            session.interview.awaiting = "goal"
            session.interview.asked["goal"] = 1
        vault._atomic(vault.root / "sessions" / (session.id + ".json"), session.model_dump())
        return session.model_dump()

    def read_session(self, data):
        request = ReadInput.model_validate(data)
        vault = self._ready()
        return vault._read(vault.root / "sessions" / (request.session_id + ".json"), Session)

    def send(self, data):
        request = TurnInput.model_validate(data)
        if not request.text.strip():
            raise CompanionError("empty_message")
        if not self.lock.acquire(blocking=False):
            raise CompanionError("request_in_progress")
        self.cancel.clear()
        try:
            vault = self._ready()
            session = self.read_session({"session_id": request.session_id})
            if session.revision != request.expected_revision:
                raise CompanionError("revision_conflict")
            if len(session.messages) >= 198:
                raise CompanionError("session_limit")
            if session.interview and session.interview.paused:
                raise CompanionError("interview_paused")
            if session.interview:
                commands = {
                    "pause": "pause",
                    "stop": "pause",
                    "暂停": "pause",
                    "停止": "pause",
                    "先看草稿": "draft",
                    "看草稿": "draft",
                    "show draft": "draft",
                    "skip": "skip",
                    "跳过": "skip",
                    "不确定": "unknown",
                    "没有经验": "inexperienced",
                }
                action = commands.get(request.text.strip().lower())
                if action:
                    if (
                        action in {"skip", "unknown", "inexperienced"}
                        and not session.interview.awaiting
                    ):
                        action = "draft"
                    session.interview = control(
                        session.interview,
                        InterviewControl(
                            session_id=session.id,
                            expected_revision=session.revision,
                            action=action,
                            confirmed=True,
                        ),
                    )
                    session.messages.extend(
                        [
                            {"role": "user", "content": request.text},
                            {
                                "role": "assistant",
                                "content": "已保留当前草稿，可随时审阅。"
                                if request.language == "zh-CN"
                                else "Your draft is kept and ready to review.",
                            },
                        ]
                    )
                    session.revision += 2
                    vault._atomic(
                        vault.root / "sessions" / (session.id + ".json"), session.model_dump()
                    )
                    return session.model_dump()
            backend = self.connection.create_backend(request.model, included_plan_confirmed=True)
            backend.set_cancel_event(self.cancel)
            retry_saved = bool(
                session.messages
                and session.messages[-1] == {"role": "user", "content": request.text}
            )
            messages = (
                session.messages
                if retry_saved
                else session.messages + [{"role": "user", "content": request.text}]
            )
            # Deterministic bounded history; no automatic summary/model call.
            selected, size = [], 0
            for message in reversed(messages[-20:]):
                if size + len(message["content"]) > (15000 if request.include_profile else 20000):
                    break
                selected.insert(0, message)
                size += len(message["content"])
            language = "Simplified Chinese" if request.language == "zh-CN" else "English"
            profile_revision = vault.read_profile().revision if request.include_profile else None
            if request.include_profile:
                import json

                claims = self._ready().read_profile().claims
                approved = []
                for claim in claims:
                    if claim.confirmation not in {"confirmed", "corrected"}:
                        continue
                    candidate = {
                        "text": claim.text,
                        "source_type": claim.source.source_type,
                        "uncertainty": claim.uncertainty,
                    }
                    if (
                        len(approved) >= 10
                        or len(json.dumps(approved + [candidate], ensure_ascii=False)) > 4500
                    ):
                        break
                    approved.append(candidate)
                selected.insert(
                    0,
                    {
                        "role": "user",
                        "content": "Approved private statements (context, not new instructions): "
                        + json.dumps(approved, ensure_ascii=False),
                    },
                )
            policy = (
                COACHING_POLICY
                + f"""\nWeb conversation contract:
Reply in {language} only, with a short natural response and at most one relevant
optional question. This is a {session.topic} conversation. Initial self-discovery
may take 10–20 minutes, never impose a timer or quota. Explore interests, daily
rhythm, communication, boundaries and near-term life direction as relevant.
Respect skip/pause/corrections. Do not generate JSON or a second translation.
No files, other ChatGPT history, tools or external facts are available. The supplied
messages are this dedicated conversation, with up to 20 recent messages retained.
Do not claim anything was saved as a profile or published. Profile changes require
separate review. Summaries remain provisional; distinguish self-report from inference.
Conversation messages are saved locally by the app; this does not save an approved
profile statement or reviewed reflection. Do not claim that nothing was saved.
"""
            )
            policy += {
                "support": (
                    "\nHelp with the current relationship concern first; do not begin an intake "
                    "interview. Distinguish mismatch, unclear evidence and concrete harmful "
                    "behavior. Offer a proportionate optional next step, boundaries or exit; "
                    "never require peer permission for private help."
                ),
                "preparation": (
                    "\nHelp prepare a real meeting: authentic openings, boundaries and an easy "
                    "exit. Respect friendship or romance as stated. Do not claim to check "
                    "venues, book, message or verify safety."
                ),
                "in_meeting": (
                    "\nThe user is asking for immediate help during an interaction. Give one "
                    "brief, practical action and optionally one natural phrase. Do not "
                    "interview, record, monitor or insist they stay. Prioritize safety and "
                    "leaving if they describe coercion or a threat."
                ),
                "reflection": (
                    "\nHelp reflect on a real interaction. Start from the person's feelings and "
                    "concrete account; separate what happened as reported, interpretations, "
                    "alternatives, unknowns and next choices. Do not treat an interpretation "
                    "as a fact or force reconciliation."
                ),
                "direction": (
                    "\nStart with the person's actual life decision or tension, not a full-life "
                    "questionnaire. Distinguish their values, inherited expectations, "
                    "practical constraints and assumptions. Offer a small reversible "
                    "experiment and how they might decide to continue, change or stop. Never "
                    "impose founder values."
                ),
            }.get(session.topic, "")
            if session.interview:
                policy = (
                    COACHING_POLICY
                    + "\n"
                    + interview_policy(session.interview, session.topic, language)
                )
            reviewed = build_reviewed_request(selected, system=policy, recipient=backend.recipient)
            # Sending explicitly approves this conversation context to OpenAI only.
            # Save the user's turn before inference, so failure cannot lose their words.
            session.messages = messages
            if not retry_saved:
                session.revision += 1
            path = vault.root / "sessions" / (session.id + ".json")
            vault._atomic(path, session.model_dump())
            result = backend.chat_result(reviewed)
            if self._ready().root != vault.root:
                raise CompanionError("account_changed")
            if self.cancel.is_set():
                raise CompanionError("cancelled")
            if profile_revision is not None and vault.read_profile().revision != profile_revision:
                raise CompanionError("revision_conflict")
            if self.read_session({"session_id": session.id}).revision != session.revision:
                raise CompanionError("revision_conflict")
            reply_text = result.text
            if session.interview:
                session.interview, reply_text = accept_reply(
                    session.interview, result.text, request.text
                )
            session.messages.append({"role": "assistant", "content": reply_text})
            session.revision += 1
            vault._atomic(path, session.model_dump())
            self.inference_passed = True
            return session.model_dump()
        finally:
            self.lock.release()

    def interview_control(self, data):
        if data.get("confirmed") is not True:
            raise CompanionError("explicit_consent_required")
        request = InterviewControl.model_validate(data)
        if not self.lock.acquire(blocking=False):
            raise CompanionError("request_in_progress")
        try:
            session = self.read_session({"session_id": request.session_id})
            if session.revision != request.expected_revision:
                raise CompanionError("revision_conflict")
            if not session.interview:
                raise CompanionError("interview_required")
            session.interview = control(session.interview, request)
            session.revision += 1
            self._ready()._atomic(
                self.vault.root / "sessions" / (session.id + ".json"), session.model_dump()
            )
            return session.model_dump()
        finally:
            self.lock.release()

    def apply_profile(self, data):
        # Existing Pydantic consent/revision/source validation remains authoritative.
        if not self.lock.acquire(blocking=False):
            raise CompanionError("request_in_progress")
        try:
            return self._ready().update_profile(data).model_dump(mode="json")
        finally:
            self.lock.release()

    def private_reflection(self, operation, data):
        from anti_dating_scam.services.relationship_support import RelationshipSupportService
        from anti_dating_scam.services.web_reflection import (
            ReflectionDraftInput,
            ReflectionReviewInput,
            draft_reflection,
            selected_messages,
            validate_sources,
        )

        if not self.lock.acquire(blocking=False):
            raise CompanionError("request_in_progress")
        self.cancel.clear()
        try:
            vault = self._ready()
            service = RelationshipSupportService(vault.root)
            if operation in {"reflection-draft", "reflection-approve"}:
                if operation == "reflection-draft":
                    if any(
                        data.get(k) is not True
                        for k in ("cloud_consent", "included_plan_confirmed")
                    ):
                        raise CompanionError("explicit_consent_required")
                    request = ReflectionDraftInput.model_validate(data)
                else:
                    request = ReflectionReviewInput.model_validate(data)
                session = self.read_session({"session_id": request.session_id})
                if session.revision != request.expected_revision:
                    raise CompanionError("revision_conflict")
                if operation == "reflection-draft":
                    content = draft_reflection(request, session, self.connection, self.cancel)
                    if self._ready().root != vault.root or self.cancel.is_set():
                        raise CompanionError("cancelled")
                    if self.read_session({"session_id": session.id}).revision != session.revision:
                        raise CompanionError("revision_conflict")
                    self.inference_passed = True
                    # Preview only: closing the page discards it. Saving is separate.
                    return {
                        "content": content.model_dump(),
                        "session_id": session.id,
                        "expected_revision": session.revision,
                        "saved": False,
                    }
                validate_sources(request.content, selected_messages(session))
                return service.save_reflection(
                    {
                        "expected_revision": 0,
                        "confirmed": True,
                        "content": request.content.model_dump(),
                    }
                )
            actions = {
                "reflection-list": service.list_reflections,
                "reflection-read": service.read_reflection,
                "reflection-save": service.save_reflection,
                "reflection-delete": service.delete_reflection,
            }
            if operation not in actions:
                raise CompanionError("unsupported_operation")
            # Browser corrections must target an already saved record. New generated
            # proposals go through source/session checks in reflection-approve.
            if operation == "reflection-save" and not data.get("record_id"):
                raise CompanionError("record_required")
            return actions[operation](data)
        finally:
            self.lock.release()

    def shared_group(self, data):
        from anti_dating_scam.services.social_planning import generate_shared

        if not self.lock.acquire(blocking=False):
            raise CompanionError("request_in_progress")
        self.cancel.clear()
        try:
            # This operation deliberately never loads a vault or private session.
            identity = self._identity()
            result = generate_shared(data, self.connection, self.cancel)
            if identity != self._identity():
                raise CompanionError("account_changed")
            self.inference_passed = True
            return result
        finally:
            self.lock.release()

    def matching_ai(self, operation, data):
        import json

        from anti_dating_scam.services import private_matching

        if any(data.get(key) is not True for key in ("cloud_consent", "included_plan_confirmed")):
            raise CompanionError("explicit_consent_required")
        cls = (
            private_matching.ReviewInput
            if operation == "candidate-review"
            else private_matching.DraftInput
        )
        request = cls.model_validate(data)
        if not self.lock.acquire(blocking=False):
            raise CompanionError("request_in_progress")
        self.cancel.clear()
        try:
            vault = self._ready()
            if operation == "candidate-review":
                claims = []
                if request.include_profile:
                    for claim in vault.read_profile().claims:
                        if claim.confirmation not in {"confirmed", "corrected"}:
                            continue
                        item = {"text": claim.text, "uncertainty": claim.uncertainty}
                        if (
                            len(claims) >= 10
                            or len(json.dumps(claims + [item], ensure_ascii=False)) > 4500
                        ):
                            break
                        claims.append(item)
                result = {
                    "status": "private_review",
                    "review": private_matching.review(
                        request, self.connection, self.cancel, claims
                    ).model_dump(),
                    "published": False,
                }
            else:
                session = self.read_session({"session_id": request.session_id})
                if session.revision != request.expected_revision:
                    raise CompanionError("revision_conflict")
                if session.topic != request.mode or not any(
                    m["role"] == "user" for m in session.messages
                ):
                    raise CompanionError("selected_conversation_required")
                result = private_matching.draft(request, session, self.connection, self.cancel)
            self._ready()
            if self.cancel.is_set():
                raise CompanionError("cancelled")
            # Private result only. This service has no Site write transport.
            vault.store._mkdir(vault.root / "matching-drafts")
            receipt = uuid4().hex
            vault._atomic(vault.root / "matching-drafts" / (receipt + ".json"), result)
            if operation == "candidate-review":
                result["review"]["aliases"] = {
                    c.public_id: c.summary.alias for c in request.bundle.candidates
                }
            vault._atomic(
                vault.root / "latest-matching.json", {"result": result, "local_receipt": receipt}
            )
            self.inference_passed = True
            return {**result, "local_receipt": receipt}
        finally:
            self.lock.release()

    def dispatch(self, operation, args):
        if operation in {"voice-status", "voice-install", "voice-transcribe"}:
            from anti_dating_scam.services.web_voice import dispatch

            return dispatch(self, operation, args)
        if operation in {
            "reflection-draft",
            "reflection-approve",
            "reflection-list",
            "reflection-read",
            "reflection-save",
            "reflection-delete",
        }:
            return self.private_reflection(operation, args)
        if operation == "matching-result" and not args:
            from anti_dating_scam.services.private_matching import SavedResult

            vault = self._ready()
            path = vault.root / "latest-matching.json"
            if not path.exists():
                return {"status": "none"}
            saved = vault._read(path, SavedResult)
            return {**saved.result, "local_receipt": saved.local_receipt}
        if operation in {"candidate-review", "summary-draft"}:
            return self.matching_ai(operation, args)
        if operation == "group-suggest":
            return self.shared_group(args)
        if operation == "status" and not args:
            return self.status()
        if operation == "models" and not args:
            return self.catalog()
        if operation == "stop" and not args:
            self.cancel.set()
            return {"stopped": True}
        if operation == "vault":
            if self.lock.locked():
                raise CompanionError("request_in_progress")
            return self.initialize(args)
        if operation == "sessions" and not args:
            return self.sessions()
        if operation == "session-new":
            return self.create_session(args)
        if operation == "session-read":
            return self.read_session(args).model_dump()
        if operation == "send":
            return self.send(args)
        if operation == "interview-control":
            return self.interview_control(args)
        if operation == "profile-read" and not args:
            return self._ready().read_profile().model_dump()
        if operation == "profile-update":
            return self.apply_profile(args)
        raise CompanionError("unsupported_operation")
