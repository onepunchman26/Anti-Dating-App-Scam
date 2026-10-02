"""Synthetic Qt integration of review, revocation, mode and playback controls."""

from anti_dating_scam_desktop.widgets.relationship_memory_dialog import (
    MemoryCandidateDialog,
    RelationshipMemoryDialog,
)
from PySide6.QtWidgets import QApplication
from test_evolving_personal_model import batch, candidate, enabled
from test_reflection_chat_ui import _QUESTION, _Deferred, _local_backend, _window


def test_candidate_ui_shows_evidence_and_needs_individual_approval(tmp_path):
    app = QApplication.instance() or QApplication([])
    memory = enabled(tmp_path)
    proposed = batch(memory, candidate(), candidate(text="Another bounded preference"))
    dialog = MemoryCandidateDialog(tmp_path, proposed)
    assert not memory.read().entries
    assert "S001" in dialog.details.toPlainText()
    dialog.approve_button.click()
    assert len(memory.read().entries) == 1
    assert not dialog.approve_button.isEnabled()
    dialog.items.setCurrentRow(1)
    dialog.reject_button.click()
    assert len(memory.read().entries) == 1
    dialog.close()
    app.processEvents()


def test_model_inspection_shows_hypothesis_and_rejection(tmp_path):
    app = QApplication.instance() or QApplication([])
    memory = enabled(tmp_path)
    memory.approve(
        batch(
            memory,
            candidate(
                kind="interpretation",
                text="A tentative pattern",
                alternatives=["Different context"],
            ),
        ),
        0,
        confirmed=True,
    )
    dialog = RelationshipMemoryDialog(tmp_path)
    dialog.items.setCurrentRow(0)
    assert "S001" in dialog.details.toPlainText()
    assert "Different context" in dialog.details.toPlainText()
    dialog._change("reject")
    assert memory.read().entries[0].review_status == "rejected"
    dialog.close()
    app.processEvents()


def test_session_only_and_end_interrupt_playback(tmp_path, monkeypatch):
    from anti_dating_scam_desktop.screens import reflection_chat_screen as screen

    app = QApplication.instance() or QApplication([])
    backend, _ = _local_backend(_QUESTION)
    monkeypatch.setattr(screen.ai_backend, "get_active", lambda: backend)
    deferred = _Deferred()
    monkeypatch.setattr(screen, "run_async", deferred.run)
    window, store = _window(tmp_path, monkeypatch)
    try:
        store.create_default_directories()
        memory = enabled(store.base_dir)
        window.navigator.go("reflection_chat")
        chat = window.navigator._screens["reflection_chat"]
        stops = []
        monkeypatch.setattr(chat.playback, "stop", lambda: stops.append(True))
        chat.start_button.click()
        deferred.finish()
        assert chat.speak_button.isEnabled()
        chat.session_only.setChecked(True)
        assert not chat.service._memory.enabled and memory.read().enabled
        chat.end_button.click()
        assert len(stops) >= 3
        assert chat.service.memory_evaluation.evaluation.outcome == "disabled"
    finally:
        window.close()
        app.processEvents()
