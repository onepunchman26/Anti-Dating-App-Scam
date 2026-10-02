"""Synthetic lifecycle and evidence-boundary regressions for approved annotations."""

import json

import pytest

from anti_dating_scam.services.reflection_chat import (
    ReflectionChatService,
    ReflectionChatStaleError,
)
from anti_dating_scam.services.relationship_memory import RelationshipMemory


def test_memory_is_empty_until_each_item_is_approved_and_enabled(tmp_path):
    memory = RelationshipMemory(tmp_path / "synthetic")
    assert memory.read().entries == [] and not memory.directory.exists()
    with pytest.raises(ValueError):
        memory.change(0, confirmed=False, action="add", text="Synthetic preference")
    state = memory.change(
        0, confirmed=True, action="add", text="Synthetic: I prefer time to think."
    )
    assert not state.enabled and state.entries[0].source == "manual"
    service = ReflectionChatService()
    service.set_memory(state)
    first = service.begin()
    assert "APPROVED_MEMORY" not in first.request.messages[0].content
    state = memory.change(state.revision, confirmed=True, action="enable")
    service.set_memory(state)
    with pytest.raises(ReflectionChatStaleError):
        service.accept_turn(first.request_id, "{}")
    prepared = service.question_request()
    payload = json.loads(prepared.request.messages[0].content)
    assert payload["APPROVED_MEMORY"][0]["text"] == state.entries[0].text
    assert json.loads(prepared.request.messages[1].content) == {"USER_STATEMENTS": []}
    service.stop()
    assert "APPROVED_MEMORY" not in service.portrait_request().request.messages[0].content


def test_correction_supersession_revoke_export_and_delete(tmp_path):
    memory = RelationshipMemory(tmp_path)
    first = memory.change(0, confirmed=True, action="add", text="Synthetic old preference")
    newer = memory.change(
        first.revision,
        confirmed=True,
        action="correct",
        text="Synthetic corrected preference",
        entry_id=first.entries[0].id,
        kind="interpretation",
    )
    assert newer.entries[0].supersedes == first.entries[0].id
    assert first.entries[0].text not in (memory.directory / "state.json").read_text()
    with pytest.raises(ValueError, match="changed"):
        memory.change(first.revision, confirmed=True, action="enable")
    newer = memory.change(newer.revision, confirmed=True, action="enable")
    revoked = memory.change(newer.revision, confirmed=True, action="revoke")
    assert not revoked.enabled and revoked.entries == newer.entries
    destination = tmp_path / "synthetic-export.json"
    memory.export(destination, confirmed=True)
    with pytest.raises(FileExistsError):
        memory.export(destination, confirmed=True)
    empty = memory.change(
        revoked.revision, confirmed=True, action="delete", entry_id=revoked.entries[0].id
    )
    assert empty.entries == [] and "Synthetic" not in (memory.directory / "state.json").read_text()
    assert destination.exists()  # Never claim to erase an already exported copy.


def test_bounds_and_wrong_entry_cannot_replace_an_approved_note(tmp_path):
    memory = RelationshipMemory(tmp_path)
    state = memory.read()
    for i in range(20):
        state = memory.change(
            state.revision, confirmed=True, action="add", text=f"Synthetic note {i}"
        )
    before = (memory.directory / "state.json").read_bytes()
    for kwargs in (
        {"text": "extra"},
        {"text": "x" * 251},
        {"text": "wrong", "entry_id": state.entries[0].id},
    ):
        with pytest.raises(ValueError):
            memory.change(state.revision, confirmed=True, action="add", **kwargs)
        assert (memory.directory / "state.json").read_bytes() == before
    state = memory.change(state.revision, confirmed=True, action="clear")
    assert not state.enabled and not state.entries


@pytest.mark.parametrize("language", ["en", "zh"])
def test_conversation_can_answer_without_another_question(language):
    service = ReflectionChatService(language)
    first = service.begin()
    response = {
        "reply": {"en": "We can focus on what matters to you.", "zh": "我们可以聊你在意的事情。"},
        "question": None,
    }
    result = service.accept_turn(first.request_id, json.dumps(response))
    assert getattr(result, language) == response["reply"][language]
    followup = service.propose_turn(
        "Synthetic: I changed my mind. I would like to stop pursuing this person."
    )
    assert "Respect a changed goal" in followup.request.system
    reply = {
        "reply": {
            "en": "You can choose to stop. No further contact is necessary.",
            "zh": "你可以选择停止，不必再联系。",
        },
        "question": None,
    }
    service.accept_turn(followup.request_id, json.dumps(reply))
    assert len(service.transcript) == 3
    service.stop()
    request = service.portrait_request()
    assert "No further contact" not in request.request.messages[1].content


def test_memory_dialog_approves_edits_and_revokes(tmp_path):
    from anti_dating_scam_desktop.widgets.relationship_memory_dialog import RelationshipMemoryDialog
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    dialog = RelationshipMemoryDialog(tmp_path)
    dialog.editor.setPlainText("Synthetic note for GUI review")
    dialog._change("add")
    assert len(dialog.state.entries) == 1 and not dialog.state.enabled
    dialog._change("enable")
    dialog.items.setCurrentRow(0)
    dialog.editor.setPlainText("Synthetic corrected note")
    dialog._change("correct")
    assert dialog.state.entries[0].text == "Synthetic corrected note"
    dialog._change("revoke")
    assert not dialog.state.enabled
    dialog.close()
    app.processEvents()


def test_quoted_example_question_does_not_force_a_followup():
    service = ReflectionChatService()
    prepared = service.begin()
    result = service.accept_turn(
        prepared.request_id,
        json.dumps(
            {
                "reply": {
                    "en": 'You could say, "Could we pause and return later?"',
                    "zh": "你可以说：“我们能否暂停，稍后继续？”",
                },
                "question": None,
            }
        ),
    )
    assert "Could we pause" in result.en
