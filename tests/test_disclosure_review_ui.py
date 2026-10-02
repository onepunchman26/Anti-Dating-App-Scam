"""Exercise the actual modal consent control without making any model calls."""

import json

import pytest
from anti_dating_scam_desktop.disclosure_review import review_request
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QPlainTextEdit

from anti_dating_scam.ai.chat_backends import AnthropicChatBackend, OllamaChatBackend
from anti_dating_scam.ai.privacy import ChatRequest


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def test_external_dialog_sends_only_edited_data(application):
    backend = AnthropicChatBackend(api_key="synthetic-not-a-real-key")
    request = ChatRequest(
        messages=[{"role": "user", "content": "synthetic.private@example.test"}],
        system="Trusted reflection instructions.",
    )

    def approve():
        dialog = application.activeModalWidget()
        editor = next(item for item in dialog.findChildren(QPlainTextEdit)
                      if not item.isReadOnly())
        editor.setPlainText(json.dumps([{"role": "user", "content": "Minimal summary"}]))
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).click()

    QTimer.singleShot(20, approve)
    approved = review_request(None, backend, request)
    assert approved.privacy_mode == "reviewed_remote"
    assert approved.disclosure.messages[0].content == "Minimal summary"
    assert "synthetic.private@example.test" not in approved.model_dump_json()


def test_external_dialog_cancellation_returns_no_request(application):
    QTimer.singleShot(20, lambda: application.activeModalWidget().reject())
    result = review_request(None, AnthropicChatBackend(api_key="synthetic"), ChatRequest(
        messages=[{"role": "user", "content": "Synthetic text"}],
    ))
    assert result is None


def test_local_request_needs_no_external_disclosure_dialog(application):
    request = ChatRequest(messages=[{"role": "user", "content": "Local only"}])
    assert review_request(None, OllamaChatBackend(), request) is request
