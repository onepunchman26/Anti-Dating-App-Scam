"""Explicit, editable disclosure review shared by application clients."""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from anti_dating_scam.ai.privacy import ChatMessage, ChatRequest, build_reviewed_request


class DisclosureChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    recipient: str = Field(min_length=1, max_length=2048)
    instructions_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)
    reviewed: bool = False


class DisclosureReviewRequired(Exception):
    def __init__(self, preview: dict[str, Any]) -> None:
        super().__init__("Review the exact data before sending to an external AI.")
        self.preview = preview


def chat_with_review(
    backend: Any,
    messages: list[dict[str, str]],
    *,
    system: str,
    disclosure: DisclosureChoice | None = None,
    response_schema: dict | None = None,
) -> str:
    """Local adapters enforce loopback; remote adapters only receive reviewed data.

    Approval never includes an implicit promise that text is anonymized. The user
    edits the payload and sees the destination and instructions before approving.
    """
    recipient = getattr(backend, "recipient", "")
    remote = bool(recipient) and not isinstance_local(backend)
    if not remote:
        if response_schema is not None and isinstance_local(backend):
            return backend.chat(
                ChatRequest(
                    messages=messages,
                    system=system,
                    response_schema=response_schema,
                )
            )
        return backend.chat(messages, system=system)
    instruction_hash = hashlib.sha256(system.encode("utf-8")).hexdigest()
    if (
        disclosure is None
        or not disclosure.reviewed
        or disclosure.recipient != recipient
        or disclosure.instructions_hash != instruction_hash
    ):
        raise DisclosureReviewRequired(
            {
                "code": "disclosure_review_required",
                "recipient": recipient,
                "instructions": system,
                "instructions_hash": instruction_hash,
                "messages": messages,
            }
        )
    request = build_reviewed_request(
        [message.model_dump() for message in disclosure.messages],
        system=system,
        recipient=recipient,
    )
    return backend.chat(request)


def isinstance_local(backend: Any) -> bool:
    # Import lazily to keep transport dependencies outside this service.
    from anti_dating_scam.ai.chat_backends import OllamaChatBackend

    return isinstance(backend, OllamaChatBackend)
