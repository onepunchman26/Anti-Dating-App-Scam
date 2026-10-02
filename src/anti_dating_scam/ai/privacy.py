"""Provider-neutral, UI-independent boundaries for connected chat.

External providers receive an explicitly reviewed summary, never an implicit copy
of a vault or conversation. This is a disclosure boundary, not a claim that a
regular expression can reliably anonymize arbitrary personal text.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class BackendError(RuntimeError):
    """Safe to display; never include provider output, prompts or credentials."""

    def __init__(self, message: str, *, category: str = "unknown"):
        super().__init__(message)
        self.category = category

    @property
    def public_detail(self) -> str:
        return {
            "usage": (
                "ChatGPT usage limit reached. Review Manage usage; no retry was made. / "
                "ChatGPT 套餐额度已用完，请检查用量设置；未自动重试。"
            ),
            "auth": ("Reconnect ChatGPT to continue. / 请重新连接 ChatGPT 后继续。"),
            "model": ("Model unavailable; choose again. / 所选模型不可用，请重新选择。"),
            "timeout": (
                "ChatGPT took too long. Your words are kept; retry when ready. / "
                "ChatGPT 等待超时，你的话语已保留，可自行重试。"
            ),
            "cancelled": (
                "Request stopped locally; late replies are discarded. / "
                "请求已在本机停止，迟到回复将被丢弃。"
            ),
            "network": (
                "ChatGPT could not be reached. Your connection is kept; no retry was made. / "
                "暂时无法访问 ChatGPT，授权已保留；未自动重试。"
            ),
        }.get(self.category, "")


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=128_000)


def disclosure_fingerprint(
    messages: list[ChatMessage] | tuple[ChatMessage, ...], system: str, recipient: str
) -> str:
    """Bind approval to the exact instructions, minimized content and recipient."""
    body = json.dumps(
        {
            "messages": [item.model_dump() for item in messages],
            "system": system,
            "recipient": recipient,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class ReviewedDisclosure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    recipient: str = Field(min_length=1, max_length=2048)
    messages: tuple[ChatMessage, ...] = Field(min_length=1, max_length=100)
    reviewed: Literal[True]
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def bounded_summary(self) -> ReviewedDisclosure:
        if sum(len(message.content) for message in self.messages) > 24_000:
            raise ValueError("External disclosure must be a summary of at most 24000 characters.")
        return self


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    messages: tuple[ChatMessage, ...] = Field(min_length=1, max_length=200)
    # Application-owned instructions only. Imported text belongs in messages.
    system: str = Field(default="", max_length=64_000)
    privacy_mode: Literal["local_only", "reviewed_remote"] = "local_only"
    disclosure: ReviewedDisclosure | None = None
    # Application-owned structured output contract; currently supported by local Ollama.
    response_schema: dict[str, Any] | None = None
    # Exact-reviewed workflows may forbid an additional request in JSON syntax mode.
    # Keep compatibility for ordinary chat callers; never coerce consent-like values.
    allow_schema_fallback: bool = Field(default=True, strict=True)

    @model_validator(mode="after")
    def bounded_request(self) -> ChatRequest:
        if sum(len(message.content) for message in self.messages) > 256_000:
            raise ValueError("Conversation is too large; select a smaller excerpt.")
        if self.response_schema is not None:
            encoded = json.dumps(self.response_schema, allow_nan=False)
            if len(encoded) > 64_000:
                raise ValueError("The response schema exceeds the allowed size.")
        return self


def coerce_request(
    messages: ChatRequest | list[dict[str, str]], system: str | None = None
) -> ChatRequest:
    if isinstance(messages, ChatRequest):
        if system is not None:
            raise BackendError("Typed requests already contain their instructions.")
        # Revalidate in case an untrusted caller bypassed Pydantic construction.
        # Serialization warnings can echo malformed caller-supplied values. The
        # explicit validation below rejects them without printing private data.
        candidate = messages.model_dump(warnings=False)
    else:
        candidate = {"messages": messages, "system": system or ""}
    try:
        return ChatRequest.model_validate(candidate)
    except (ValidationError, TypeError, ValueError):
        raise BackendError(
            "Invalid chat request; only user and assistant data roles are allowed."
        ) from None


def build_reviewed_request(
    messages: list[dict[str, str]] | tuple[ChatMessage, ...],
    *,
    system: str = "",
    recipient: str,
) -> ChatRequest:
    """Call ONLY after the user reviews these exact minimized messages/instructions.

    This helper does not obtain consent and must never be invoked automatically
    on raw conversation history or vault contents.
    """
    request = coerce_request(list(messages), system)  # type: ignore[arg-type]
    disclosure = ReviewedDisclosure(
        recipient=recipient,
        messages=request.messages,
        reviewed=True,
        fingerprint=disclosure_fingerprint(request.messages, request.system, recipient),
    )
    return ChatRequest(
        messages=request.messages,
        system=request.system,
        privacy_mode="reviewed_remote",
        disclosure=disclosure,
    )


def outbound_messages(request: ChatRequest, *, recipient: str, local: bool) -> list[dict]:
    if local:
        return [message.model_dump() for message in request.messages]
    disclosure = request.disclosure
    if request.privacy_mode != "reviewed_remote" or disclosure is None:
        raise BackendError(
            "Local-only request blocked: review a minimal summary and explicitly approve "
            "its disclosure to this external provider. / 纯本地请求已拦截：请审核最小摘要，"
            "并明确同意将其披露给此外部提供方。"
        )
    expected = disclosure_fingerprint(disclosure.messages, request.system, recipient)
    if disclosure.recipient != recipient or disclosure.fingerprint != expected:
        raise BackendError(
            "Disclosure changed or targets another provider; review it again. / "
            "披露内容或提供方已变更，请重新审核。"
        )
    return [message.model_dump() for message in disclosure.messages]


def validate_local_url(url: str) -> str:
    """Require an unambiguous loopback origin; no credentials or URL decorations."""
    try:
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        local = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = False
        parsed = urlsplit("")
    if (
        not local
        or parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise BackendError("Local AI requires a loopback URL (localhost, 127.0.0.1 or ::1).")
    try:
        _ = parsed.port
    except ValueError:
        raise BackendError("The local AI port is invalid.") from None
    # Avoid DNS/proxy surprises even for the conventional localhost alias.
    if host == "localhost":
        port = f":{parsed.port}" if parsed.port is not None else ""
        return f"{parsed.scheme}://127.0.0.1{port}"
    return url.rstrip("/")


def validate_remote_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        valid_port = parsed.port
    except ValueError:
        raise BackendError("The external AI endpoint is invalid.") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or valid_port == 0
    ):
        raise BackendError("External AI requires HTTPS without URL credentials or query strings.")
    return url.rstrip("/")
