"""Synthetic OAuth/JWKS/refresh/HTTP contract checks; no real login or inference."""

import base64
import hashlib
import io
import json
import threading
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlsplit

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from anti_dating_scam.ai.chatgpt_auth import (
    AUTHORIZE_URL,
    DISCOVERY_URL,
    ISSUER,
    JWKS_URL,
    MANAGE_USAGE_URL,
    MODELS_URL,
    PLAN_SCOPE,
    RESOURCE,
    TOKEN_URL,
    ChatGPTConnectionError,
    ChatGPTConnectionService,
    OfficialChatGPTHttpTransport,
    _safe_http_error,
    verify_chatgpt_id_token,
)
from anti_dating_scam.ai.chatgpt_credentials import (
    ChatGPTCredential,
    ChatGPTCredentialState,
    ChatGPTCredentialStore,
)
from anti_dating_scam.ai.privacy import BackendError

NOW = 1_800_000_000.0
CLIENT = "oaiapp_synthetic"
SCOPES = "openid offline_access resource.invoke " + PLAN_SCOPE


class FakeProtector:
    """Test-only reversible encoding; never used by the application."""

    def protect(self, plaintext):
        return b"synthetic:" + base64.b64encode(plaintext)

    def unprotect(self, ciphertext):
        return base64.b64decode(ciphertext.removeprefix(b"synthetic:"))


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def claims(nonce="synthetic-nonce", **updates):
    result = {
        "iss": ISSUER,
        "aud": CLIENT,
        "sub": "synthetic-subject",
        "nonce": nonce,
        "iat": NOW - 10,
        "exp": NOW + 3600,
    }
    return {**result, **updates}


def jwks(key):
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    return {"keys": [{**public, "kid": "synthetic-key", "use": "sig", "alg": "RS256"}]}


def signed(key, data, **headers):
    return jwt.encode(data, key, algorithm="RS256", headers={"kid": "synthetic-key", **headers})


class FakeTransport:
    def __init__(self, key):
        self.key, self.calls, self.nonce = key, [], ""
        self.scope = SCOPES
        self.subject = "synthetic-subject"
        self.expiry = 3600
        self.invalid_grant = False
        self.models = [
            {"slug": "synthetic-model", "display_name": "Synthetic", "visibility": "list"}
        ]

    def get_json(self, url, headers, timeout):
        self.calls.append(("GET", url, headers))
        if url == DISCOVERY_URL:
            return {
                "issuer": ISSUER,
                "authorization_endpoint": AUTHORIZE_URL,
                "token_endpoint": TOKEN_URL,
                "jwks_uri": JWKS_URL,
                "revocation_endpoint": ISSUER + "/api/accounts/oauth/revoke",
            }
        if url == JWKS_URL:
            return jwks(self.key)
        if url == MODELS_URL:
            return {"models": self.models}
        raise AssertionError("Unexpected synthetic endpoint")

    def post_form(self, url, form, timeout):
        self.calls.append(("POST", url, form.copy()))
        if url.endswith("/revoke"):
            return {}
        if self.invalid_grant:
            raise BackendError("Synthetic exchange failed.")
        return {
            "access_token": "synthetic-access",
            "refresh_token": "synthetic-refresh-new",
            "id_token": signed(self.key, claims(self.nonce, sub=self.subject)),
            "token_type": "Bearer",
            "expires_in": self.expiry,
            "scope": self.scope,
        }

    def stream_json(self, *args):
        raise AssertionError("OAuth and discovery must never infer")


@pytest.fixture
def service(tmp_path, signing_key):
    transport = FakeTransport(signing_key)
    store = ChatGPTCredentialStore(tmp_path / "own" / "credentials.bin", FakeProtector())
    connection = ChatGPTConnectionService(store, transport, clock=lambda: NOW)
    return connection, transport


def begin(service, client_id=None):
    connection, transport = service
    pending = connection.begin_login("http://127.0.0.1:54321/auth/callback", client_id=client_id)
    transport.nonce = pending.nonce
    return pending


def callback(pending, **updates):
    parameters = {"state": pending.state, "code": "synthetic-code", "client_id": CLIENT}
    parameters.update(updates)
    return pending.redirect_uri + "?" + urlencode(parameters)


def test_dynamic_pkce_and_one_shot_verified_login(service):
    connection, transport = service
    assert not connection.status().connected and not connection.store.path.exists()
    pending = begin(service)
    query = parse_qs(urlsplit(pending.authorization_url).query)
    assert query["client_id"] == ["dynamic_agent_client"]
    assert query["agent_name_hint"] == ["AI-SlowMatch"]
    assert query["resource"] == [RESOURCE]
    digest = (
        base64.urlsafe_b64encode(hashlib.sha256(pending.verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    assert query["code_challenge"] == [digest]
    assert MANAGE_USAGE_URL == "https://chatgpt.com/settings/usage"
    status = connection.complete_login(pending, callback(pending))
    assert status.connected and status.sharing and status.client_id == CLIENT
    assert "synthetic-subject" not in repr(status)
    exchange = next(item[2] for item in transport.calls if item[0] == "POST")
    assert exchange["client_id"] == CLIENT and exchange["redirect_uri"] == pending.redirect_uri
    assert exchange["code_verifier"] == pending.verifier and "client_secret" not in exchange
    with pytest.raises(BackendError, match="already"):
        connection.complete_login(pending, callback(pending))
    assert len([call for call in transport.calls if call[0] == "POST"]) == 1


@pytest.mark.parametrize(
    "updates",
    [
        {"state": "wrong"},
        {"client_id": "dynamic_agent_client"},
        {"code": ""},
        {"error": "access_denied"},
        {"error": "server_error"},
    ],
)
def test_invalid_callbacks_never_exchange(service, updates):
    connection, transport = service
    pending = begin(service)
    with pytest.raises(BackendError):
        connection.complete_login(pending, callback(pending, **updates))
    assert transport.calls == []
    assert not connection.status().connected


def test_duplicate_state_and_callback_address_are_rejected(service):
    connection, transport = service
    pending = begin(service)
    for url in (
        callback(pending) + "&state=" + pending.state,
        callback(pending).replace("127.0.0.1", "localhost"),
        callback(pending).replace("/auth/callback", "/callback"),
    ):
        with pytest.raises(BackendError):
            connection.complete_login(pending, url)
    assert transport.calls == []


def test_failed_exchange_keeps_issued_registration_without_retries(service):
    connection, transport = service
    pending = begin(service)
    transport.invalid_grant = True
    with pytest.raises(BackendError):
        connection.complete_login(pending, callback(pending))
    assert connection.store.load().pending_client_id == CLIENT
    assert not connection.status().connected
    following = begin(service)
    assert following.client_id == CLIENT and following.host_id == pending.host_id
    assert "agent_name_hint" not in parse_qs(urlsplit(following.authorization_url).query)
    assert len([call for call in transport.calls if call[0] == "POST"]) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://wrong.example"},
        {"aud": "oaiapp_other"},
        {"exp": NOW - 100},
        {"iat": NOW + 100},
        {"nonce": "wrong"},
        {"sub": ""},
        {"exp": True},
        {"nbf": NOW + 100},
        {"aud": [CLIENT, "other"], "azp": "other"},
    ],
)
def test_signed_untrusted_oidc_claims_rejected(signing_key, changes):
    token = signed(signing_key, claims(**changes))
    with pytest.raises(BackendError, match="verification failed"):
        verify_chatgpt_id_token(token, CLIENT, "synthetic-nonce", jwks(signing_key), NOW)


def test_signature_key_confusion_and_embedded_key_rejected(signing_key):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = signed(other, claims())
    with pytest.raises(BackendError):
        verify_chatgpt_id_token(token, CLIENT, "synthetic-nonce", jwks(signing_key), NOW)
    token = signed(signing_key, claims(), jku="https://wrong.example/jwks")
    with pytest.raises(BackendError):
        verify_chatgpt_id_token(token, CLIENT, "synthetic-nonce", jwks(signing_key), NOW)
    token = jwt.encode(
        claims(),
        "synthetic-not-a-key-000000000000000000000000",
        algorithm="HS256",
        headers={"kid": "synthetic-key"},
    )
    with pytest.raises(BackendError):
        verify_chatgpt_id_token(token, CLIENT, "synthetic-nonce", jwks(signing_key), NOW)


def test_returning_subject_change_preserves_original_credentials(service):
    connection, transport = service
    pending = begin(service)
    connection.complete_login(pending, callback(pending))
    original = connection.store.load().registrations
    pending = begin(service)
    assert "id_token_hint" in parse_qs(urlsplit(pending.authorization_url).query)
    assert "agent_name_hint" not in pending.authorization_url
    transport.subject = "another-synthetic-subject"
    with pytest.raises(BackendError, match="identity changed"):
        connection.complete_login(pending, callback(pending))
    assert connection.store.load().registrations == original


def test_authorization_without_plan_scope_never_discovers_models(service):
    connection, transport = service
    transport.scope = "openid"
    pending = begin(service)
    status = connection.complete_login(pending, callback(pending))
    assert status.connected and not status.sharing
    with pytest.raises(BackendError, match="not authorized"):
        connection.list_models()
    assert not any(call[1] == MODELS_URL for call in transport.calls)


def test_model_catalog_filters_server_choices_and_check_never_infers(service):
    connection, transport = service
    pending = begin(service)
    connection.complete_login(pending, callback(pending))
    transport.models += [{"slug": "hidden", "display_name": "Hidden", "visibility": "hidden"}]
    assert [choice.slug for choice in connection.list_models()] == ["synthetic-model"]
    backend = connection.create_backend("synthetic-model")
    assert backend.provider_id == "chatgpt_plan" and backend.check()[0]
    assert len([call for call in transport.calls if call[0] == "POST"]) == 1


def test_refresh_rotates_atomically_and_retains_verified_hint(service):
    connection, transport = service
    credential = ChatGPTCredential(
        client_id=CLIENT,
        subject="synthetic-subject",
        access_token="expired-synthetic-access",
        refresh_token="synthetic-refresh-old",
        id_token="verified-synthetic-hint",
        scopes=tuple(SCOPES.split()),
        expires_at=NOW - 10,
    )
    connection.store.save(
        ChatGPTCredentialState(
            host_id="urn:uuid:00000000-0000-4000-8000-000000000000",
            registrations=(credential,),
            active_client_id=CLIENT,
        )
    )
    assert connection.access_token() == "synthetic-access"
    refreshed = connection.store.load().registrations[0]
    assert refreshed.refresh_token.get_secret_value() == "synthetic-refresh-new"
    assert refreshed.id_token.get_secret_value() == "verified-synthetic-hint"
    assert refreshed.expires_at == NOW + 3600
    form = transport.calls[0][2]
    assert form["client_id"] == CLIENT and form["refresh_token"] == "synthetic-refresh-old"
    assert "scope" not in form
    assert connection.access_token() == "synthetic-access" and len(transport.calls) == 1


def test_disconnect_clears_tokens_retains_host_and_client(service):
    connection, transport = service
    pending = begin(service)
    connection.complete_login(pending, callback(pending))
    host = connection.store.load().host_id
    assert connection.disconnect()
    state = connection.store.load()
    assert state.host_id == host and state.registrations[0].client_id == CLIENT
    assert not state.registrations[0].access_token.get_secret_value()
    assert state.registrations[0].refresh_token is None and state.registrations[0].id_token is None
    assert not connection.status().connected
    pending = begin(service, CLIENT)
    assert pending.client_id == CLIENT and "id_token_hint" not in pending.authorization_url


def test_cancelled_or_browser_failure_never_exchanges(service):
    connection, transport = service
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(BackendError, match="cancelled"):
        connection.connect(cancel)
    connection._browser_open = lambda _url: False
    with pytest.raises(BackendError, match="open"):
        connection.connect()
    assert transport.calls == []


def test_sse_transport_parses_events_and_does_not_treat_done_as_completed(monkeypatch):
    transport = OfficialChatGPTHttpTransport()
    raw = (
        b":comment\nevent: response.output_text.delta\n"
        b'data: {"type":"response.output_text.delta","delta":"hi"}\n\n'
        b"data: [DONE]\n\n"
    )
    monkeypatch.setattr(transport, "_open", lambda *args: io.BytesIO(raw))
    events = list(transport.stream_json(RESOURCE + "/responses", {"stream": True}, {}, 1))
    assert events == [
        {"type": "response.output_text.delta", "delta": "hi"},
        {"type": "transport.done"},
    ]


@pytest.mark.parametrize(
    "url",
    [
        "http://api.openai.com/v1/models",
        "https://wrong.example/models",
        "https://api.openai.com:444/v1/models",
        "https://access@api.openai.com/v1/models",
        "https://api.openai.com/v1/models?token=synthetic",
    ],
)
def test_transport_rejects_nonofficial_decorated_urls_without_network(url):
    with pytest.raises(BackendError, match="official"):
        OfficialChatGPTHttpTransport().get_json(url, {}, 1)


def test_strict_schema_rejects_before_discovery_or_inference(service):
    from anti_dating_scam.ai.privacy import build_reviewed_request

    connection, transport = service
    pending = begin(service)
    connection.complete_login(pending, callback(pending))
    backend = connection.create_backend("synthetic-model", included_plan_confirmed=True)
    before = len(transport.calls)
    request = build_reviewed_request(
        [{"role": "user", "content": "synthetic"}], recipient=backend.recipient
    ).model_copy(
        update={
            "response_schema": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": [],
                "additionalProperties": False,
            }
        }
    )
    with pytest.raises(BackendError, match="schema"):
        backend.chat(request)
    assert len(transport.calls) == before


def test_real_loopback_callback_phases_never_expose_authorization_data(service):
    """Real local listener/browser handoff; token HTTP remains synthetic."""
    connection, transport = service
    captured, callback_threads, phases = {}, [], []

    def browser_open(url):
        parameters = parse_qs(urlsplit(url).query)
        transport.nonce = parameters["nonce"][0]
        target = (
            parameters["redirect_uri"][0]
            + "?"
            + urlencode(
                {
                    "state": parameters["state"][0],
                    "code": "synthetic-browser-code",
                    "client_id": CLIENT,
                }
            )
        )

        def browser_callback():
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(target, timeout=5) as response:
                captured["body"] = response.read().decode()

        worker = threading.Thread(target=browser_callback)
        worker.start()
        callback_threads.append(worker)
        return True

    connection._browser_open = browser_open
    status = connection.connect(progress_callback=phases.append)
    for worker in callback_threads:
        worker.join(timeout=5)
        assert not worker.is_alive()
    assert status.connected and status.sharing
    assert "check connection completion" in captured["body"]
    assert "synthetic-browser-code" not in captured["body"]
    assert connection.diagnostic().phase == "connected"
    assert not connection.diagnostic().listener_active
    assert connection.diagnostic().browser_opened and connection.diagnostic().callback_received
    for phase in ("listener_ready", "waiting_callback", "token_exchange", "identity_verification"):
        assert phase in [item.phase for item in phases]
    serialized = " ".join(str(item.model_dump()) for item in phases)
    assert "synthetic-access" not in serialized and "synthetic-subject" not in serialized
    assert "synthetic-browser-code" not in serialized and "nonce" not in serialized
    assert "http:" not in serialized and "https:" not in serialized


@pytest.mark.parametrize(
    "body,status,code,shape",
    [
        (
            {"error": "invalid_grant", "error_description": "private synthetic token"},
            400,
            "invalid_grant",
            "oauth_error",
        ),
        (
            {"error": {"code": "subscription_sharing_usage_unavailable", "message": "private"}},
            503,
            "subscription_sharing_usage_unavailable",
            "api_error",
        ),
        ({"detail": "private subscriber data"}, 403, "http_error", "detail"),
        ({"error": "synthetic-secret-unknown-code"}, 400, "http_error", "oauth_error"),
    ],
)
def test_http_failures_preserve_only_known_code_and_shape(body, status, code, shape):
    failure = urllib.error.HTTPError(
        TOKEN_URL,
        status,
        "private status reason",
        {"x-request-id": "req_synthetic"},
        io.BytesIO(json.dumps(body).encode()),
    )
    safe = _safe_http_error(failure)
    assert safe.code == code and safe.response_shape == shape and safe.http_status == status
    assert safe.request_id == "req_synthetic"
    assert "private" not in str(safe) and "synthetic-secret" not in str(safe)


def test_failed_exchange_phase_identifies_stage_without_saved_private_data(service):
    connection, transport = service
    pending = begin(service)
    transport.post_form = lambda *args: (_ for _ in ()).throw(
        ChatGPTConnectionError(
            "Reconnect the saved account.",
            code="invalid_grant",
            http_status=400,
        )
    )
    with pytest.raises(ChatGPTConnectionError):
        connection.complete_login(pending, callback(pending))
    diagnostic = connection.diagnostic()
    assert diagnostic.phase == "failed" and diagnostic.failed_phase == "token_exchange"
    assert diagnostic.code == "invalid_grant" and diagnostic.callback_received
    assert connection.store.load().pending_client_id == CLIENT
    assert not connection.status().connected


@pytest.mark.parametrize("code,cleared", [("invalid_grant", True), ("http_error", False)])
def test_refresh_terminal_failure_clears_tokens_while_temporary_failure_preserves(
    service, code, cleared
):
    connection, transport = service
    credential = ChatGPTCredential(
        client_id=CLIENT,
        subject="synthetic-subject",
        access_token="expired-synthetic-access",
        refresh_token="synthetic-refresh-old",
        id_token="verified-synthetic-hint",
        scopes=tuple(SCOPES.split()),
        expires_at=NOW - 10,
    )
    connection.store.save(
        ChatGPTCredentialState(
            host_id="urn:uuid:00000000-0000-4000-8000-000000000000",
            registrations=(credential,),
            active_client_id=CLIENT,
        )
    )
    transport.post_form = lambda *args: (_ for _ in ()).throw(
        ChatGPTConnectionError(
            "Synthetic safe error.",
            code=code,
            http_status=400 if cleared else 503,
        )
    )
    with pytest.raises(ChatGPTConnectionError):
        connection.access_token()
    result = connection.store.load().registrations[0]
    assert result.client_id == CLIENT and result.subject == credential.subject
    assert bool(result.refresh_token) is not cleared
    assert bool(result.access_token.get_secret_value()) is not cleared
    assert connection.status().connected is not cleared


def test_status_does_not_claim_plan_access_without_resource_permission(service):
    connection, transport = service
    transport.scope = "openid " + PLAN_SCOPE
    pending = begin(service)
    status = connection.complete_login(pending, callback(pending))
    assert status.connected and not status.sharing
