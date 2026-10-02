"""Real Qt voice-to-draft controls with synthetic speech and model transport."""

import json
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.screens import reflection_chat_screen
from anti_dating_scam_desktop.widgets.voice_input_dialog import VoiceInputDialog
from PySide6.QtWidgets import QApplication

from anti_dating_scam.ai.chat_backends import OllamaChatBackend


class Deferred:
    def __init__(self):
        self.pending = []

    def run(self, _owner, call, done, error):
        self.pending.append((call, done, error))

    def finish(self):
        call, done, error = self.pending.pop(0)
        try:
            result = call()
        except Exception:
            error("Synthetic failure")
        else:
            done(result)


class SyntheticSpeech:
    """No installation, microphone or real model directory is touched."""

    @staticmethod
    def model_spec(language):
        return SimpleNamespace(
            language=language,
            download_mb=1,
            license="Synthetic test fixture",
            url="https://example.invalid/synthetic-model.zip",
        )

    @staticmethod
    def model_ready(_language):
        return True

    @staticmethod
    def recognizer_available():
        return True


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def restore_language():
    original = current_language()
    yield
    set_language(original, persist=False)


def chat(monkeypatch, tmp_path, language):
    set_language(language, persist=False)
    calls = []

    def transport(_url, payload, _headers, _timeout):
        calls.append(payload)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "question": {
                            "en": "What helps you feel heard?",
                            "zh": "什么能让你感到被倾听？",
                        },
                    }
                ),
            },
        }

    backend = OllamaChatBackend(model="synthetic-voice-chat", transport=transport)
    deferred = Deferred()
    monkeypatch.setattr(reflection_chat_screen.ai_backend, "get_active", lambda: backend)
    monkeypatch.setattr(reflection_chat_screen, "run_async", deferred.run)
    holder = reflection_chat_screen.ReflectionChatState()
    page = reflection_chat_screen.ReflectionChatScreen(
        None,
        SimpleNamespace(base_dir=tmp_path / "synthetic-vault"),
        holder,
        lambda: None,
        lambda: None,
    )
    page.show()
    page.start_button.click()
    deferred.finish()
    return page, holder, deferred, calls


def install_dialog(monkeypatch, on_open):
    dialogs = []

    def factory(parent, *, language):
        dialog = VoiceInputDialog(parent, language=language, service=SyntheticSpeech())
        dialogs.append(dialog)
        # Exercise the actual signal and editable Qt controls without opening
        # a modal loop or touching any microphone.
        dialog.exec = lambda: on_open(dialog)
        return dialog

    monkeypatch.setattr(reflection_chat_screen, "VoiceInputDialog", factory)
    return dialogs


@pytest.mark.parametrize("language", ["en", "zh"])
def test_voice_signal_only_adds_editable_draft_until_explicit_send(
    application,
    monkeypatch,
    tmp_path,
    language,
):
    page, holder, deferred, calls = chat(monkeypatch, tmp_path, language)

    def recognized(dialog):
        dialog._transcribed("Synthetic recognized phrase.")
        assert not dialog.transcript.isReadOnly()
        dialog.transcript.setPlainText("Synthetic corrected phrase.")
        assert dialog.use_button.text() == ("Use this text" if language == "en" else "使用这些文字")
        dialog.use_button.click()

    dialogs = install_dialog(monkeypatch, recognized)
    try:
        page.input_box.setPlainText("Synthetic typed start.")
        page.voice_button.click()
        assert len(dialogs) == 1 and dialogs[0].language == language
        assert page.voice_button.text() == ("Voice input" if language == "en" else "语音输入")
        assert page.input_box.toPlainText() == (
            "Synthetic typed start.\nSynthetic corrected phrase."
        )
        assert holder.drafts[page._vault] == page.input_box.toPlainText()
        assert not page.input_box.isReadOnly() and page.input_box.isEnabled()
        assert len(calls) == 1 and deferred.pending == []
        assert [item.role for item in page.service.transcript] == ["assistant"]
        assert page.service.portrait is None and not tmp_path.joinpath("synthetic-vault").exists()
        assert (
            "Edit it, then press Send" if language == "en" else "准备好后自行点击发送"
        ) in page.banner.label.text()

        final = "Synthetic final edit chosen by the user."
        page.input_box.setPlainText(final)
        page.send_button.click()
        assert len(calls) == 1 and len(deferred.pending) == 1
        deferred.finish()
        assert len(calls) == 2
        assert [item.content for item in page.service.transcript if item.role == "user"] == [final]
    finally:
        page.close()


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("state", ["busy", "ended"])
def test_late_voice_signal_is_discarded_while_chat_busy_or_ended(
    application,
    monkeypatch,
    tmp_path,
    language,
    state,
):
    page, holder, deferred, calls = chat(monkeypatch, tmp_path, language)

    def late_signal(dialog):
        if state == "busy":
            page.send_button.click()
            assert page._busy
        else:
            page.end_button.click()
            assert not page.service.running
        previous_text = page.input_box.toPlainText()
        previous_transcript = page.service.transcript
        previous_pending = len(deferred.pending)
        dialog._transcribed("Synthetic late recognized words.")
        dialog.use_button.click()
        assert page.input_box.toPlainText() == previous_text
        assert page.service.transcript == previous_transcript
        assert len(deferred.pending) == previous_pending

    dialogs = install_dialog(monkeypatch, late_signal)
    try:
        page.input_box.setPlainText("Synthetic previously typed draft.")
        page.voice_button.click()
        assert len(dialogs) == 1 and len(calls) == 1
        assert "Synthetic late" not in holder.drafts[page._vault]
        assert all("Synthetic late" not in item.content for item in page.service.transcript)
        assert not page.voice_button.isEnabled()
        if state == "busy":
            deferred.finish()
            assert len(calls) == 2
        else:
            assert deferred.pending == []
    finally:
        page.close()


@pytest.mark.parametrize("language", ["en", "zh"])
def test_cancel_voice_keeps_typed_draft_and_does_not_send(
    application,
    monkeypatch,
    tmp_path,
    language,
):
    page, holder, deferred, calls = chat(monkeypatch, tmp_path, language)

    def cancel(dialog):
        dialog._transcribed("Synthetic unused voice words.")
        dialog.cancel_button.click()

    install_dialog(monkeypatch, cancel)
    try:
        page.input_box.setPlainText("Synthetic typed draft stays.")
        page.voice_button.click()
        assert (
            page.input_box.toPlainText()
            == holder.drafts[page._vault]
            == "Synthetic typed draft stays."
        )
        assert len(calls) == 1 and deferred.pending == []
        assert [item.role for item in page.service.transcript] == ["assistant"]
    finally:
        page.close()
