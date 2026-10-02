import pytest
from fastapi.testclient import TestClient

from anti_dating_scam.api.rendezvous_app import create_client_app, create_rendezvous_app


@pytest.fixture
def client():
    app = create_client_app()
    calls = []

    # A route with a visible side effect proves rejection precedes execution.
    @app.post("/_boundary_probe")
    def probe():
        calls.append(True)
        return {"ok": True}

    # Static mount is a catch-all; place this synthetic route before it.
    app.router.routes.insert(0, app.router.routes.pop())
    with TestClient(app, base_url="http://127.0.0.1:8471") as session:
        yield session, calls


@pytest.mark.parametrize("origin", [
    "https://attacker.example", "null", "http://127.0.0.1:9999",
    "http://localhost:8471", "http://127.0.0.1:8471.attacker.example",
    "http://127.0.0.1:bad", "http://user@127.0.0.1:8471",
])
def test_foreign_origin_cannot_read_or_write(client, origin):
    session, calls = client
    for method, path in [("GET", "/local/profile/load"), ("POST", "/_boundary_probe")]:
        response = session.request(method, path, headers={"Origin": origin})
        assert response.status_code == 403
        assert "access-control-allow-origin" not in response.headers
    assert calls == []


@pytest.mark.parametrize("headers", [
    {"Host": "attacker.example"},
    {"Host": "127.0.0.1.attacker.example:8471"},
    {"Sec-Fetch-Site": "cross-site"},
    {"Sec-Fetch-Site": "same-site"},
])
def test_rebinding_and_cross_site_requests_fail_before_side_effects(client, headers):
    session, calls = client
    assert session.post("/_boundary_probe", headers=headers).status_code == 403
    assert calls == []


def test_preflight_is_denied(client):
    session, calls = client
    response = session.options("/local/ai/config", headers={
        "Origin": "https://attacker.example",
        "Access-Control-Request-Method": "POST",
    })
    assert response.status_code == 403
    assert calls == []


@pytest.mark.parametrize("headers", [{}, {
    "Origin": "http://127.0.0.1:8471", "Sec-Fetch-Site": "same-origin",
}])
def test_local_requests_work(client, headers):
    session, calls = client
    assert session.get("/", headers=headers).status_code == 200
    assert session.post("/_boundary_probe", headers=headers).status_code == 200
    assert calls == [True]


def test_public_node_keeps_cors_but_never_mounts_local_routes():
    with TestClient(create_rendezvous_app(web_dir=None)) as session:
        response = session.get("/local/profile/load", headers={"Origin": "https://example.test"})
        assert response.status_code == 404
        assert response.headers["access-control-allow-origin"] == "*"
