"""Official open-source Sign in with ChatGPT flow, with injectable transport.

Contract checked against OpenAI's September 2026 sign-in, token, session and
model guides. No constructor signs in, borrows another app's tokens or infers.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import queue
import re
import secrets
import socket
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Literal, Protocol
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from anti_dating_scam.ai.chatgpt_credentials import (
    ISSUER,
    ChatGPTCredential,
    ChatGPTCredentialState,
    ChatGPTCredentialStore,
)
from anti_dating_scam.ai.privacy import BackendError

DISCOVERY_URL = ISSUER + "/.well-known/openid-configuration"
AUTHORIZE_URL = ISSUER + "/api/accounts/authorize"
TOKEN_URL = ISSUER + "/api/accounts/oauth/token"
JWKS_URL = ISSUER + "/.well-known/jwks.json"
RESOURCE = "https://api.openai.com/v1"
MODELS_URL = RESOURCE + "/models"
RESPONSES_URL = RESOURCE + "/responses"
MANAGE_USAGE_URL = "https://chatgpt.com/settings/usage"
REQUESTED_SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
ISSUED_CLIENT_PATTERN = re.compile(r"oaiapp_[A-Za-z0-9_-]{1,240}\Z")


class ChatGPTConnectionError(BackendError):
    """Displayable failure with an application-owned code and no provider body."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        http_status: int | None = None,
        response_shape: str = "",
        request_id: str = "",
    ) -> None:
        category = (
            "usage"
            if http_status == 429
            else "auth"
            if http_status in {401, 403}
            else "network"
            if http_status == 503
            else "unknown"
        )
        super().__init__(message, category=category)
        self.code, self.http_status = code, http_status
        self.response_shape, self.request_id = response_shape, request_id


class ChatGPTConnectionDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    phase: Literal[
        "idle",
        "preparing",
        "listener_ready",
        "waiting_callback",
        "callback_received",
        "registration_saved",
        "discovery",
        "token_exchange",
        "identity_verification",
        "credential_save",
        "connected",
        "cancelled",
        "failed",
    ] = "idle"
    code: str = ""
    listener_active: bool = False
    browser_opened: bool = False
    callback_received: bool = False
    failed_phase: str = ""


_OAUTH_TERMINAL_REFRESH_ERRORS = frozenset(
    {
        "invalid_grant",
        "invalid_refresh_token",
        "token_expired",
        "refresh_token_expired",
        "refresh_token_invalidated",
        "refresh_token_reused",
    }
)
_SAFE_PROVIDER_CODES = _OAUTH_TERMINAL_REFRESH_ERRORS | frozenset(
    {
        "invalid_client",
        "invalid_request",
        "access_denied",
        "insufficient_scope",
        "subscription_sharing_user_not_eligible",
        "subscription_sharing_usage_limit_exceeded",
        "subscription_sharing_usage_unavailable",
        "subscription_sharing_unsupported_capability",
        "subscription_sharing_route_not_supported",
        "subscription_sharing_invalid_user",
        "chatpass_v2_scope_not_authorized",
        "chatpass_v2_invalid_authorization_context",
        "subscription_sharing_user_unavailable",
    }
)


def _safe_http_error(error: urllib.error.HTTPError) -> ChatGPTConnectionError:
    """Preserve only status, known code, body shape and a bounded request ID."""
    code, shape, request_id = "http_error", "other", ""
    try:
        request_id = str(error.headers.get("x-request-id", "")) if error.headers else ""
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
            request_id = ""
        raw = error.read(16_385)
        if not raw:
            shape = "empty"
        elif len(raw) <= 16_384:
            data = json.loads(raw)
            if isinstance(data, dict):
                provider_error = data.get("error")
                if isinstance(provider_error, str):
                    shape, returned = "oauth_error", provider_error
                elif isinstance(provider_error, dict):
                    shape, returned = "api_error", provider_error.get("code")
                else:
                    shape, returned = ("detail" if "detail" in data else "other"), None
                if isinstance(returned, str) and returned in _SAFE_PROVIDER_CODES:
                    code = returned
    except (OSError, ValueError, UnicodeDecodeError):
        pass
    finally:
        error.close()
    if code in _OAUTH_TERMINAL_REFRESH_ERRORS:
        message = "ChatGPT authorization expired or was already used. Connect again."
    elif code == "invalid_client":
        message = "ChatGPT rejected this app registration. Reconnect the saved account."
    elif code in {
        "subscription_sharing_usage_unavailable",
        "subscription_sharing_user_unavailable",
    }:
        message = "ChatGPT plan access is temporarily unavailable. Your connection was preserved."
    elif error.code == 429:
        message = "ChatGPT usage limit reached. Review Manage usage."
    elif error.code == 401:
        message = "ChatGPT access was not accepted. Check the selected account and granted access."
    elif error.code == 403:
        message = "ChatGPT restricted this app or account. Review plan access and availability."
    elif error.code == 503:
        message = "ChatGPT is temporarily unavailable. Your connection was preserved."
    else:
        message = f"ChatGPT request failed (HTTP {error.code}). No retry was made."
    return ChatGPTConnectionError(
        message, code=code, http_status=error.code, response_shape=shape, request_id=request_id
    )


class ChatGPTTransport(Protocol):
    def get_json(self, url: str, headers: dict[str, str], timeout: float) -> dict: ...

    def post_form(self, url: str, form: dict[str, str], timeout: float) -> dict: ...

    def stream_json(
        self, url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float
    ) -> Iterable[dict]: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BackendError("ChatGPT endpoint redirects are blocked.")


class OfficialChatGPTHttpTransport:
    """Fixed official origins, no system proxies/redirects, bounded responses."""

    def _open(self, url: str, body: bytes | None, headers: dict[str, str], timeout: float):
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in {"auth.openai.com", "api.openai.com"}
            or parsed.port not in {None, 443}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise BackendError("Only official ChatGPT authorization and inference endpoints work.")
        request = urllib.request.Request(
            url, data=body, headers=headers, method="POST" if body is not None else "GET"
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        try:
            return opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            raise _safe_http_error(exc) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise BackendError(
                "Could not reach ChatGPT. Your request was not retried.", category="network"
            ) from None

    @staticmethod
    def _read_json(response) -> dict:
        raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise BackendError("ChatGPT returned an oversized connection response.")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError
            return data
        except (ValueError, UnicodeDecodeError):
            raise BackendError("ChatGPT returned an invalid connection response.") from None

    def get_json(self, url: str, headers: dict[str, str], timeout: float) -> dict:
        with self._open(url, None, headers, timeout) as response:
            return self._read_json(response)

    def post_form(self, url: str, form: dict[str, str], timeout: float) -> dict:
        with self._open(
            url,
            urlencode(form).encode(),
            {"Content-Type": "application/x-www-form-urlencoded"},
            timeout,
        ) as response:
            return self._read_json(response)

    def stream_json(self, url, payload, headers, timeout):
        return self.stream_json_controlled(url, payload, headers, timeout)

    _stream_slots = threading.BoundedSemaphore(2)

    def stream_json_controlled(self, url, payload, headers, timeout, *, cancel_event=None):
        """Bound total caller latency, queue size and outstanding HTTP readers.

        A Windows socket shutdown does not always interrupt a pending select.
        The consumer therefore stops independently. The daemon reader has a
        bounded socket timeout, owns its response and always releases its slot.
        No more than two readers can remain alive; saturation fails without retry.
        """
        deadline = time.monotonic() + timeout
        finished = threading.Event()
        response_socket = []
        mailbox = queue.Queue(maxsize=8)

        def check():
            if cancel_event is not None and cancel_event.is_set():
                raise BackendError("ChatGPT request stopped.", category="cancelled")
            if time.monotonic() >= deadline:
                raise BackendError("ChatGPT response timed out.", category="timeout")

        def publish(kind, value):
            while not finished.is_set():
                try:
                    mailbox.put((kind, value), timeout=0.05)
                    return
                except queue.Full:
                    pass

        def read():
            try:
                with self._open(
                    url,
                    json.dumps(payload, ensure_ascii=False, allow_nan=False).encode(),
                    {"Content-Type": "application/json", "Accept": "text/event-stream", **headers},
                    timeout,
                ) as response:
                    sock = getattr(
                        getattr(getattr(response, "fp", None), "raw", None), "_sock", None
                    )
                    if sock is not None:
                        response_socket.append(sock)
                    parts, total = [], 0
                    while not finished.is_set():
                        raw = response.readline(262_145)
                        if len(raw) > 262_144:
                            raise BackendError("ChatGPT returned an oversized stream event.")
                        if not raw:
                            if parts:
                                publish("event", self._event(parts))
                            publish("end", None)
                            return
                        total += len(raw)
                        if total > 2_000_000:
                            raise BackendError("ChatGPT reply exceeded the size limit.")
                        line = raw.decode("utf-8").rstrip("\r\n")
                        if not line and parts:
                            publish("event", self._event(parts))
                            parts = []
                        elif line.startswith("data:"):
                            parts.append(line[5:].lstrip(" "))
            except BackendError as exc:
                publish("error", exc)
            except Exception:
                publish(
                    "error", BackendError("ChatGPT stream was interrupted.", category="network")
                )
            finally:
                self._stream_slots.release()

        check()
        if not self._stream_slots.acquire(blocking=False):
            raise BackendError(
                "Earlier connections are still closing. Try again shortly.", category="network"
            )
        worker = threading.Thread(target=read, daemon=True, name="slowmatch-stream-reader")
        worker.start()
        try:
            while True:
                check()
                try:
                    kind, value = mailbox.get(timeout=0.05)
                except queue.Empty:
                    continue
                check()
                if kind == "error":
                    raise value
                if kind == "end":
                    return
                yield value
        finally:
            finished.set()
            if response_socket:
                try:
                    response_socket[0].shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    @staticmethod
    def _event(parts: list[str]) -> dict:
        text = "\n".join(parts)
        if text == "[DONE]":
            return {"type": "transport.done"}
        try:
            event = json.loads(text)
            if not isinstance(event, dict):
                raise ValueError
            return event
        except ValueError:
            raise BackendError("ChatGPT returned an invalid stream event.") from None


class ChatGPTConnectionStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    connected: bool = False
    sharing: bool = False
    label: str = "ChatGPT"
    client_id: str = ""
    scopes: tuple[str, ...] = ()


class ChatGPTModelChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._:/-]+$")
    display_name: str = Field(min_length=1, max_length=200)


@dataclass
class PendingChatGPTLogin:
    redirect_uri: str
    client_id: str
    host_id: str
    expires_at: float
    expected_subject: SecretStr | None = field(default=None, repr=False)
    state: str = field(default="", repr=False)
    nonce: str = field(default="", repr=False)
    verifier: str = field(default="", repr=False)
    authorization_url: str = field(default="", repr=False)
    consumed: bool = False


def verify_chatgpt_id_token(token: str, client_id: str, nonce: str, jwks: dict, now: float) -> dict:
    """Maintained PyJWT/cryptography validates RSA signature and OIDC identity."""
    try:
        import jwt

        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
            raise ValueError
        # Never follow untrusted token jku/x5u links or accept embedded keys.
        if any(field in header for field in ("jku", "x5u", "jwk", "crit")):
            raise ValueError
        keys = jwks.get("keys")
        if not isinstance(keys, list) or len(keys) > 100:
            raise ValueError
        matching = [
            key for key in keys if isinstance(key, dict) and key.get("kid") == header["kid"]
        ]
        if len(matching) != 1:
            raise ValueError
        key = matching[0]
        if key.get("kty") != "RSA" or key.get("use", "sig") != "sig":
            raise ValueError
        if key.get("alg", "RS256") != "RS256":
            raise ValueError
        public_key = jwt.PyJWK.from_dict(key, algorithm="RS256").key
        if public_key.key_size < 2048:
            raise ValueError
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=ISSUER,
            options={
                "require": ["iss", "aud", "sub", "exp", "iat", "nonce"],
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
            },
        )
        for name in ("iat", "exp"):
            value = claims[name]
            if type(value) not in {int, float} or not math.isfinite(value):
                raise ValueError
        if claims["exp"] <= now - 5 or claims["iat"] > now + 5:
            raise ValueError
        if claims["exp"] <= claims["iat"]:
            raise ValueError
        if "nbf" in claims:
            if type(claims["nbf"]) not in {int, float} or not math.isfinite(claims["nbf"]):
                raise ValueError
            if claims["nbf"] > now + 5:
                raise ValueError
        if not isinstance(claims["sub"], str) or not claims["sub"] or len(claims["sub"]) > 1024:
            raise ValueError
        if not isinstance(claims["nonce"], str) or not secrets.compare_digest(
            claims["nonce"], nonce
        ):
            raise ValueError
        audience = claims["aud"]
        if isinstance(audience, list) and len(audience) > 1 and claims.get("azp") != client_id:
            raise ValueError
        return {"sub": claims["sub"], "iss": claims["iss"]}
    except ImportError:
        raise BackendError(
            "ChatGPT sign-in needs the desktop identity verification component."
        ) from None
    except Exception:
        raise BackendError("ChatGPT identity verification failed. Sign in again.") from None


def _callback_parameters(pending: PendingChatGPTLogin, callback_url: str, now: float) -> dict:
    if pending.consumed or now >= pending.expires_at:
        raise BackendError("ChatGPT sign-in expired or was already completed.")
    parsed = urlsplit(callback_url)
    if urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", "")) != pending.redirect_uri:
        raise BackendError("ChatGPT callback address did not match this sign-in.")
    if parsed.fragment or len(parsed.query) > 16_384:
        raise BackendError("ChatGPT returned an invalid sign-in callback.")
    query = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=20)
    if any(len(values) != 1 for values in query.values()):
        raise BackendError("ChatGPT returned repeated sign-in parameters.")
    parameters = {key: value[0] for key, value in query.items()}
    if not secrets.compare_digest(parameters.get("state", ""), pending.state):
        raise BackendError("ChatGPT sign-in state did not match this attempt.")
    return parameters


class ChatGPTConnectionService:
    def __init__(
        self,
        store: ChatGPTCredentialStore | None = None,
        transport: ChatGPTTransport | None = None,
        browser_open: Callable[[str], bool] | None = None,
        clock: Callable[[], float] = time.time,
        identity_verifier: Callable[[str, str, str, dict, float], dict] = verify_chatgpt_id_token,
    ) -> None:
        self.store = store or ChatGPTCredentialStore()
        self.transport = transport or OfficialChatGPTHttpTransport()
        self._browser_open = browser_open or webbrowser.open
        self._clock, self._identity_verifier = clock, identity_verifier
        self._diagnostic = ChatGPTConnectionDiagnostic()
        self._progress_callback: Callable[[ChatGPTConnectionDiagnostic], None] | None = None

    def diagnostic(self) -> ChatGPTConnectionDiagnostic:
        """Public in-memory phases only; never reads saved credentials."""
        return self._diagnostic

    def _progress(self, phase: str, **updates: Any) -> None:
        self._diagnostic = ChatGPTConnectionDiagnostic.model_validate(
            {
                **self._diagnostic.model_dump(),
                "phase": phase,
                **updates,
            }
        )
        if self._progress_callback is not None:
            try:
                self._progress_callback(self._diagnostic)
            except Exception:
                # A UI observer cannot abort identity verification or leak errors.
                pass

    def _failed(self, error: BackendError) -> None:
        previous = self._diagnostic.phase
        code = error.code if isinstance(error, ChatGPTConnectionError) else "connection_failed"
        cancelled = "cancelled" in str(error).lower()
        self._progress("cancelled" if cancelled else "failed", code=code, failed_phase=previous)

    @staticmethod
    def _status(credential: ChatGPTCredential | None, now: float) -> ChatGPTConnectionStatus:
        if credential is None:
            return ChatGPTConnectionStatus()
        connected = bool(credential.access_token.get_secret_value()) and (
            credential.expires_at > now or credential.refresh_token is not None
        )
        return ChatGPTConnectionStatus(
            connected=connected,
            sharing=(
                connected
                and PLAN_SCOPE in credential.scopes
                and "resource.invoke" in credential.scopes
            ),
            label="ChatGPT · " + credential.client_id[-6:],
            client_id=credential.client_id,
            scopes=credential.scopes,
        )

    def status(self) -> ChatGPTConnectionStatus:
        state = self.store.load()
        credential = self._selected(state) if state else None
        return self._status(credential, self._clock())

    def accounts(self) -> tuple[ChatGPTConnectionStatus, ...]:
        state = self.store.load()
        return (
            tuple(self._status(item, self._clock()) for item in state.registrations)
            if state
            else ()
        )

    @staticmethod
    def _selected(state: ChatGPTCredentialState) -> ChatGPTCredential | None:
        return next(
            (entry for entry in state.registrations if entry.client_id == state.active_client_id),
            None,
        )

    def _discovery(self) -> dict:
        data = self.transport.get_json(DISCOVERY_URL, {}, 20)
        expected = {
            "issuer": ISSUER,
            "authorization_endpoint": AUTHORIZE_URL,
            "token_endpoint": TOKEN_URL,
            "jwks_uri": JWKS_URL,
        }
        if any(data.get(key) != value for key, value in expected.items()):
            raise BackendError("ChatGPT authorization settings did not match official endpoints.")
        return data

    def begin_login(
        self, redirect_uri: str, *, client_id: str | None = None, timeout: float = 180
    ) -> PendingChatGPTLogin:
        parsed = urlsplit(redirect_uri)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or not parsed.port
            or parsed.path != "/auth/callback"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise BackendError("ChatGPT sign-in needs a 127.0.0.1 /auth/callback listener.")
        if not 1 <= timeout <= 600:
            raise BackendError("ChatGPT sign-in timeout is invalid.")
        state = self.store.load(create=True)
        assert state is not None
        selected = (
            next((item for item in state.registrations if item.client_id == client_id), None)
            if client_id
            else self._selected(state)
        )
        if client_id and selected is None and client_id != state.pending_client_id:
            raise BackendError("This ChatGPT account registration has not been saved.")
        selected_id = selected.client_id if selected else (client_id or state.pending_client_id)
        verifier = secrets.token_urlsafe(64)
        pending = PendingChatGPTLogin(
            redirect_uri=redirect_uri,
            client_id=selected_id or "dynamic_agent_client",
            host_id=state.host_id,
            expires_at=self._clock() + timeout,
            expected_subject=selected.subject if selected else None,
            state=secrets.token_urlsafe(32),
            nonce=secrets.token_urlsafe(32),
            verifier=verifier,
        )
        parameters = {
            "client_id": pending.client_id,
            "ext_agent_host_id": pending.host_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": REQUESTED_SCOPES,
            "resource": RESOURCE,
            "state": pending.state,
            "nonce": pending.nonce,
            "code_challenge_method": "S256",
            "code_challenge": base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode(),
        }
        if pending.client_id == "dynamic_agent_client":
            parameters["agent_name_hint"] = "AI-SlowMatch"
        elif selected and selected.id_token:
            parameters["id_token_hint"] = selected.id_token.get_secret_value()
        pending.authorization_url = AUTHORIZE_URL + "?" + urlencode(parameters)
        return pending

    def complete_login(
        self, pending: PendingChatGPTLogin, callback_url: str
    ) -> ChatGPTConnectionStatus:
        try:
            result = self._complete_login(pending, callback_url)
            self._progress("connected", code="", failed_phase="")
            return result
        except BackendError as error:
            self._failed(error)
            raise
        except Exception:
            error = ChatGPTConnectionError(
                "ChatGPT sign-in could not complete. No private diagnostics were disclosed.",
                code="connection_failed",
            )
            self._failed(error)
            raise error from None

    def _complete_login(
        self, pending: PendingChatGPTLogin, callback_url: str
    ) -> ChatGPTConnectionStatus:
        parameters = _callback_parameters(pending, callback_url, self._clock())
        pending.consumed = True
        self._progress("callback_received", callback_received=True)
        if parameters.get("error"):
            if parameters["error"] == "access_denied":
                raise BackendError("ChatGPT sign-in was cancelled. No model request was made.")
            raise BackendError("ChatGPT sign-in was not completed.")
        issued = parameters.get("client_id", pending.client_id)
        if not ISSUED_CLIENT_PATTERN.fullmatch(issued):
            raise BackendError("ChatGPT did not return a completed client registration.")
        if pending.client_id != "dynamic_agent_client" and issued != pending.client_id:
            raise BackendError("ChatGPT callback returned another account registration.")
        code = parameters.get("code", "")
        if not code or len(code) > 4096:
            raise BackendError("ChatGPT did not return a valid authorization code.")
        with self.store.exclusive():
            state = self.store.load(create=True)
            assert state is not None
            if state.host_id != pending.host_id:
                raise BackendError("ChatGPT host registration changed. Sign in again.")
            self.store.save(state.model_copy(update={"pending_client_id": issued}))
        self._progress("registration_saved")
        self._progress("discovery")
        self._discovery()
        self._progress("token_exchange")
        data = self.transport.post_form(
            TOKEN_URL,
            {
                "grant_type": "authorization_code",
                "client_id": issued,
                "code": code,
                "code_verifier": pending.verifier,
                "redirect_uri": pending.redirect_uri,
                "resource": RESOURCE,
            },
            30,
        )
        id_token = data.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise ChatGPTConnectionError(
                "ChatGPT sign-in did not include a verifiable identity.", code="id_token_missing"
            )
        self._progress("identity_verification")
        jwks = self.transport.get_json(JWKS_URL, {}, 20)
        identity = self._identity_verifier(id_token, issued, pending.nonce, jwks, self._clock())
        if (
            pending.expected_subject
            and identity["sub"] != pending.expected_subject.get_secret_value()
        ):
            raise BackendError("ChatGPT identity changed. The previous connection was preserved.")
        credential = self._credential(data, issued, identity["sub"])
        self._progress("credential_save")
        with self.store.exclusive():
            state = self.store.load(create=True)
            assert state is not None
            registrations = tuple(item for item in state.registrations if item.client_id != issued)
            self.store.save(
                state.model_copy(
                    update={
                        "registrations": (*registrations, credential),
                        "active_client_id": issued,
                        "pending_client_id": None,
                    }
                )
            )
        return self._status(credential, self._clock())

    def _credential(self, data: dict, client_id: str, subject: str) -> ChatGPTCredential:
        try:
            access = data["access_token"]
            expiry = data["expires_in"]
            scope = data["scope"]
            token_type = data.get("token_type")
            if (
                not isinstance(token_type, str)
                or token_type.lower() != "bearer"
                or not isinstance(access, str)
                or not access
                or len(access) > 131_072
                or type(expiry) not in {int, float}
                or not math.isfinite(expiry)
                or not 0 < expiry <= 86_400
                or not isinstance(scope, str)
            ):
                raise ValueError
            scopes = tuple(scope.split())
            if len(scopes) > 30 or any(len(item) > 200 for item in scopes):
                raise ValueError
            for field_name in ("refresh_token", "id_token"):
                value = data.get(field_name)
                if value is not None and (
                    not isinstance(value, str) or not value or len(value) > 131_072
                ):
                    raise ValueError
            earliest = data.get("earliest_refresh_at", 0)
            if type(earliest) not in {int, float} or not math.isfinite(earliest) or earliest < 0:
                raise ValueError
            return ChatGPTCredential(
                client_id=client_id,
                subject=subject,
                access_token=access,
                refresh_token=data.get("refresh_token"),
                id_token=data.get("id_token"),
                scopes=scopes,
                expires_at=self._clock() + expiry,
                earliest_refresh_at=earliest,
            )
        except (KeyError, ValueError, TypeError):
            raise BackendError(
                "ChatGPT returned incomplete or invalid connection credentials."
            ) from None

    def connect(
        self,
        cancel_event: threading.Event | None = None,
        timeout: float = 180,
        *,
        client_id: str | None = None,
        progress_callback: Callable[[ChatGPTConnectionDiagnostic], None] | None = None,
    ) -> ChatGPTConnectionStatus:
        service = self
        callback: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            # A stalled local browser request must not freeze the callback loop.
            timeout = 3

            def log_message(self, format, *args):
                # Authorization codes and URL hints must never enter server logs.
                pass

            def do_GET(self):  # noqa: N802
                supplied = pending.redirect_uri.split("/auth/callback")[0] + self.path
                try:
                    _callback_parameters(pending, supplied, service._clock())
                    callback.append(supplied)
                    service._progress("callback_received", callback_received=True)
                    status = 200
                    body = (
                        "Browser authorization received. Return to AI-SlowMatch to check "
                        "connection completion. / 已收到浏览器授权，"
                        "请返回 AI-SlowMatch 查看连接结果。"
                    ).encode()
                except (BackendError, ValueError):
                    status, body = 400, b"Invalid sign-in callback."
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self._progress_callback = progress_callback
        self._diagnostic = ChatGPTConnectionDiagnostic(phase="preparing")
        self._progress("preparing")
        try:
            if cancel_event and cancel_event.is_set():
                raise BackendError("ChatGPT sign-in was cancelled.")
            with HTTPServer(("127.0.0.1", 0), Handler) as server:
                server.timeout = 0.2
                pending = self.begin_login(
                    f"http://127.0.0.1:{server.server_port}/auth/callback",
                    client_id=client_id,
                    timeout=timeout,
                )
                self._progress("listener_ready", listener_active=True)
                if not self._browser_open(pending.authorization_url):
                    pending.consumed = True
                    raise BackendError("Could not open ChatGPT sign-in in your browser.")
                self._progress("waiting_callback", browser_opened=True)
                while not callback:
                    if cancel_event and cancel_event.is_set():
                        pending.consumed = True
                        raise BackendError("ChatGPT sign-in was cancelled.")
                    if self._clock() >= pending.expires_at:
                        pending.consumed = True
                        raise BackendError("ChatGPT sign-in timed out. Try connecting again.")
                    server.handle_request()
                if cancel_event and cancel_event.is_set():
                    pending.consumed = True
                    raise BackendError("ChatGPT sign-in was cancelled.")
                return self.complete_login(pending, callback[0])
        except BackendError as error:
            if self._diagnostic.phase not in {"failed", "cancelled"}:
                self._failed(error)
            raise
        except Exception:
            error = ChatGPTConnectionError(
                "ChatGPT sign-in could not complete. Your request was not retried.",
                code="connection_failed",
            )
            self._failed(error)
            raise error from None
        finally:
            self._progress(self._diagnostic.phase, listener_active=False)
            self._progress_callback = None

    def access_token(self) -> str:
        with self.store.exclusive():
            state = self.store.load()
            credential = self._selected(state) if state else None
            if not credential or not credential.access_token.get_secret_value():
                raise BackendError("Connect ChatGPT before starting an AI conversation.")
            if PLAN_SCOPE not in credential.scopes or "resource.invoke" not in credential.scopes:
                raise BackendError("ChatGPT plan use was not authorized. Review app access.")
            if credential.expires_at > self._clock() + 30:
                return credential.access_token.get_secret_value()
            if not credential.refresh_token or "offline_access" not in credential.scopes:
                raise BackendError("ChatGPT connection expired. Sign in again.")
            if self._clock() < credential.earliest_refresh_at:
                raise BackendError("ChatGPT token renewal is not available yet. Try later.")
            try:
                data = self.transport.post_form(
                    TOKEN_URL,
                    {
                        "grant_type": "refresh_token",
                        "client_id": credential.client_id,
                        "refresh_token": credential.refresh_token.get_secret_value(),
                        "resource": RESOURCE,
                    },
                    30,
                )
            except ChatGPTConnectionError as error:
                if error.code in _OAUTH_TERMINAL_REFRESH_ERRORS:
                    # A confirmed unusable renewable session must not continue
                    # displaying connected. Preserve the verified registration.
                    assert state is not None
                    cleared = credential.model_copy(
                        update={
                            "access_token": SecretStr(""),
                            "refresh_token": None,
                            "id_token": None,
                            "scopes": (),
                        }
                    )
                    self.store.save(
                        state.model_copy(
                            update={
                                "registrations": tuple(
                                    cleared if item.client_id == credential.client_id else item
                                    for item in state.registrations
                                )
                            }
                        )
                    )
                raise
            if not data.get("refresh_token"):
                raise BackendError(
                    "ChatGPT token renewal did not supply its replacement credential."
                )
            refreshed = self._credential(
                data, credential.client_id, credential.subject.get_secret_value()
            )
            # Keep the original verified identity hint. A refresh response does
            # not have this login attempt's fresh OIDC nonce; never replace the
            # verified hint with an unverified new ID token.
            refreshed = refreshed.model_copy(update={"id_token": credential.id_token})
            assert state is not None
            self.store.save(
                state.model_copy(
                    update={
                        "registrations": tuple(
                            refreshed if item.client_id == credential.client_id else item
                            for item in state.registrations
                        )
                    }
                )
            )
            if PLAN_SCOPE not in refreshed.scopes or "resource.invoke" not in refreshed.scopes:
                raise BackendError("ChatGPT plan permission was removed. Review app access.")
            return refreshed.access_token.get_secret_value()

    def list_models(self) -> tuple[ChatGPTModelChoice, ...]:
        token = self.access_token()
        data = self.transport.get_json(MODELS_URL, {"Authorization": f"Bearer {token}"}, 20)
        entries = data.get("models")
        if not isinstance(entries, list) or len(entries) > 500:
            raise BackendError("ChatGPT returned an invalid account model catalog.")
        try:
            choices = tuple(
                ChatGPTModelChoice(slug=item["slug"], display_name=item["display_name"])
                for item in entries
                if isinstance(item, dict) and item.get("visibility") == "list"
            )
        except (KeyError, ValueError, TypeError):
            raise BackendError("ChatGPT returned an invalid account model catalog.") from None
        if len({choice.slug for choice in choices}) != len(choices):
            raise BackendError("ChatGPT returned duplicate account model choices.")
        return choices

    def create_backend(self, model: str, *, included_plan_confirmed: bool = False):
        from anti_dating_scam.ai.chatgpt_backend import ChatGPTPlanBackend

        return ChatGPTPlanBackend(self, model, included_plan_confirmed=included_plan_confirmed)

    def disconnect(self) -> bool:
        """Clear selected tokens even if remote revocation cannot be confirmed."""
        confirmed = False
        with self.store.exclusive():
            state = self.store.load()
            credential = self._selected(state) if state else None
            if not state or not credential:
                return True
            try:
                discovery = self._discovery()
                endpoint = discovery.get("revocation_endpoint", "")
                parsed = urlsplit(endpoint)
                if (
                    parsed.scheme != "https"
                    or parsed.hostname != "auth.openai.com"
                    or parsed.port not in {None, 443}
                    or parsed.username
                    or parsed.password
                    or parsed.query
                    or parsed.fragment
                ):
                    raise BackendError("Invalid ChatGPT revocation endpoint.")
                if credential.refresh_token:
                    self.transport.post_form(
                        endpoint,
                        {
                            "token": credential.refresh_token.get_secret_value(),
                            "token_type_hint": "refresh_token",
                            "client_id": credential.client_id,
                        },
                        20,
                    )
                confirmed = True
            except Exception:
                confirmed = False
            cleared = credential.model_copy(
                update={
                    "access_token": SecretStr(""),
                    "refresh_token": None,
                    "id_token": None,
                    "scopes": (),
                }
            )
            self.store.save(
                state.model_copy(
                    update={
                        "registrations": tuple(
                            cleared if item.client_id == credential.client_id else item
                            for item in state.registrations
                        ),
                        "active_client_id": None,
                    }
                )
            )
        return confirmed
