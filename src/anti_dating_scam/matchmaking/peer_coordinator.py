"""Persistent extension of the rendezvous node for approved adult snapshots.

The private personal model never enters this store. A single encrypted state row
uses SQLite transactions to serialize permissions, revisions and invitation claims.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from anti_dating_scam.matchmaking.peer_models import (
    InviteAction,
    InviteCreate,
    MatchingProfile,
    PeerReport,
    ProfileUpdate,
    PublicUpdate,
    Registration,
)
from anti_dating_scam.services.report_review import ReportReviewService


class PeerError(ValueError):
    """Stable safe code, never private content, credentials or a provider response."""


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def _area(value):
    return " ".join(value.casefold().split())


class PeerCoordinator:
    def __init__(self, directory: Path, *, key: bytes | None = None, clock=time.time):
        self.directory = Path(directory).absolute()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.guard = ReportReviewService(self.directory)
        self.guard._check(self.directory, directory=True)
        self.clock = clock
        if key is None:
            from anti_dating_scam.ai.chatgpt_credentials import WindowsDPAPIProtector

            protector = WindowsDPAPIProtector()
            path = self.directory / "coordinator.key"
            try:
                protected = self.guard._read(path, 8192)
            except FileNotFoundError:
                proposed = AESGCM.generate_key(bit_length=256)
                try:
                    self.guard._write_new(path, protector.protect(proposed))
                except FileExistsError:
                    pass
                protected = self.guard._read(path, 8192)
            key = protector.unprotect(protected)
        self.cipher = AESGCM(key)
        self.database = self.directory / "approved-matching.sqlite3"
        if self.database.exists():
            self.guard._check(self.database, directory=False)
        with closing(self._connection()) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, data BLOB)"
            )
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT data FROM state WHERE id=1").fetchone() is None:
                connection.execute(
                    "INSERT INTO state VALUES (1,?)",
                    (
                        self._encode(
                            {
                                "users": {},
                                "invitations": {},
                                "blocks": [],
                                "declines": [],
                            }
                        ),
                    ),
                )
            connection.commit()

    def _connection(self):
        if self.database.exists():
            self.guard._check(self.database, directory=False)
        connection = sqlite3.connect(self.database, timeout=5, isolation_level=None)
        connection.execute("PRAGMA secure_delete=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        return connection

    def _encode(self, state):
        raw = json.dumps(state, ensure_ascii=False, separators=(",", ":")).encode()
        if len(raw) > 2_000_000:
            raise PeerError("capacity")
        nonce = os.urandom(12)
        return nonce + self.cipher.encrypt(nonce, raw, b"slowmatch-peer-v1")

    @contextmanager
    def transaction(self):
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            raw = connection.execute("SELECT data FROM state WHERE id=1").fetchone()[0]
            state = json.loads(self.cipher.decrypt(raw[:12], raw[12:], b"slowmatch-peer-v1"))
            yield state
            connection.execute("UPDATE state SET data=? WHERE id=1", (self._encode(state),))
            connection.commit()
        finally:
            connection.close()

    def _actor(self, state, token):
        if not isinstance(token, str) or not 40 <= len(token) <= 128:
            raise PeerError("unauthorized")
        hashed = hashlib.sha256(token.encode()).hexdigest()
        actor = next(
            (u for u in state["users"].values() if secrets.compare_digest(u["token_hash"], hashed)),
            None,
        )
        if actor is None or not actor["eligible"]:
            raise PeerError("unauthorized")
        return actor

    def register(self, request: Registration):
        request = Registration.model_validate(request.model_dump())
        with self.transaction() as state:
            if len(state["users"]) >= 1000:
                raise PeerError("capacity")
            token = secrets.token_urlsafe(32)
            identity = uuid4().hex
            state["users"][identity] = {
                "id": identity,
                "alias": request.alias,
                "age": request.age,
                "eligible": True,
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                "version": 0,
                "profile": None,
                "public": "",
                "public_alias": "",
                "public_version": 0,
                "public_enabled": False,
                "next_run": 0,
                "last_run": None,
                "last_fingerprint": "",
                "notice": False,
            }
            return {"member_id": identity, "token": token, "identity": "self_declared_adult"}

    def me(self, token):
        with self.transaction() as state:
            user = self._actor(state, token)
            return {
                k: user[k]
                for k in (
                    "id",
                    "alias",
                    "age",
                    "version",
                    "profile",
                    "public",
                    "public_version",
                    "public_enabled",
                    "last_run",
                    "notice",
                )
            }

    def _invalidate(self, state, identity):
        for invitation in state["invitations"].values():
            if identity in (invitation["owner"], invitation["recipient"]):
                invitation["approvals"] = {}
                invitation["reports"] = {}
                if invitation["status"] in {"ready", "claimed"}:
                    invitation["status"] = "claimed"
        for user in state["users"].values():
            user["notice"] = False

    def update_profile(self, token, request: ProfileUpdate):
        request = ProfileUpdate.model_validate(request.model_dump())
        with self.transaction() as state:
            user = self._actor(state, token)
            if user["version"] != request.expected_version:
                raise PeerError("stale")
            self._invalidate(state, user["id"])
            user["profile"] = request.profile.model_dump()
            user["alias"], user["age"] = request.profile.alias, request.profile.age
            user["version"] += 1
            user["next_run"] = self.clock() + request.profile.automatic_minutes * 60
            return {"version": user["version"]}

    def public_update(self, token, request: PublicUpdate):
        request = PublicUpdate.model_validate(request.model_dump())
        if request.publish and (not request.text.strip() or not request.alias.strip()):
            raise PeerError("empty")
        with self.transaction() as state:
            user = self._actor(state, token)
            if user["public_version"] != request.expected_version:
                raise PeerError("stale")
            user["public"], user["public_enabled"] = request.text, request.publish
            user["public_alias"] = request.alias if request.publish else ""
            user["public_version"] += 1
            return {"public_version": user["public_version"], "member_id": user["id"]}

    def public_read(self, identity):
        with self.transaction() as state:
            user = state["users"].get(identity)
            if not user or not user["eligible"] or not user["public_enabled"]:
                raise PeerError("unavailable")
            return {
                "alias": user["public_alias"],
                "text": user["public"],
                "version": user["public_version"],
            }

    @staticmethod
    def _pair(a, b):
        return sorted([a, b])

    def _blocked(self, state, a, b):
        pair = self._pair(a, b)
        return pair in state["blocks"] or pair in state["declines"]

    @staticmethod
    def _profile(user):
        if not user["eligible"] or not user["profile"]:
            raise PeerError("profile_required")
        profile = MatchingProfile.model_validate(user["profile"])
        if not profile.process_matching:
            raise PeerError("consent_required")
        return profile

    def _eligible_pair(self, state, a, b, *, discovery):
        if a["id"] == b["id"] or self._blocked(state, a["id"], b["id"]):
            return False
        try:
            first, second = self._profile(a), self._profile(b)
        except PeerError:
            return False
        if discovery and not (first.discoverable and second.discoverable):
            return False
        for own, other in ((first, second), (second, first)):
            if not own.age_min <= other.age <= own.age_max:
                return False
            if _area(other.city) not in {_area(v) for v in own.areas}:
                return False
            for field, accepted in own.required.items():
                supplied = other.attributes.get(field)
                if supplied is None or not set(accepted) & set(supplied.values):
                    return False
        return True

    def _visible(self, user):
        profile = self._profile(user)
        return {
            "member_id": user["id"],
            "alias": user["alias"],
            "version": user["version"],
            "city": profile.city if profile.show_city else None,
            "attributes": {k: v.values for k, v in profile.attributes.items() if v.disclose},
        }

    def _discover(self, state, user, *, authorized_only=False):
        profile = self._profile(user)
        allowed = None
        if authorized_only:
            allowed = set()
            for invite in state["invitations"].values():
                try:
                    a, b = self._ready(state, user, invite)
                    allowed.add(b["id"] if a["id"] == user["id"] else a["id"])
                except PeerError:
                    pass
        ranked, unranked = [], []
        for other in state["users"].values():
            if allowed is not None and other["id"] not in allowed:
                continue
            if not self._eligible_pair(state, user, other, discovery=not authorized_only):
                continue
            visible = self._visible(other)
            own_visible = self._visible(user)["attributes"]
            alignment, differences, missing, order = [], [], [], []
            for field in profile.priorities:
                own, theirs = own_visible.get(field), visible["attributes"].get(field)
                if not own or not theirs:
                    missing.append(field)
                    order.append(0)
                elif set(own) & set(theirs):
                    alignment.append(field)
                    order.append(2)
                else:
                    differences.append(field)
                    order.append(1)
            visible.update({"alignment": alignment, "differences": differences, "missing": missing})
            if len(alignment) + len(differences) >= 2:
                ranked.append((tuple(order), visible))
            else:
                visible["order"] = None
                unranked.append(visible)
        ranked.sort(key=lambda pair: (tuple(-n for n in pair[0]), pair[1]["member_id"]))
        output = []
        previous = None
        for index, (order, row) in enumerate(ranked):
            if order != previous:
                position = index + 1
            row["order"] = position
            previous = order
            output.append(row)
        output += sorted(unranked, key=lambda row: row["member_id"])
        return {
            "candidates": output[:20],
            "eligible_count": len(output),
            "limited": len(output) > 20,
            "priorities": profile.priorities,
            "method": "private_stated_priority_order_v1",
        }

    def discover(self, token, *, authorized_only=False):
        with self.transaction() as state:
            user = self._actor(state, token)
            user["notice"] = False
            return self._discover(state, user, authorized_only=authorized_only)

    def create_invitation(self, token, request: InviteCreate):
        request = InviteCreate.model_validate(request.model_dump())
        with self.transaction() as state:
            user = self._actor(state, token)
            self._profile(user)
            for invite in state["invitations"].values():
                if invite["owner"] == user["id"] and invite["request_id"] == request.request_id:
                    return self._invitation_view(state, user, invite)
            if sum(i["owner"] == user["id"] for i in state["invitations"].values()) >= 100:
                raise PeerError("capacity")
            if request.intended_member:
                target = state["users"].get(request.intended_member)
                if not target or not self._eligible_pair(state, user, target, discovery=True):
                    raise PeerError("unavailable")
            identity = secrets.token_urlsafe(32)
            invitation = {
                "id": identity,
                "owner": user["id"],
                "recipient": None,
                "intended": request.intended_member,
                "request_id": request.request_id,
                "expires": self.clock() + request.hours * 3600,
                "status": "pending",
                "approvals": {},
                "reports": {},
            }
            state["invitations"][identity] = invitation
            return self._invitation_view(state, user, invitation)

    def _status(self, invitation):
        if invitation["status"] in {"revoked", "declined"}:
            return invitation["status"]
        return "expired" if invitation["expires"] <= self.clock() else invitation["status"]

    def _invitation_view(self, state, user, invitation):
        return {
            "invitation": invitation["id"],
            "status": self._status(invitation),
            "expires": invitation["expires"],
            "owner": invitation["owner"],
            "recipient": invitation["recipient"],
            "counterpart_alias": next(
                (
                    state["users"][identity]["alias"]
                    for identity in (invitation["owner"], invitation["recipient"])
                    if identity and identity != user["id"] and identity in state["users"]
                ),
                None,
            ),
            "approved_by_me": user["id"] in invitation["approvals"],
        }

    def invitations(self, token):
        with self.transaction() as state:
            user = self._actor(state, token)
            return {
                "invitations": [
                    self._invitation_view(state, user, i)
                    for i in state["invitations"].values()
                    if user["id"] in (i["owner"], i["recipient"])
                ]
            }

    def act(self, token, request: InviteAction):
        request = InviteAction.model_validate(request.model_dump())
        with self.transaction() as state:
            user = self._actor(state, token)
            invitation = state["invitations"].get(request.invitation)
            if invitation is None:
                raise PeerError("unavailable")
            participant = user["id"] in (invitation["owner"], invitation["recipient"])
            if request.action == "revoke":
                if not participant:
                    raise PeerError("unauthorized")
                invitation.update(status="revoked", approvals={}, reports={})
                return self._invitation_view(state, user, invitation)
            status = self._status(invitation)
            if status in {"expired", "revoked", "declined"}:
                raise PeerError(status)
            owner = state["users"].get(invitation["owner"])
            if owner is None or not owner["eligible"]:
                raise PeerError("unavailable")
            if request.action == "claim":
                if invitation["recipient"] == user["id"]:
                    return self._invitation_view(state, user, invitation)
                if invitation["recipient"] is not None:
                    raise PeerError("already_used")
                if invitation["intended"] and invitation["intended"] != user["id"]:
                    raise PeerError("wrong_recipient")
                if not self._eligible_pair(state, owner, user, discovery=False):
                    raise PeerError("unavailable")
                invitation["recipient"] = user["id"]
                invitation["status"] = "claimed"
            elif request.action == "decline":
                if not participant:
                    raise PeerError("unauthorized")
                invitation.update(status="declined", approvals={}, reports={})
                if invitation["recipient"]:
                    pair = self._pair(invitation["owner"], invitation["recipient"])
                    if pair not in state["declines"]:
                        state["declines"].append(pair)
            elif request.action == "approve":
                if not participant or not invitation["recipient"]:
                    raise PeerError("recipient_confirmation_required")
                recipient = state["users"].get(invitation["recipient"])
                if not recipient or not self._eligible_pair(
                    state, owner, recipient, discovery=False
                ):
                    raise PeerError("unavailable")
                versions = {owner["id"]: owner["version"], recipient["id"]: recipient["version"]}
                if request.expected_versions != versions:
                    raise PeerError("stale")
                consent = {"versions": versions, "cloud": request.allow_cloud_ai}
                if invitation["approvals"].get(user["id"]) == consent:
                    return self._invitation_view(state, user, invitation)
                invitation["approvals"][user["id"]] = {
                    "versions": versions,
                    "cloud": request.allow_cloud_ai,
                }
                invitation["reports"] = {}
                invitation["status"] = "ready" if len(invitation["approvals"]) == 2 else "claimed"
            return self._invitation_view(state, user, invitation)

    def _ready(self, state, user, invitation, *, cloud=False):
        if self._status(invitation) != "ready" or user["id"] not in (
            invitation["owner"],
            invitation["recipient"],
        ):
            raise PeerError("consent_required")
        first, second = (state["users"].get(invitation[k]) for k in ("owner", "recipient"))
        if (
            not first
            or not second
            or not self._eligible_pair(state, first, second, discovery=False)
        ):
            raise PeerError("unavailable")
        versions = {first["id"]: first["version"], second["id"]: second["version"]}
        if set(invitation["approvals"]) != set(versions) or any(
            consent["versions"] != versions or (cloud and not consent["cloud"])
            for consent in invitation["approvals"].values()
        ):
            raise PeerError("consent_required")
        return first, second

    def _comparison(self, state, user, invitation):
        first, second = self._ready(state, user, invitation, cloud=True)
        sources = []
        for label, person in (("A", first), ("B", second)):
            for index, (field, values) in enumerate(self._visible(person)["attributes"].items()):
                sources.append(
                    {"id": f"{label}{index:02}", "field": field, "text": ", ".join(values)}
                )
        # Hidden attributes, hard settings, age, city, aliases and account IDs never go to AI.
        shared = set(self._visible(first)["attributes"]) & set(self._visible(second)["attributes"])
        priorities = [k for k in self._profile(user).priorities if k in shared]
        ticket = _digest(
            [invitation["id"], user["id"], invitation["approvals"], sources, priorities]
        )
        return {
            "ticket": ticket,
            "sources": sources,
            "basis": "participant_approved_self_reports; not verified behavior",
            "priorities": priorities,
        }

    def prepare_comparison(self, token, identity):
        with self.transaction() as state:
            user = self._actor(state, token)
            invitation = state["invitations"].get(identity)
            if not invitation:
                raise PeerError("unavailable")
            return self._comparison(state, user, invitation)

    def preview_pair(self, token, identity):
        with self.transaction() as state:
            user = self._actor(state, token)
            invitation = state["invitations"].get(identity)
            if (
                not invitation
                or self._status(invitation) not in {"claimed", "ready"}
                or user["id"] not in (invitation["owner"], invitation["recipient"])
            ):
                raise PeerError("unavailable")
            first, second = (state["users"].get(invitation[k]) for k in ("owner", "recipient"))
            if (
                not first
                or not second
                or not self._eligible_pair(state, first, second, discovery=False)
            ):
                raise PeerError("unavailable")
            return {
                "participants": [self._visible(first), self._visible(second)],
                "versions": {first["id"]: first["version"], second["id"]: second["version"]},
            }

    def finish_comparison(self, token, identity, ticket, report):
        from anti_dating_scam.services.peer_ai import validate_report

        with self.transaction() as state:
            user = self._actor(state, token)
            invitation = state["invitations"].get(identity)
            if not invitation:
                raise PeerError("unavailable")
            prepared = self._comparison(state, user, invitation)
            if ticket != prepared["ticket"]:
                raise PeerError("stale")
            report = PeerReport.model_validate(report)
            validate_report(report, prepared["sources"])
            # Private result for this viewer, never the other participant's ranking/report.
            invitation["reports"][user["id"]] = {"ticket": ticket, "report": report.model_dump()}
            return {"saved": True}

    def read_comparison(self, token, identity):
        with self.transaction() as state:
            user = self._actor(state, token)
            invitation = state["invitations"].get(identity)
            if not invitation:
                raise PeerError("unavailable")
            prepared = self._comparison(state, user, invitation)
            saved = invitation["reports"].get(user["id"])
            if not saved or saved["ticket"] != prepared["ticket"]:
                raise PeerError("no_current_result")
            return saved

    def control(self, token, action, target=None):
        with self.transaction() as state:
            user = self._actor(state, token)
            if action == "block":
                if target not in state["users"] or target == user["id"]:
                    raise PeerError("unavailable")
                pair = self._pair(user["id"], target)
                if pair not in state["blocks"]:
                    state["blocks"].append(pair)
                self._invalidate(state, user["id"])
            elif action == "pause":
                if user["profile"]:
                    user["profile"]["discoverable"] = False
                    user["profile"]["automatic_minutes"] = 0
                    user["version"] += 1
                self._invalidate(state, user["id"])
            elif action == "withdraw":
                if user["profile"]:
                    user["profile"].update(
                        process_matching=False, discoverable=False, automatic_minutes=0
                    )
                    user["version"] += 1
                self._invalidate(state, user["id"])
            elif action == "delete":
                identity = user["id"]
                state["invitations"] = {
                    k: v
                    for k, v in state["invitations"].items()
                    if identity not in (v["owner"], v["recipient"], v["intended"])
                }
                for key in ("blocks", "declines"):
                    state[key] = [pair for pair in state[key] if identity not in pair]
                del state["users"][identity]
                for other in state["users"].values():
                    other["notice"] = False
            else:
                raise PeerError("unsupported_action")
            return {"done": True}

    def run_due(self):
        """One bounded local worker tick; no AI requests, invitations or email."""
        completed = 0
        with self.transaction() as state:
            for user in state["users"].values():
                if completed >= 20 or not user["profile"]:
                    continue
                profile = MatchingProfile.model_validate(user["profile"])
                if not (
                    profile.discoverable
                    and profile.process_matching
                    and profile.automatic_minutes
                    and user["next_run"] <= self.clock()
                ):
                    continue
                result = self._discover(state, user)
                fingerprint = _digest(result)
                user["notice"] = bool(
                    profile.notifications
                    and (
                        user["notice"]
                        or (result["candidates"] and fingerprint != user["last_fingerprint"])
                    )
                )
                user["last_fingerprint"] = fingerprint
                user["last_run"] = self.clock()
                user["next_run"] = self.clock() + profile.automatic_minutes * 60
                completed += 1
        return completed
