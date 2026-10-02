"""Explicit local OS speech. Never uses an online voice service or retains audio."""

from PySide6.QtCore import QLocale, QObject, Signal
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtTextToSpeech import QTextToSpeech


class SpeechPlayback(QObject):
    status_changed = Signal(str)

    def __init__(self, parent=None, *, factory=None, has_output=None):
        super().__init__(parent)
        self._engine = None
        self._factory = factory
        self._has_output = has_output or (lambda: bool(QMediaDevices.audioOutputs()))

    def _create(self):
        if self._factory:
            return self._factory()
        engines = QTextToSpeech.availableEngines()
        # Explicit OS/offline engines; Qt's mock engine is never a product fallback.
        selected = next((e for e in ("sapi", "darwin", "speechd") if e in engines), None)
        if selected is None:
            raise ValueError("No local speech engine.")
        return QTextToSpeech(selected, self)

    def say(self, text: str, language: str):
        self.stop()
        if not text.strip():
            return
        try:
            if not self._has_output():
                raise ValueError("No audio output device.")
            if self._engine is None:
                self._engine = self._create()
                self._engine.stateChanged.connect(self._state)
            locales = self._engine.availableLocales()
            wanted = QLocale.Language.Chinese if language == "zh" else QLocale.Language.English
            locale = next((loc for loc in locales if loc.language() == wanted), None)
            if locale is None:
                raise ValueError("The chosen language has no installed local voice.")
            self._engine.setLocale(locale)
            self.status_changed.emit("speaking")
            self._engine.say(text)
            if self._engine.state() == QTextToSpeech.State.Error:
                raise ValueError("Speech engine error.")
        except Exception:
            self.stop()
            self.status_changed.emit("error")

    def stop(self):
        if self._engine is not None:
            self._engine.stop(QTextToSpeech.BoundaryHint.Immediate)
        self.status_changed.emit("stopped")

    def _state(self, state):
        if state == QTextToSpeech.State.Error:
            self.status_changed.emit("error")
        elif state == QTextToSpeech.State.Ready:
            self.status_changed.emit("ready")
        elif state == QTextToSpeech.State.Speaking:
            self.status_changed.emit("speaking")
