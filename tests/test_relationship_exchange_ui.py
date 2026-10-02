"""Real Qt controls around synthetic exchange data and injected AI transports."""

import json
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.navigation import Navigator
from anti_dating_scam_desktop.screens import relationship_exchange_screen as exchange_ui
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QPlainTextEdit,
    QStackedWidget,
)
from test_relationship_exchange import _PASSWORD, _USER_TEXT, _saved_reflection

from anti_dating_scam.ai.chat_backends import OllamaChatBackend
from anti_dating_scam.ai.privacy import build_reviewed_request
from anti_dating_scam.services.relationship_exchange import (
    RelationshipExchangeService,
    import_relationship_file,
)


class _Deferred:
    def __init__(self):
        self.pending = []

    def run(self, _owner, call, done, error):
        self.pending.append((call, done, error))

    def finish(self):
        call, done, error = self.pending.pop(0)
        try:
            done(call())
        except Exception as exc:
            error(str(exc))


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def language_restore():
    language = current_language()
    yield
    set_language(language, persist=False)


def _settle(application):
    for _ in range(5):
        application.processEvents()


def _files(tmp_path):
    first, second = tmp_path / "synthetic-a", tmp_path / "synthetic-b"
    first.mkdir()
    second.mkdir()
    own_vault, saved = _saved_reflection(first)
    other_vault, other_saved = _saved_reflection(second)
    own_service, other_service = (
        RelationshipExchangeService(own_vault),
        RelationshipExchangeService(other_vault),
    )
    own = own_service.prepare_export(saved.session_id)
    other = other_service.prepare_export(other_saved.session_id)
    own_file, other_file = tmp_path / "own.slowmatch", tmp_path / "other.slowmatch"
    own_service.export_file(own, own_file, _PASSWORD, confirmed=True)
    other_service.export_file(other, other_file, _PASSWORD, confirmed=True)
    return own_vault, saved, own_file, other_file, own.packet, other.packet


def _pair(en, zh):
    return {"en": en, "zh": zh}


def _comparison_response():
    quote = "The user may prefer calm communication."
    return {
        "schema_version": "1.0",
        "origin": "ai_discussion",
        "basis": "unverified_shared_reflection_summaries",
        "possible_common_ground": [
            {
                "text": _pair(
                    "Both summaries may offer a starting point to discuss calm communication.",
                    "双方摘要可能提供一个讨论平静沟通的起点。",
                ),
                "evidence": [
                    {"source": "A001", "quote": quote},
                    {"source": "B001", "quote": quote},
                ],
                "confidence": "low",
            }
        ],
        "possible_tensions": [],
        "risk_considerations": [],
        "conversation_questions": [
            _pair("How could we arrange a respectful pause?", "我们可以怎样商量尊重彼此的暂停？")
        ],
        "unknowns": [
            _pair("Actual behavior together remains unknown.", "双方实际相处行为仍不清楚。")
        ],
        "caveats": [
            _pair(
                "A tentative discussion based only on unverified shared summaries.",
                "仅基于未经核实的共享摘要作暂定讨论。",
            )
        ],
    }


def _local(hook=None):
    calls = []

    def transport(_url, payload, _headers, _timeout):
        calls.append(payload)
        if hook is not None:
            hook()
        return {"message": {"content": json.dumps(_comparison_response(), ensure_ascii=False)}}

    return OllamaChatBackend(model="synthetic-exchange-ui-only", transport=transport), calls


class _Remote:
    name = "Synthetic reviewed provider"
    recipient = "https://synthetic.invalid/comparison"

    def __init__(self):
        self.calls = []

    def chat(self, request):
        self.calls.append(request)
        return json.dumps(_comparison_response(), ensure_ascii=False)


def _approve(request, backend):
    approved = build_reviewed_request(
        request.messages, system=request.system, recipient=backend.recipient
    )
    return approved.model_copy(
        update={
            "response_schema": request.response_schema,
            "allow_schema_fallback": False,
        }
    )


def _screen(vault, *, backend=None, holder=None, deferred=None, reviewer=None):
    holder = holder or exchange_ui.RelationshipExchangeState()
    deferred = deferred or _Deferred()
    store = SimpleNamespace(base_dir=vault)
    screen = exchange_ui.RelationshipExchangeScreen(
        SimpleNamespace(),
        store,
        holder,
        lambda: None,
        backend_getter=lambda: backend,
        async_runner=deferred.run,
        reviewer=reviewer or (lambda _parent, _backend, prepared: prepared.request),
    )
    return screen, holder, store, deferred


def _load_pair(screen, own, other):
    screen.own_consent.setChecked(True)
    screen.other_consent.setChecked(True)
    screen.holder.own_packet, screen.holder.other_packet = own, other
    screen._render()
    screen._controls()


def _contents(directory):
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_constructor_does_not_read_vault_or_provider(tmp_path, monkeypatch, application):
    vault = tmp_path / "unselected-folder"
    forbidden = []

    def unexpected(*_args, **_kwargs):
        forbidden.append(True)
        raise AssertionError("No data may be read while constructing all application pages.")

    monkeypatch.setattr(exchange_ui, "list_saved_reflections", unexpected)
    screen, holder, _store, deferred = _screen(vault)
    try:
        assert not forbidden
        assert not vault.exists()
        assert screen.saved_picker.count() == 0
        assert holder.vault_key is None
        assert holder.own_packet is holder.other_packet is None
        assert deferred.pending == []
        assert not screen.compare_button.isEnabled()
    finally:
        screen.close()


def test_selected_preview_export_requires_explicit_share_consent(
    tmp_path,
    monkeypatch,
    application,
):
    vault, saved, _own_path, _other_path, packet, _other = _files(tmp_path)
    before = _contents(vault)
    backend = _Remote()
    screen, holder, _store, _deferred = _screen(vault, backend=backend)
    destination = tmp_path / "manual-email-attachment.slowmatch"
    monkeypatch.setattr(screen, "_password", lambda: _PASSWORD)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_a, **_k: (str(destination), ""))
    try:
        screen.on_enter()
        assert holder.own_packet is None
        assert not screen.export_button.isEnabled()
        screen.saved_picker.setCurrentIndex(screen.saved_picker.findData(saved.session_id))
        screen.prepare_button.click()
        assert holder.own_packet.items == packet.items
        assert "calm communication" in screen.own_preview.toPlainText()
        assert _USER_TEXT not in screen.own_preview.toPlainText()
        assert not screen.export_button.isEnabled()
        screen._export()
        assert not destination.exists()
        screen.export_consent.setChecked(True)
        assert screen.export_button.isEnabled()
        screen.export_button.click()
        assert import_relationship_file(destination, _PASSWORD, confirmed=True) == holder.own_packet
        assert b"calm communication" not in destination.read_bytes()
        assert _contents(vault) == before
        assert backend.calls == []
        assert "attach" in screen.banner.label.text()
    finally:
        screen.close()


def test_export_wrong_password_and_existing_destination_preserve_files(
    tmp_path,
    monkeypatch,
    application,
):
    vault, saved, _own_path, _other_path, _packet, _other = _files(tmp_path)
    destination = tmp_path / "already-owned.slowmatch"
    destination.write_bytes(b"synthetic-existing-file-do-not-overwrite")
    screen, _holder, _store, _deferred = _screen(vault)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_a, **_k: (str(destination), ""))
    try:
        screen.on_enter()
        screen.saved_picker.setCurrentIndex(screen.saved_picker.findData(saved.session_id))
        screen.prepare_button.click()
        screen.export_consent.setChecked(True)
        for password in ("short", _PASSWORD):
            monkeypatch.setattr(screen, "_password", lambda selected=password: selected)
            screen.export_button.click()
            assert destination.read_bytes() == b"synthetic-existing-file-do-not-overwrite"
            assert "could not export" in screen.banner.label.text().lower()
    finally:
        screen.close()


def test_manual_import_requires_each_permission_and_stays_in_memory(
    tmp_path,
    monkeypatch,
    application,
):
    vault, _saved, own_path, other_path, own, other = _files(tmp_path)
    before = _contents(tmp_path)
    backend = _Remote()
    screen, holder, _store, _deferred = _screen(vault, backend=backend)
    selected = []

    def select(*_args, **_kwargs):
        selected.append(True)
        return str(own_path if len(selected) == 1 else other_path), ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", select)
    monkeypatch.setattr(screen, "_password", lambda: _PASSWORD)
    try:
        screen.on_enter()
        screen._import_file(own=True)
        screen._import_file(own=False)
        assert selected == []
        screen.own_consent.setChecked(True)
        screen.import_own_button.click()
        assert holder.own_packet == own
        assert holder.other_packet is None
        assert not screen.compare_button.isEnabled()
        screen.other_consent.setChecked(True)
        screen.import_other_button.click()
        assert holder.other_packet == other
        assert screen.compare_button.isEnabled()
        assert (
            _USER_TEXT not in screen.own_preview.toPlainText() + screen.other_preview.toPlainText()
        )
        assert holder.prepared_export is None
        assert not screen.export_button.isEnabled()
        assert backend.calls == []
        assert _contents(tmp_path) == before
    finally:
        screen.close()


@pytest.mark.parametrize("failure", ["bad-password", "tampered", "cancel-file", "cancel-password"])
def test_failed_or_canceled_import_preserves_selected_packets(
    tmp_path,
    monkeypatch,
    application,
    failure,
):
    vault, _saved, own_path, other_path, own, other = _files(tmp_path)
    if failure == "tampered":
        data = bytearray(other_path.read_bytes())
        data[-1] ^= 1
        other_path.write_bytes(data)
    before = _contents(tmp_path)
    screen, holder, _store, _deferred = _screen(vault)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_a, **_k: (
            "" if failure == "cancel-file" else str(other_path),
            "",
        ),
    )
    monkeypatch.setattr(
        screen,
        "_password",
        lambda: (
            None
            if failure == "cancel-password"
            else "incorrect-but-long-password"
            if failure == "bad-password"
            else _PASSWORD
        ),
    )
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.import_other_button.click()
        assert holder.own_packet == own
        assert holder.other_packet == other
        assert _contents(tmp_path) == before
        if failure in {"bad-password", "tampered"}:
            assert "Could not open" in screen.banner.label.text()
        assert own_path.exists()
    finally:
        screen.close()


def test_local_compare_is_one_reviewed_call_with_readable_quoted_result(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend, calls = _local()
    reviews = []

    def review(_parent, _backend, prepared):
        reviews.append(prepared)
        return prepared.request

    screen, holder, _store, deferred = _screen(vault, backend=backend, reviewer=review)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        assert len(reviews) == len(deferred.pending) == 1
        assert calls == []
        assert screen.stop_button.isEnabled()
        assert not screen.compare_button.isEnabled()
        deferred.finish()
        assert len(calls) == 1
        assert holder.report.origin == "ai_discussion"
        assert "calm communication" in screen.result_view.toPlainText()
        assert "Actual behavior together remains unknown." in screen.result_view.toPlainText()
        assert _USER_TEXT not in json.dumps(calls, ensure_ascii=False)
        assert not screen.stop_button.isEnabled()
    finally:
        screen.close()


def test_remote_compare_sends_only_exact_approved_request(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend = _Remote()
    approved = []
    prepared_requests = []

    def review(_parent, recipient, prepared):
        prepared_requests.append(prepared.request)
        exact = _approve(prepared.request, recipient)
        approved.append(exact)
        return exact

    screen, holder, _store, deferred = _screen(vault, backend=backend, reviewer=review)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        assert backend.calls == []
        deferred.finish()
        assert len(backend.calls) == 1
        request = backend.calls[0]
        assert request == approved[0]
        assert request.messages == prepared_requests[0].messages
        assert request.system == prepared_requests[0].system
        assert request.response_schema == prepared_requests[0].response_schema
        assert request.allow_schema_fallback is False
        assert _USER_TEXT not in request.model_dump_json()
        assert holder.report.origin == "ai_discussion"
    finally:
        screen.close()


@pytest.mark.parametrize("decision", ["cancel", "changed-system", "changed-schema"])
def test_remote_cancel_or_changed_disclosure_never_calls_provider(tmp_path, application, decision):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend = _Remote()

    def review(_parent, recipient, prepared):
        if decision == "cancel":
            return None
        exact = _approve(prepared.request, recipient)
        return exact.model_copy(
            update={"system": "unreviewed replacement"}
            if decision == "changed-system"
            else {"response_schema": {"type": "object"}}
        )

    screen, holder, _store, deferred = _screen(vault, backend=backend, reviewer=review)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        if decision == "cancel":
            assert deferred.pending == []
            assert "Nothing was sent" in screen.banner.label.text()
        else:
            deferred.finish()
            assert "No AI result was accepted" in screen.banner.label.text()
        assert backend.calls == []
        assert holder.report is None
        assert holder.own_packet == own
        assert holder.other_packet == other
    finally:
        screen.close()


@pytest.mark.parametrize("timing", ["before-transport", "during-transport", "late-delivery"])
def test_stop_discards_pending_and_late_results(tmp_path, application, timing):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    screen = None
    backend, calls = _local(lambda: screen._stop() if timing == "during-transport" else None)
    screen, holder, _store, deferred = _screen(vault, backend=backend)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        cancel = holder.cancel_event
        if timing == "late-delivery":
            call, done, _error = deferred.pending.pop()
            report = call()
            screen.stop_button.click()
            done(report)
        else:
            if timing == "before-transport":
                screen.stop_button.click()
            deferred.finish()
        assert cancel.is_set()
        assert holder.report is None
        assert screen.result_view.toPlainText() == ""
        assert len(calls) == (0 if timing == "before-transport" else 1)
        assert not screen.stop_button.isEnabled()
        assert screen.compare_button.isEnabled()
    finally:
        screen.close()


@pytest.mark.parametrize("change", ["own-consent", "other-consent", "own-packet", "other-packet"])
def test_changed_permissions_or_packet_during_review_require_fresh_approval(
    tmp_path,
    application,
    change,
):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend = _Remote()

    def review(parent, recipient, prepared):
        exact = _approve(prepared.request, recipient)
        if change.endswith("consent"):
            checkbox = parent.own_consent if change == "own-consent" else parent.other_consent
            checkbox.setChecked(False)
        else:
            packet = (
                parent.holder.own_packet if change == "own-packet" else parent.holder.other_packet
            )
            packet.unknowns[0].en = "Synthetic changed summary requires a fresh review."
        return exact

    screen, holder, _store, deferred = _screen(vault, backend=backend, reviewer=review)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        assert deferred.pending == []
        assert backend.calls == []
        assert holder.report is None
        assert not screen.stop_button.isEnabled()
        assert "permissions first" in screen.banner.label.text()
    finally:
        screen.close()


def test_provider_failure_does_not_automatically_generate_offline_result(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)

    class Unavailable(_Remote):
        def chat(self, request):
            self.calls.append(request)
            raise ValueError("Synthetic unavailable transport.")

    backend = Unavailable()
    screen, holder, _store, deferred = _screen(
        vault,
        backend=backend,
        reviewer=lambda _parent, recipient, prepared: _approve(prepared.request, recipient),
    )
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        deferred.finish()
        assert len(backend.calls) == 1
        assert holder.report is None
        assert screen.result_view.toPlainText() == ""
        assert "No AI result was accepted" in screen.banner.label.text()
    finally:
        screen.close()


def test_revoked_permission_cancels_pending_and_clears_other_packet(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend, calls = _local()
    screen, holder, _store, deferred = _screen(vault, backend=backend)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        screen.other_consent.setChecked(False)
        deferred.finish()
        assert calls == []
        assert holder.other_packet is None
        assert holder.report is None
        assert screen.other_preview.toPlainText() == ""
        assert not screen.compare_button.isEnabled()
        assert not screen.import_other_button.isEnabled()
    finally:
        screen.close()


def test_vault_change_forgets_packets_permissions_and_inflight_work(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    next_vault = tmp_path / "another-empty-synthetic-vault"
    next_vault.mkdir()
    backend, calls = _local()
    screen, holder, store, deferred = _screen(vault, backend=backend)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.compare_button.click()
        store.base_dir = next_vault
        screen.on_enter()
        deferred.finish()
        assert calls == []
        assert holder.vault_key == str(next_vault)
        assert holder.own_packet is holder.other_packet is holder.report is None
        assert not screen.own_consent.isChecked()
        assert not screen.other_consent.isChecked()
        assert screen.saved_picker.count() == 1
        assert not screen.compare_button.isEnabled()
        assert not any(next_vault.iterdir())
    finally:
        screen.close()


def test_offline_guide_is_explicit_and_labeled_without_provider_call(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend = _Remote()
    screen, holder, _store, deferred = _screen(vault, backend=backend)
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.offline_button.click()
        assert holder.report.origin == "offline_guidance"
        assert "not an AI analysis" in screen.result_view.toPlainText()
        assert "no AI was called" in screen.banner.label.text()
        assert backend.calls == []
        assert deferred.pending == []
    finally:
        screen.close()


def test_navigation_and_language_rebuild_preserve_only_same_vault_holder(tmp_path, application):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    screen, holder, store, _deferred = _screen(vault)
    second = None
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        screen.offline_button.click()
        screen._stop()
        screen.on_enter()
        assert holder.own_packet == own
        assert holder.other_packet == other
        assert screen.own_consent.isChecked() and screen.other_consent.isChecked()
        set_language("zh", persist=False)
        second, same_holder, _store, _deferred = _screen(vault, holder=holder)
        second.on_enter()
        assert same_holder is holder
        assert "用户可能偏好平静沟通" in second.own_preview.toPlainText()
        assert "并非 AI 分析" in second.result_view.toPlainText()
        assert "导入" in second.import_other_button.text()
        assert store.base_dir == vault
    finally:
        screen.close()
        if second is not None:
            second.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("width", [940, 1100])
def test_bilingual_exchange_form_scrolls_without_widening_window(
    tmp_path,
    application,
    language,
    width,
):
    vault = tmp_path / "empty-synthetic-vault"
    vault.mkdir()
    set_language(language, persist=False)
    screen, _holder, _store, _deferred = _screen(vault)
    shell = QStackedWidget()
    navigation = Navigator(shell)
    navigation.add("exchange", screen)
    shell.resize(width, 700)
    shell.show()
    try:
        navigation.go("exchange")
        _settle(application)
        viewport = navigation._viewports["exchange"]
        assert shell.width() == width
        assert viewport.horizontalScrollBar().maximum() == 0
        assert viewport.verticalScrollBar().maximum() > 0
        viewport.ensureWidgetVisible(screen.result_view)
        _settle(application)
        assert viewport.verticalScrollBar().value() > 0
        assert screen.result_view.isVisible()
        for control in (
            screen.prepare_button,
            screen.export_button,
            screen.import_own_button,
            screen.import_other_button,
            screen.compare_button,
            screen.stop_button,
            screen.offline_button,
        ):
            assert control.objectName().startswith("exchange_")
            assert control.width() > control.fontMetrics().horizontalAdvance(control.text())
        assert ("导出" in screen.export_button.text()) == (language == "zh")
    finally:
        shell.close()


@pytest.mark.parametrize("approve", [True, False])
def test_real_remote_review_dialog_shows_exact_details_and_requires_decision(
    tmp_path,
    application,
    approve,
):
    vault, _saved, _own_path, _other_path, own, other = _files(tmp_path)
    backend = _Remote()
    screen, _holder, _store, _deferred = _screen(vault, backend=backend)
    observed = []
    try:
        screen.on_enter()
        _load_pair(screen, own, other)
        prepared = screen._comparison().prepare(own_consent=True, other_consent=True)

        def decide():
            dialog = application.activeModalWidget()
            assert isinstance(dialog, QDialog)
            editors = dialog.findChildren(QPlainTextEdit)
            observed.extend(editor.toPlainText() for editor in editors)
            buttons = dialog.findChild(QDialogButtonBox)
            buttons.button(
                QDialogButtonBox.StandardButton.Ok
                if approve
                else QDialogButtonBox.StandardButton.Cancel
            ).click()

        QTimer.singleShot(0, decide)
        request = exchange_ui.review_relationship_request(screen, backend, prepared)
        assert len(observed) == 2
        assert backend.recipient in observed[1]
        assert prepared.request.system in observed[1]
        assert prepared.request.messages[0].content in observed[1]
        assert json.dumps(prepared.request.response_schema, ensure_ascii=False) in observed[1]
        assert _USER_TEXT not in "".join(observed)
        assert backend.calls == []
        if approve:
            assert request.messages == prepared.request.messages
            assert request.response_schema == prepared.request.response_schema
            assert request.allow_schema_fallback is False
        else:
            assert request is None
    finally:
        screen.close()
