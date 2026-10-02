"""ChatGPT-plan Responses adapter: explicit consent, no retries or fallback."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

from anti_dating_scam.ai.chatgpt_auth import RESPONSES_URL, ChatGPTModelChoice
from anti_dating_scam.ai.privacy import BackendError, ChatRequest, coerce_request, outbound_messages
from anti_dating_scam.ai.results import AIProvenance, ChatResult

if TYPE_CHECKING:
    from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionService


class ChatGPTPlanBackend:
    name = "ChatGPT plan"
    provider_id = "chatgpt_plan"
    local = False

    def __init__(
        self,
        connection: ChatGPTConnectionService,
        model: str,
        *,
        included_plan_confirmed: bool = False,
        timeout: float = 180,
    ) -> None:
        try:
            ChatGPTModelChoice(slug=model, display_name=model)
        except ValueError:
            raise BackendError("Choose a model from your ChatGPT account's model list.") from None
        if type(included_plan_confirmed) is not bool:
            raise BackendError("Confirm the ChatGPT usage setting explicitly.")
        self.connection, self.model, self.timeout = connection, model, timeout
        self._included_plan_confirmed = included_plan_confirmed
        self._client_id = connection.status().client_id
        self._cancel_event: threading.Event | None = None

    @property
    def recipient(self) -> str:
        return f"{RESPONSES_URL}#{self.model}"

    def set_included_plan_confirmed(self, confirmed: bool) -> None:
        """Local confirmation, not a server guarantee or a billing-setting API.

        The UI must first explain that OpenAI's Usage settings control whether
        credits may be used. No documented request field enforces included-only.
        """
        if type(confirmed) is not bool:
            raise BackendError("Confirm the ChatGPT usage setting explicitly.")
        self._included_plan_confirmed = confirmed

    def set_cancel_event(self, event: threading.Event | None) -> None:
        self._cancel_event = event

    def _check_cancelled(self) -> None:
        if self._cancel_event is not None and self._cancel_event.is_set():
            raise BackendError(
                "ChatGPT request was stopped locally. An in-flight request may still be processed."
            )

    def check(self) -> tuple[bool, str]:
        """Connection/model discovery only; never a sample inference request."""
        try:
            if not self._client_id or self.connection.status().client_id != self._client_id:
                raise BackendError("Reconnect the selected ChatGPT account before chatting.")
            models = self.connection.list_models()
            if self.model not in {choice.slug for choice in models}:
                raise BackendError(
                    "The selected model is not available to this ChatGPT account.", category="model"
                )
            return True, "ChatGPT is connected; no AI request was made during this check."
        except BackendError as exc:
            return False, str(exc)
        except Exception:
            return False, "Could not inspect the ChatGPT connection."

    @staticmethod
    def _completed_text(response: dict) -> str:
        if response.get("status") != "completed" or not isinstance(response.get("output"), list):
            raise BackendError("ChatGPT did not return a completed response.")
        texts = []
        for item in response["output"]:
            if not isinstance(item, dict):
                raise BackendError("ChatGPT returned an invalid completed response.")
            if item.get("type") == "reasoning":
                continue
            if item.get("type") != "message" or item.get("role") != "assistant":
                raise BackendError("ChatGPT returned an unsupported response item.")
            contents = item.get("content")
            if not isinstance(contents, list):
                raise BackendError("ChatGPT returned an invalid completed response.")
            for block in contents:
                if not isinstance(block, dict) or block.get("type") != "output_text":
                    raise BackendError("ChatGPT did not return a usable text answer.")
                if not isinstance(block.get("text"), str):
                    raise BackendError("ChatGPT returned an invalid text answer.")
                texts.append(block["text"])
        text = "".join(texts)
        if not text.strip() or len(text) > 256_000:
            raise BackendError("ChatGPT returned an empty or oversized answer.")
        return text

    @staticmethod
    def _validate_strict_schema(schema: dict) -> None:
        """Reject incompatible objects; never rewrite an already reviewed schema."""

        def visit(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    visit(item)
                return
            if not isinstance(value, dict):
                return
            kind = value.get("type")
            object_kind = kind == "object" or isinstance(kind, list) and "object" in kind
            if object_kind or "properties" in value:
                properties = value.get("properties")
                required = value.get("required")
                if (
                    not isinstance(properties, dict)
                    or not isinstance(required, list)
                    or any(not isinstance(item, str) for item in required)
                    or len(required) != len(set(required))
                    or set(required) != set(properties)
                    or value.get("additionalProperties") is not False
                ):
                    raise BackendError(
                        "This report schema is not compatible with ChatGPT strict output. "
                        "Review a supported request before sending it."
                    )
            for item in value.values():
                visit(item)

        if schema.get("type") != "object" or "anyOf" in schema:
            raise BackendError("ChatGPT structured output needs a supported root object schema.")
        visit(schema)

    def chat(self, messages: ChatRequest | list[dict[str, str]], system: str | None = None) -> str:
        return self.chat_result(messages, system).text

    def chat_result(
        self, messages: ChatRequest | list[dict[str, str]], system: str | None = None
    ) -> ChatResult:
        request = coerce_request(messages, system)
        # Capture once: starting another request must never replace this request's stop signal.
        cancel = self._cancel_event
        deadline = time.monotonic() + self.timeout

        def check():
            if cancel is not None and cancel.is_set():
                raise BackendError(
                    "ChatGPT request stopped. / ChatGPT 请求已停止。", category="cancelled"
                )
            if time.monotonic() >= deadline:
                raise BackendError(
                    "ChatGPT response timed out. No retry was made. / "
                    "ChatGPT 回复超时，未自动重试。",
                    category="timeout",
                )

        check()
        if not self._included_plan_confirmed:
            raise BackendError(
                "Before chatting, confirm that credits are disabled for this app in ChatGPT "
                "Manage usage. This app cannot enforce that setting through the request API."
            )
        selected = outbound_messages(request, recipient=self.recipient, local=False)
        if request.response_schema is not None:
            self._validate_strict_schema(request.response_schema)
        if not self._client_id or self.connection.status().client_id != self._client_id:
            raise BackendError("ChatGPT account changed. Reconnect before chatting.")
        # Re-discover account choices; an invented or stale model never infers.
        choices = self.connection.list_models()
        if self.model not in {choice.slug for choice in choices}:
            raise BackendError(
                "The selected model is not available to this ChatGPT account.", category="model"
            )
        check()
        token = self.connection.access_token()
        payload: dict[str, Any] = {
            "model": self.model,
            "input": selected,
            "stream": True,
            "store": False,
        }
        if request.system:
            payload["instructions"] = request.system
        if request.response_schema is not None:
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "slowmatch_response",
                    "schema": request.response_schema,
                    "strict": True,
                }
            }
        completed: str | None = None
        provenance = None
        response_id = None
        added_items: dict[int, str] = {}
        done_items: dict[int, dict] = {}
        deltas: list[str] = []
        delta_length = 0
        controlled = getattr(self.connection.transport, "stream_json_controlled", None)
        if callable(controlled):
            events = controlled(
                RESPONSES_URL,
                payload,
                {"Authorization": f"Bearer {token}"},
                max(0.01, deadline - time.monotonic()),
                cancel_event=cancel,
            )
        else:
            events = self.connection.transport.stream_json(
                RESPONSES_URL, payload, {"Authorization": f"Bearer {token}"}, self.timeout
            )
        try:
            for event in events:
                check()
                if not isinstance(event, dict):
                    raise BackendError("ChatGPT returned an invalid stream event.")
                kind = event.get("type")
                if kind in {"response.created", "response.in_progress"}:
                    incoming_id = (event.get("response") or {}).get("id")
                    if not isinstance(incoming_id, str) or (
                        response_id and incoming_id != response_id
                    ):
                        raise BackendError("ChatGPT response identity changed during streaming.")
                    response_id = incoming_id
                if kind in {"response.output_item.added", "response.output_item.done"}:
                    item, index = event.get("item"), event.get("output_index")
                    if (
                        completed is not None
                        or type(index) is not int
                        or not 0 <= index < 32
                        or not isinstance(item, dict)
                        or not isinstance(item.get("id"), str)
                    ):
                        raise BackendError("ChatGPT returned an invalid output item.")
                    if kind == "response.output_item.added":
                        if index in added_items:
                            raise BackendError("ChatGPT repeated an output item.")
                        added_items[index] = item["id"]
                    else:
                        if (
                            index in done_items
                            or added_items.get(index, item["id"]) != item["id"]
                            or item.get("type") == "message"
                            and item.get("status") != "completed"
                        ):
                            raise BackendError(
                                "ChatGPT returned an unfinished or changed output item."
                            )
                        done_items[index] = item
                if kind in {"response.failed", "error", "response.incomplete"}:
                    error = (event.get("response") or {}).get("error") or event.get("error") or {}
                    code = error.get("code") if isinstance(error, dict) else ""
                    if code in {
                        "subscription_sharing_usage_limit_exceeded",
                    }:
                        raise BackendError(
                            "ChatGPT usage limit reached. Review Manage usage.", category="usage"
                        )
                    if code == "subscription_sharing_usage_unavailable":
                        raise BackendError(
                            "ChatGPT plan availability could not be checked. "
                            "Your connection was preserved; try again later."
                        )
                    raise BackendError("ChatGPT did not complete the answer. No retry was made.")
                if kind == "response.output_text.delta":
                    if completed is not None or not isinstance(event.get("delta"), str):
                        raise BackendError("ChatGPT returned an invalid text stream.")
                    delta_length += len(event["delta"])
                    if delta_length > 256_000:
                        raise BackendError("ChatGPT reply exceeded the size limit.")
                    deltas.append(event["delta"])
                elif kind == "response.completed":
                    if completed is not None or not isinstance(event.get("response"), dict):
                        raise BackendError("ChatGPT returned an invalid completion event.")
                    response = event["response"]
                    if response_id and response.get("id") != response_id:
                        raise BackendError("ChatGPT completion belongs to another response.")
                    if added_items and set(added_items) != set(done_items):
                        raise BackendError("ChatGPT completed with unfinished output items.")
                    # Some plan streams carry final content in output_item.done and
                    # an empty terminal output list. Still require terminal completion,
                    # completed message items and exact agreement with text deltas.
                    streamed = None
                    if done_items:
                        streamed = self._completed_text(
                            {
                                "status": "completed",
                                "output": [done_items[i] for i in sorted(done_items)],
                            }
                        )
                    terminal = response
                    if response.get("output") == [] and done_items:
                        terminal = {
                            **response,
                            "output": [done_items[i] for i in sorted(done_items)],
                        }
                    completed = self._completed_text(terminal)
                    if streamed is not None and streamed != completed:
                        raise BackendError("ChatGPT terminal and streamed output do not match.")
                    usage = response.get("usage") or {}
                    provenance = AIProvenance(
                        provider=self.provider_id,
                        requested_model=self.model,
                        reported_model=response.get("model"),
                        response_id=response.get("id"),
                        input_tokens=usage.get("input_tokens"),
                        output_tokens=usage.get("output_tokens"),
                    )
                    if deltas and "".join(deltas) != completed:
                        raise BackendError("ChatGPT final answer did not match its text stream.")
            check()
            if completed is None:
                raise BackendError("ChatGPT stream ended before a completed answer arrived.")
            return ChatResult(text=completed, provenance=provenance)
        except BackendError:
            raise
        except Exception:
            raise BackendError(
                "ChatGPT request failed. No private diagnostics were disclosed."
            ) from None
        finally:
            close = getattr(events, "close", None)
            if callable(close):
                close()
