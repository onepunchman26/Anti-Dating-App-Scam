from fastapi.testclient import TestClient
from test_web_companion import Connection

from anti_dating_scam.api.web_companion import SITE_ORIGIN, create_companion_app
from anti_dating_scam.services.web_companion import WebCompanion


def test_local_page_is_not_a_cross_origin_capability_dispenser(tmp_path):
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "index.html").write_text('<meta name="slowmatch-pair" content="__SLOWMATCH_PAIR__">')
    for name in ("app.js", "app.css"):
        (ui / name).write_text("/* synthetic */")
    service = WebCompanion(tmp_path / "state", Connection())
    client = TestClient(
        create_companion_app(service, pairing_token="synthetic-pair", ui_root=ui),
        base_url="http://127.0.0.1:8911",
    )
    health = client.get("/health")
    assert (
        health.json()["ui_ready"]
        and "account" not in health.text
        and "synthetic-pair" not in health.text
    )
    page = client.get("/app")
    assert page.status_code == 200 and "synthetic-pair" in page.text
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    for headers in (
        {"Origin": SITE_ORIGIN},
        {"Origin": "https://evil.test"},
        {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Dest": "iframe"},
        {"Host": "evil.test"},
    ):
        denied = client.get("/app", headers=headers)
        assert denied.status_code == 403 and "synthetic-pair" not in denied.text
    assert (
        client.get(
            "/app",
            headers={
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-User": "?1",
            },
        ).status_code
        == 200
    )
    assert client.get("/assets/app.js").headers["content-type"].startswith("text/javascript")
    assert client.get("/assets/secrets.json").status_code == 404
    assert (
        client.post(
            "/v1",
            json={"operation": "status", "arguments": {}},
            headers={"Origin": "http://127.0.0.1:8911"},
        ).status_code
        == 403
    )
    (ui / "app.js").unlink()
    assert not client.get("/health").json()["ui_ready"]


def test_daily_launcher_reuses_and_rejects_foreign_service(monkeypatch):
    import json

    from anti_dating_scam.services import local_launcher as mod
    from anti_dating_scam.version import build_info

    class Reply:
        status = 200
        data = {"service": "slowmatch-local", "version": build_info()["version"], "ui_ready": True}

        def getresponse(self):
            return self

        def request(self, *args):
            pass

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return json.dumps(self.data).encode()

    reply = Reply()
    monkeypatch.setattr(mod.http.client, "HTTPConnection", lambda *args, **kwargs: reply)
    monkeypatch.setattr(
        mod.subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("duplicate process")),
    )
    assert mod.launch(open_browser=False)["assistant"] == "already_running"
    import pytest

    reply.data["service"] = "another-app"
    with pytest.raises(ValueError, match="local_assistant_not_ready"):
        mod.launch(open_browser=False)
    reply.data["service"] = "slowmatch-local"
    reply.data["version"] = "0.0.1"
    with pytest.raises(ValueError, match="restart_updated_assistant_required"):
        mod.launch(open_browser=False)
