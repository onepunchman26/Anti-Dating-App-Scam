"""Speech adapter tests use a labelled fake engine, never claim audible acceptance."""

from anti_dating_scam_desktop.speech_playback import SpeechPlayback
from PySide6.QtCore import QLocale, QObject, Signal
from PySide6.QtTextToSpeech import QTextToSpeech
from PySide6.QtWidgets import QApplication


class FakeSpeech(QObject):
    stateChanged = Signal(object)

    def __init__(self):
        super().__init__()
        self.calls = []
        self.stops = []
        self.current = QTextToSpeech.State.Ready

    def availableLocales(self):
        return [QLocale("en_US")]

    def setLocale(self, locale):
        self.locale = locale

    def say(self, text):
        self.calls.append(text)
        self.current = QTextToSpeech.State.Speaking
        self.stateChanged.emit(self.current)

    def state(self):
        return self.current

    def stop(self, hint):
        self.stops.append(hint)
        self.current = QTextToSpeech.State.Ready


def test_optional_playback_can_interrupt_and_restart():
    app = QApplication.instance() or QApplication([])
    engine = FakeSpeech()
    playback = SpeechPlayback(factory=lambda: engine, has_output=lambda: True)
    states = []
    playback.status_changed.connect(states.append)
    assert engine.calls == []
    playback.say("Synthetic spoken answer", "en")
    playback.stop()
    assert engine.stops[-1] == QTextToSpeech.BoundaryHint.Immediate
    assert states[-1] == "stopped"
    playback.say("Another synthetic answer", "en")
    assert len(engine.calls) == 2
    playback.stop()
    app.processEvents()


def test_missing_hardware_or_language_retains_text_fallback():
    app = QApplication.instance() or QApplication([])
    engine = FakeSpeech()
    playback = SpeechPlayback(factory=lambda: engine, has_output=lambda: False)
    states = []
    playback.status_changed.connect(states.append)
    playback.say("Synthetic words", "en")
    assert states[-1] == "error" and not engine.calls
    playback._has_output = lambda: True
    playback.say("合成文字", "zh")
    assert states[-1] == "error" and not engine.calls
    app.processEvents()


def test_engine_error_is_not_a_successful_playback():
    app = QApplication.instance() or QApplication([])
    engine = FakeSpeech()
    playback = SpeechPlayback(factory=lambda: engine, has_output=lambda: True)
    states = []
    playback.status_changed.connect(states.append)
    playback.say("Synthetic answer", "en")
    engine.stateChanged.emit(QTextToSpeech.State.Error)
    assert states[-1] == "error"
    playback.stop()
    app.processEvents()
