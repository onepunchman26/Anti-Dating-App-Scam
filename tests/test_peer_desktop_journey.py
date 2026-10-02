"""Real loopback HTTP, DPAPI and Qt journey with synthetic adults and fake model responses."""

import time
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.peer_runtime import LocalPeerNode, PeerSessionStore
from anti_dating_scam_desktop.screens import peer_workbench_screen as ui
from anti_dating_scam_desktop.widgets.peer_profile_dialog import MatchingProfileDialog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from test_peer_coordinator import profile
from test_peer_introduction import SyntheticBackend, report_data, reviewed, seeded

from anti_dating_scam.matchmaking.peer_client import PeerClient, invitation_link


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def server(tmp_path):
    node = LocalPeerNode(tmp_path / "node", port=0)
    node.start()
    yield node
    node.stop()
    node.thread.join(5)
    assert not node.thread.is_alive()


def register(server, alias):
    client = PeerClient(server.origin)
    identity = client.call(
        "/peer/register", {"alias": alias, "age": 30, "adult_confirmed": True}, authenticated=False
    )
    client.token = identity["token"]
    client.call(
        "/peer/profile",
        {"expected_version": 0, "profile": profile(alias).model_dump(), "approved": True},
    )
    return client, identity


@pytest.mark.parametrize("language", ["en", "zh"])
def test_qt_live_node_end_to_end(application, tmp_path, monkeypatch, server, language):
    previous = current_language()
    set_language(language, persist=False)
    first, identity = register(server, "Synthetic A")
    second, _ = register(server, "Synthetic B")
    PeerSessionStore(tmp_path).save(server.origin, identity)
    holder = ui.PeerWorkbenchState(origin=server.origin)
    returned = []
    screen = ui.PeerWorkbenchScreen(
        SimpleNamespace(), SimpleNamespace(base_dir=tmp_path), holder, lambda: returned.append(True)
    )
    screen.on_enter()
    monkeypatch.setattr(ui, "run_async", lambda parent, call, done, fail: done(call()))
    monkeypatch.setattr(ui, "review_text", lambda *args, **kwargs: (True, True))
    monkeypatch.setattr(
        ui, "review_ai", lambda parent, backend, request: reviewed(request, backend)
    )
    screen._connect()
    assert identity["member_id"] in screen.member_info.text()
    screen._discover()
    assert screen.candidates.count() == 1
    screen.candidates.setCurrentRow(0)
    assert "Synthetic B" in screen.candidate_detail.toPlainText()
    screen._invite_candidate()
    invite = screen._invitation()
    second.call("/peer/invitation-action", {"invitation": invite, "action": "claim"})
    screen._authorize()
    preview = second.call("/peer/preview", {"invitation": invite})
    second.call(
        "/peer/invitation-action",
        {
            "invitation": invite,
            "action": "approve",
            "allow_cloud_ai": True,
            "expected_versions": preview["versions"],
        },
    )
    prepared = first.call("/peer/prepare", {"invitation": invite})
    backend = SyntheticBackend(report_data(prepared["sources"]))
    monkeypatch.setattr(ui.ai_backend, "get_active", lambda: backend)
    screen._compare()
    assert screen.report.toPlainText() and screen.report_invitation == invite
    assert len(backend.calls) == 1
    # A separate participant corrects their profile while this view is open.
    second.call("/peer/control", {"action": "withdraw", "confirmed": True})

    def synchronous(parent, call, done, fail):
        try:
            result = call()
        except Exception as exc:
            fail(exc)
        else:
            done(result)

    monkeypatch.setattr(ui, "run_async", synchronous)
    screen._check_report()
    assert screen.report.toPlainText() == "" and screen.report_invitation is None
    screen._control("delete")
    assert PeerSessionStore(tmp_path).load(server.origin) is None
    screen.close()
    screen.deleteLater()
    application.processEvents()
    set_language(previous, persist=False)


def test_qt_intro_edit_approve_copy_and_node_change(application, tmp_path, monkeypatch):
    service, _, _, _, response = seeded(tmp_path)
    holder = ui.PeerWorkbenchState(introductions={str(tmp_path): service})
    screen = ui.PeerWorkbenchScreen(
        SimpleNamespace(), SimpleNamespace(base_dir=tmp_path), holder, lambda: None
    )
    screen.on_enter()
    screen.age.setValue(30)
    screen.adult.setChecked(True)
    backend = SyntheticBackend(response)
    monkeypatch.setattr(ui.ai_backend, "get_active", lambda: backend)
    monkeypatch.setattr(
        ui, "review_ai", lambda parent, backend, request: reviewed(request, backend)
    )
    monkeypatch.setattr(ui, "review_text", lambda *args, **kwargs: (True, False))
    monkeypatch.setattr(ui, "run_async", lambda parent, call, done, fail: done(call()))
    screen.format_fields.setText("About me; What I value")
    screen._load_sources()
    screen.sources.item(0).setCheckState(Qt.CheckState.Checked)
    screen._generate_intro()
    assert screen.fields.rowCount() == 2
    screen.fields.item(0, 1).setText("I enjoy reading on weekends.")
    screen._approve_intro()
    screen._copy_intro()
    assert "weekends" in QApplication.clipboard().text()
    screen.fields.item(0, 1).setText("Unapproved edit")
    screen._copy_intro()
    assert "Unapproved edit" not in QApplication.clipboard().text()
    screen.age.setValue(17)
    with pytest.raises(ValueError):
        screen._approved_text()
    screen.age.setValue(30)
    screen._generate_intro()
    assert screen.fields.item(0, 1).text() == "I enjoy reading."
    screen.report.setPlainText("Synthetic old result")
    screen.origin.setText("https://synthetic.invalid")
    assert not screen.report.toPlainText()
    screen.close()
    screen.deleteLater()
    application.processEvents()


def test_multiple_attribute_values_preserved_in_dialog(application):
    supplied = profile().model_dump()
    supplied["attributes"]["interests"] = {"values": ["reading", "music"], "disclose": True}
    supplied["required"]["interests"] = ["reading", "music"]
    dialog = MatchingProfileDialog({"profile": supplied, "alias": "Synthetic", "age": 30})
    dialog.adult.setChecked(True)
    dialog._approve()
    assert dialog.profile.attributes["interests"].values == ["reading", "music"]
    assert dialog.profile.required["interests"] == ["reading", "music"]
    dialog.close()


def test_worker_lifespan_real_tick_and_scoped_session(server, tmp_path):
    for _ in range(100):
        if server.server.config.app.state.peer_worker_status == "running_local":
            break
        time.sleep(0.01)
    assert server.server.config.app.state.peer_worker_status == "running_local"
    _, identity = register(server, "Synthetic worker")
    store = PeerSessionStore(tmp_path)
    store.save(server.origin, identity)
    assert store.load(server.origin)["token"] == identity["token"]
    assert store.load("https://synthetic.invalid") is None
    assert identity["token"].encode() not in store._path(server.origin).read_bytes()
    # Opening a pending link alone does not connect, claim, or authorize.
    holder = ui.PeerWorkbenchState(pending_link=invitation_link(server.origin, "a" * 43))
    assert holder.node is None
