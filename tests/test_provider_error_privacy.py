import io
import traceback
import urllib.error
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop import ai_backend

from anti_dating_scam.ai import chat_backends


@pytest.mark.parametrize("module", [chat_backends, ai_backend])
@pytest.mark.parametrize("kind", ["http", "connection", "timeout", "json"])
def test_provider_errors_do_not_echo_sensitive_remote_content(monkeypatch, module, kind):
    marker = "SYNTHETIC_PRIVATE_MARKER"

    def fail(*args, **kwargs):
        if kind == "http":
            raise urllib.error.HTTPError(
                "https://example.test/?key=" + marker,
                401,
                marker,
                {},
                io.BytesIO(marker.encode()),
            )
        if kind == "connection":
            raise urllib.error.URLError(marker)
        if kind == "timeout":
            raise TimeoutError(marker)
        return io.BytesIO(marker.encode())

    monkeypatch.setattr(
        chat_backends.urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=fail),
    )
    with pytest.raises(module.BackendError) as caught:
        module._default_http("https://example.test/", {}, {}, 1)
    assert marker not in str(caught.value)
    assert marker not in "".join(traceback.format_exception(caught.value))
    if kind == "http":
        assert "401" in str(caught.value)
