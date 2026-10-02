"""Opt-in, three bounded synthetic service calls through the existing ChatGPT-plan adapter."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionService
from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.matchmaking.peer_coordinator import PeerCoordinator
from anti_dating_scam.matchmaking.peer_models import (
    AdultDeclaration,
    Attribute,
    InviteAction,
    InviteCreate,
    MatchingProfile,
    ProfileUpdate,
    Registration,
)
from anti_dating_scam.services.dating_introduction import IntroductionFormat, IntroductionService
from anti_dating_scam.services.peer_ai import comparison_request, generate_comparison


class ReceiptBackend:
    def __init__(self, backend):
        self.backend = backend
        self.recipient = backend.recipient
        self.provenance = None

    def chat_result(self, request):
        result = self.backend.chat_result(request)
        self.provenance = result.provenance
        return result


def reviewed(backend, request):
    return build_reviewed_request(
        request.messages, system=request.system, recipient=backend.recipient
    ).model_copy(
        update={"response_schema": request.response_schema, "allow_schema_fallback": False}
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-included-plan", action="store_true")
    parser.add_argument("--model", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--cases", choices=["all", "introductions"], default="all")
    args = parser.parse_args()
    if not args.confirm_included_plan:
        parser.error("Explicit confirmation that extra credits are disabled is required.")
    if args.receipt.exists():
        parser.error("Receipt already exists; preserve prior evidence.")
    connection = ChatGPTConnectionService()
    if args.model not in {m.slug for m in connection.list_models()}:
        raise ValueError("Model unavailable in account catalog.")
    backend = ReceiptBackend(connection.create_backend(args.model, included_plan_confirmed=True))
    receipt = {
        "at": datetime.now(UTC).isoformat(),
        "synthetic_only": True,
        "automatic_retries": 0,
        "public_deployment": False,
        "calls": [],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)

    def save(case, callback):
        backend.provenance = None
        try:
            output = callback()
            entry = {"case": case, "service_accepted": True, "output": output.model_dump()}
        except Exception as exc:
            # Only a stable category; never raw network output, identity or credential.
            entry = {"case": case, "service_accepted": False, "error_type": type(exc).__name__}
        if backend.provenance:
            entry["provenance"] = backend.provenance.model_dump(exclude={"response_id"})
            entry["model_agreement"] = backend.provenance.model_agreement
        receipt["calls"].append(entry)
        args.receipt.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(case + ": " + ("accepted" if entry["service_accepted"] else "failed"), flush=True)

    with tempfile.TemporaryDirectory(prefix="slowmatch-synthetic-peer-") as sandbox:
        root = Path(sandbox)
        intro = IntroductionService(root / "synthetic")
        memory = intro.memory
        for text in (
            "I enjoy reading and cooking.",
            "I value direct and considerate communication.",
        ):
            memory.change(memory.read().revision, action="add", text=text, confirmed=True)
        memory.change(memory.read().revision, action="enable", confirmed=True)
        adult = AdultDeclaration(age=30, adult_confirmed=True)
        ids = [s["id"] for s in intro.list_sources(adult)]
        for language in ("en", "zh"):
            request = intro.prepare(
                adult, ids, [], IntroductionFormat(language=language, max_chars=350)
            )

            def generate(request=request):
                draft = intro.generate(backend, reviewed(backend, request))
                if not any(field.text.strip() for field in draft.fields):
                    raise ValueError("Empty draft despite sufficient synthetic facts.")
                return draft

            save("introduction_" + language, generate)
        if args.cases == "introductions":
            return 0 if all(c["service_accepted"] for c in receipt["calls"]) else 1
        node = PeerCoordinator(root / "node")
        members = []
        for alias, pace in [("Synthetic A", "slow"), ("Synthetic B", "steady")]:
            person = node.register(Registration(alias=alias, age=30, adult_confirmed=True))
            profile = MatchingProfile(
                alias=alias,
                age=30,
                adult_confirmed=True,
                city="Toronto",
                areas=["Toronto"],
                process_matching=True,
                attributes={
                    "intention": Attribute(values=["long_term"], disclose=True),
                    "communication": Attribute(values=["direct"], disclose=True),
                    "pace": Attribute(values=[pace], disclose=True),
                    "smoking": Attribute(values=["no"], disclose=False),
                },
            )
            node.update_profile(
                person["token"], ProfileUpdate(expected_version=0, profile=profile, approved=True)
            )
            members.append(person)
        a, b = members
        invite = node.create_invitation(a["token"], InviteCreate(request_id=uuid4().hex))[
            "invitation"
        ]
        node.act(b["token"], InviteAction(invitation=invite, action="claim"))
        versions = node.preview_pair(a["token"], invite)["versions"]
        for person in members:
            node.act(
                person["token"],
                InviteAction(
                    invitation=invite,
                    action="approve",
                    allow_cloud_ai=True,
                    expected_versions=versions,
                ),
            )
        prepared = node.prepare_comparison(a["token"], invite)
        request = comparison_request(prepared)

        def compare():
            result = generate_comparison(backend, prepared, reviewed(backend, request))
            node.finish_comparison(a["token"], invite, prepared["ticket"], result)
            assert node.read_comparison(a["token"], invite)["report"] == result.model_dump()
            node.control(b["token"], "withdraw")
            try:
                node.read_comparison(a["token"], invite)
            except ValueError:
                pass
            else:
                raise AssertionError("Revoked result remained readable.")
            return result

        save("peer_comparison_private_cache_and_withdraw", compare)
    return 0 if all(c["service_accepted"] for c in receipt["calls"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
