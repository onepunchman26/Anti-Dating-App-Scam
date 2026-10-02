import io
import traceback
import urllib.error
import urllib.request
from types import SimpleNamespace

import pytest

from anti_dating_scam.ai.ollama_provider import (
    OllamaClient,
    OllamaUnavailableError,
    _default_transport,
)
from anti_dating_scam.ai.privacy import BackendError


@pytest.mark.parametrize("url", [
    "https://remote.example.test", "http://192.168.1.8:11434", "file:///tmp/model",
    "http://127.0.0.1:11434?secret=synthetic", "http://user:secret@127.0.0.1:11434",
    "http://127.0.0.1:11434/path", "http://localhost:11434#fragment",
])
def test_legacy_client_rejects_nonlocal_and_decorated_origins_before_transport(url):
    calls = []
    with pytest.raises(OllamaUnavailableError):
        OllamaClient(base_url=url, transport=lambda *args: calls.append(args))
    assert calls == []


@pytest.mark.parametrize("change", ["origin", "cloud-model"])
def test_mutated_legacy_client_cannot_relabel_remote_calls_local(change):
    calls = []
    client = OllamaClient(transport=lambda *args: calls.append(args))
    if change == "origin":
        client.base_url = "https://remote.example.test"
    else:
        client.model = "synthetic:cloud"
    with pytest.raises(OllamaUnavailableError):
        client.generate("synthetic private note")
    assert calls == []


def test_legacy_transport_disables_proxy_and_redirect(monkeypatch):
    handlers = []

    def opener(*supplied):
        handlers.extend(supplied)
        return SimpleNamespace(open=lambda *args, **kwargs: io.BytesIO(b'{"response":"{}"}'))

    monkeypatch.setattr(urllib.request, "build_opener", opener)
    assert _default_transport("http://127.0.0.1:11434/api/generate", {}, 1) == {"response": "{}"}
    assert next(h for h in handlers if isinstance(h, urllib.request.ProxyHandler)).proxies == {}
    redirect = next(h for h in handlers if isinstance(h, urllib.request.HTTPRedirectHandler))
    with pytest.raises(BackendError, match="redirects"):
        redirect.redirect_request(None, None, 302, None, {}, "https://remote.example.test")


def test_legacy_errors_hide_transport_exception_context():
    def fail(*args):
        raise urllib.error.URLError("synthetic-secret-url-and-prompt")

    with pytest.raises(OllamaUnavailableError) as caught:
        OllamaClient(transport=fail).generate("synthetic private prompt")
    formatted = "".join(traceback.format_exception(caught.value))
    assert "synthetic-secret-url-and-prompt" not in formatted


def test_legacy_localhost_normalization_and_structured_response():
    seen = []

    def transport(url, payload, timeout):
        seen.append(url)
        return {"response": '{"summary":"Synthetic local result."}'}

    result = OllamaClient(transport=transport).generate("Synthetic input.")
    assert result.parsed_json == {"summary": "Synthetic local result."}
    assert seen == ["http://127.0.0.1:11434/api/generate"]
