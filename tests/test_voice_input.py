"""Synthetic offline-voice tests. No microphone, real recording, or HTTP call."""

import io
import json
import os
import stat
import struct
import subprocess
import sys
import threading
import wave
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.widgets import voice_input_dialog
from anti_dating_scam_desktop.widgets.voice_input_dialog import VoiceInputDialog
from PySide6.QtMultimedia import QAudio
from PySide6.QtWidgets import QApplication, QWidget

from anti_dating_scam.services import voice_input


def _archive(name, *, unsafe_name=None, symlink=False):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member in ("am/final.mdl", "conf/model.conf", "graph/HCLr.fst"):
            archive.writestr(f"{name}/{member}", b"synthetic model bytes")
        if unsafe_name:
            info = zipfile.ZipInfo(unsafe_name)
            if symlink:
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, b"synthetic unsafe bytes")
    return buffer.getvalue()


def _spec(monkeypatch, payload):
    import hashlib

    spec = voice_input.ModelSpec(
        "en", "synthetic-model", "https://alphacephei.com/vosk/models/synthetic-model.zip",
        hashlib.sha256(payload).hexdigest(), 1,
    )
    monkeypatch.setitem(voice_input.MODELS, "en", spec)
    return spec


def test_install_requires_explicit_call_and_stores_only_app_model(tmp_path, monkeypatch):
    payload = _archive("synthetic-model")
    _spec(monkeypatch, payload)
    root = tmp_path / "app-speech-models"
    calls = []

    def source(spec):
        calls.append(spec.url)
        return io.BytesIO(payload)

    assert not voice_input.model_ready("en", root=root)
    assert calls == [] and not root.exists()
    installed = voice_input.install_model("en", root=root, source_factory=source)
    assert installed == root / "synthetic-model"
    assert voice_input.model_ready("en", root=root)
    assert calls == [voice_input.MODELS["en"].url]
    assert not list(root.glob(".voice-*"))
    assert voice_input.install_model("en", root=root, source_factory=source) == installed
    assert len(calls) == 1


def test_temporary_model_cleanup_handles_read_only_staging_folder(tmp_path):
    """Windows/OneDrive may mark a downloaded model's staging folder read-only."""
    staging = tmp_path / ".voice-staging"
    nested = staging / "nested"
    nested.mkdir(parents=True)
    (nested / "synthetic.txt").write_text("synthetic", encoding="utf-8")
    staging.chmod(stat.S_IREAD)
    nested.chmod(stat.S_IREAD)

    voice_input._cleanup_temporary(staging, tmp_path)

    assert not staging.exists()


@pytest.mark.parametrize(
    "unsafe,symlink",
    [
        ("synthetic-model/../../outside.txt", False),
        ("synthetic-model/am/linked", True),
        ("other-model/am/final.mdl", False),
        ("synthetic-model/C:/bad", False),
    ],
)
def test_model_archive_rejects_traversal_links_and_wrong_roots(
    tmp_path, monkeypatch, unsafe, symlink
):
    payload = _archive("synthetic-model", unsafe_name=unsafe, symlink=symlink)
    _spec(monkeypatch, payload)
    root = tmp_path / "app-speech-models"
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.install_model(
            "en", root=root, source_factory=lambda _spec: io.BytesIO(payload)
        )
    assert not (root / "synthetic-model").exists()
    assert not (tmp_path / "outside.txt").exists()
    assert not list(root.glob(".voice-*"))


def test_model_archive_and_download_limits_fail_closed(tmp_path, monkeypatch):
    payload = _archive("synthetic-model")
    _spec(monkeypatch, payload)
    root = tmp_path / "app-speech-models"
    monkeypatch.setattr(voice_input, "MAX_ARCHIVE_BYTES", 16)
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.install_model(
            "en", root=root, source_factory=lambda _spec: io.BytesIO(payload)
        )
    assert not list(root.glob(".voice-*"))
    monkeypatch.setattr(voice_input, "MAX_ARCHIVE_BYTES", 100_000_000)
    monkeypatch.setattr(voice_input, "MAX_EXTRACT_BYTES", 5)
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.install_model(
            "en", root=root, source_factory=lambda _spec: io.BytesIO(payload)
        )
    assert not (root / "synthetic-model").exists()


def test_hash_mismatch_or_cancel_never_installs_model(tmp_path, monkeypatch):
    payload = _archive("synthetic-model")
    spec = _spec(monkeypatch, payload)
    root = tmp_path / "app-speech-models"
    monkeypatch.setitem(
        voice_input.MODELS, "en", voice_input.ModelSpec(
            "en", spec.name, spec.url, "0" * 64, 1
        )
    )
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.install_model(
            "en", root=root, source_factory=lambda _spec: io.BytesIO(payload)
        )
    assert not (root / spec.name).exists()
    monkeypatch.setitem(voice_input.MODELS, "en", spec)
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.install_model(
            "en", root=root, cancel=cancelled,
            source_factory=lambda _spec: io.BytesIO(payload),
        )
    assert not (root / spec.name).exists()
    assert not list(root.glob(".voice-*"))


def test_normalize_capture_supports_mic_formats_and_bounds():
    raw = struct.pack("<ff", 0.5, 0.5) * 48_000
    pcm = voice_input.normalize_capture(
        raw, sample_rate=48_000, channels=2, sample_format="float32"
    )
    assert len(pcm) == 16_000 * 2
    assert 16_000 <= struct.unpack_from("<h", pcm)[0] <= 16_500
    assert voice_input.normalize_capture(
        pcm, sample_rate=16_000, channels=1, sample_format="int16"
    ) == pcm
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.normalize_capture(
            b"\x00", sample_rate=16_000, channels=1, sample_format="int16"
        )
    with pytest.raises(voice_input.VoiceInputError):
        voice_input.normalize_capture(
            b"\x00" * (voice_input.MAX_PCM_BYTES + 2),
            sample_rate=16_000, channels=1, sample_format="int16",
        )


def test_transcribe_uses_local_model_and_bounded_pcm_only(tmp_path, monkeypatch):
    root = tmp_path / "app-speech-models"
    path = voice_input.model_path("en", root=root)
    path.mkdir(parents=True)
    monkeypatch.setattr(voice_input, "model_ready", lambda *args, **kwargs: True)
    voice_input._model_cache.clear()
    seen = []

    class Recognizer:
        def __init__(self, model, rate):
            assert model == str(path) and rate == 16_000

        def AcceptWaveform(self, chunk):
            seen.append(chunk)
            return False

        def FinalResult(self):
            return json.dumps({"text": "synthetic spoken words"})

    monkeypatch.setitem(sys.modules, "vosk", SimpleNamespace(
        Model=lambda model_path: str(model_path),
        KaldiRecognizer=Recognizer,
        SetLogLevel=lambda level: None,
    ))
    pcm = b"\x00\x00" * 1_600
    assert voice_input.transcribe_pcm(pcm, language="en", root=root) == "synthetic spoken words"
    assert b"".join(seen) == pcm
    assert not list(path.iterdir())
    voice_input._model_cache.clear()


class _FakeVoiceService:
    SAMPLE_RATE = 16_000
    MAX_RECORD_SECONDS = 30

    @staticmethod
    def model_spec(language):
        return SimpleNamespace(
            language=language, download_mb=40,
            license="Apache-2.0", url="https://alphacephei.com/vosk/models/synthetic.zip",
        )

    @staticmethod
    def model_ready(language):
        return True

    @staticmethod
    def recognizer_available():
        return True


@pytest.mark.parametrize("language", ["en", "zh"])
def test_dialog_does_not_record_or_send_until_user_acts(language):
    app = QApplication.instance() or QApplication([])
    prior = current_language()
    set_language(language, persist=False)
    try:
        dialog = VoiceInputDialog(language=language, service=_FakeVoiceService)
        received = []
        dialog.transcript_ready.connect(received.append)
        assert dialog.objectName() == "voice_input_dialog"
        assert dialog.findChild(type(dialog.start_button), "voice_start_recording")
        assert dialog.findChild(type(dialog.stop_button), "voice_stop_recording")
        assert dialog.findChild(type(dialog.install_button), "voice_install_model")
        assert dialog.findChild(type(dialog.transcript), "voice_transcript")
        assert dialog.findChild(type(dialog.use_button), "voice_use_text")
        assert dialog.findChild(type(dialog.cancel_button), "voice_cancel")
        assert not dialog._recording and dialog._source is None
        assert received == [] and not dialog.use_button.isEnabled()
        dialog._transcribed("synthetic spoken words")
        dialog.transcript.setPlainText("edited synthetic draft")
        assert received == []
        dialog.use_button.click()
        assert received == ["edited synthetic draft"]
        assert dialog.result() == dialog.DialogCode.Accepted
        dialog.deleteLater()
        app.processEvents()
    finally:
        set_language(prior, persist=False)


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("size", [(940, 700), (1100, 760)])
def test_voice_dialog_controls_fit_real_viewports_without_starting_microphone(language, size):
    app = QApplication.instance() or QApplication([])
    prior = current_language()
    set_language(language, persist=False)
    try:
        dialog = VoiceInputDialog(language=language, service=_FakeVoiceService)
        dialog.resize(*size)
        dialog.show()
        app.processEvents()
        assert dialog.size().width() >= size[0] and dialog.size().height() >= size[1]
        for name in (
            "voice_language", "voice_start_recording", "voice_stop_recording",
            "voice_transcript", "voice_use_text", "voice_cancel", "voice_status",
        ):
            child = dialog.findChild(QWidget, name)
            assert child is not None and child.isVisible()
            top_left = child.mapTo(dialog, child.rect().topLeft())
            bottom_right = child.mapTo(dialog, child.rect().bottomRight())
            assert top_left.x() >= 0 and top_left.y() >= 0
            assert bottom_right.x() < dialog.width() and bottom_right.y() < dialog.height()
        assert not dialog._recording and dialog._source is None
        dialog.close()
        dialog.deleteLater()
        app.processEvents()
    finally:
        set_language(prior, persist=False)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_no_microphone_message_is_bilingual_and_never_opens_capture(language, monkeypatch):
    app = QApplication.instance() or QApplication([])
    prior = current_language()
    set_language(language, persist=False)
    monkeypatch.setattr(
        voice_input_dialog, "QMediaDevices", SimpleNamespace(audioInputs=lambda: [])
    )
    try:
        dialog = VoiceInputDialog(language=language, service=_FakeVoiceService)
        dialog.start_button.click()
        assert not dialog._recording and dialog._source is None
        assert ("No microphone" if language == "en" else "未检测到麦克风") in dialog.status.text()
        dialog.deleteLater()
        app.processEvents()
    finally:
        set_language(prior, persist=False)


def test_model_download_only_occurs_after_explicit_button_click(monkeypatch):
    app = QApplication.instance() or QApplication([])

    class Service(_FakeVoiceService):
        ready = False
        calls = []

        @classmethod
        def model_ready(cls, language):
            return cls.ready

        @classmethod
        def install_model(cls, language, *, progress, cancel):
            cls.calls.append(language)
            cls.ready = True
            return "synthetic installed model"

    def immediate(_owner, work, on_ok, _on_error):
        on_ok(work())

    monkeypatch.setattr(voice_input_dialog, "run_async", immediate)
    dialog = VoiceInputDialog(language="en", service=Service)
    assert Service.calls == [] and not dialog.start_button.isEnabled()
    dialog.install_button.click()
    assert Service.calls == ["en"] and dialog.start_button.isEnabled()
    assert not dialog._recording and dialog._source is None
    dialog.deleteLater()
    app.processEvents()


def test_full_audio_buffer_stops_once_without_recursive_stop(monkeypatch):
    app = QApplication.instance() or QApplication([])

    class Service(_FakeVoiceService):
        @staticmethod
        def normalize_capture(raw, **_details):
            return raw

        @staticmethod
        def transcribe_pcm(pcm, *, language):
            assert len(pcm) == voice_input.MAX_PCM_BYTES and language == "en"
            return "synthetic recognized text"

    class Source:
        stops = 0

        def error(self):
            return QAudio.Error.NoError

        def stop(self):
            self.stops += 1

        def deleteLater(self):
            pass

    class Input:
        chunks = [b"\x00" * 8]

        def readAll(self):
            return self.chunks.pop(0) if self.chunks else b""

    class Format:
        def sampleRate(self):
            return 16_000

        def channelCount(self):
            return 1

        def bytesPerSample(self):
            return 2

        def sampleFormat(self):
            return next(key for key, value in voice_input_dialog._FORMATS.items()
                        if value == "int16")

    callbacks = []
    dialog = VoiceInputDialog(language="en", service=Service)
    monkeypatch.setattr(voice_input_dialog, "QTimer", SimpleNamespace(
        singleShot=lambda _ms, callback: callbacks.append(callback)
    ))
    monkeypatch.setattr(
        voice_input_dialog, "run_async",
        lambda _owner, work, on_ok, _on_error: on_ok(work()),
    )
    source = Source()
    dialog._source = source
    dialog._io = Input()
    dialog._capture_format = Format()
    dialog._recording = True
    dialog._audio = bytearray(b"\x00" * (voice_input.MAX_PCM_BYTES - 2))
    dialog._read_audio()
    assert len(dialog._audio) == voice_input.MAX_PCM_BYTES
    assert len(callbacks) == 1 and source.stops == 0
    callbacks[0]()
    assert source.stops == 1 and dialog.transcript.toPlainText() == "synthetic recognized text"
    assert not dialog._recording and dialog._source is None
    dialog.deleteLater()
    app.processEvents()


def test_microphone_error_discards_buffer_and_never_transcribes():
    app = QApplication.instance() or QApplication([])

    class Source:
        stops = 0

        def error(self):
            return QAudio.Error.IOError

        def stop(self):
            self.stops += 1

        def deleteLater(self):
            pass

    dialog = VoiceInputDialog(language="en", service=_FakeVoiceService)
    source = Source()
    dialog._source = source
    dialog._recording = True
    dialog._audio = bytearray(b"synthetic audio bytes")
    dialog._on_source_state(QAudio.State.StoppedState)
    assert source.stops == 1 and dialog._audio == b""
    assert dialog.transcript.toPlainText() == ""
    assert not dialog._recording and dialog._source is None
    assert "stopped unexpectedly" in dialog.status.text()
    dialog.deleteLater()
    app.processEvents()


def test_optional_real_vosk_recognizes_generated_synthetic_tts(tmp_path):
    """Local opt-in smoke: ignored official model plus Windows synthetic voice."""
    if os.name != "nt":
        pytest.skip("Windows System.Speech synthetic TTS is required for this smoke.")
    model_root = Path(__file__).parents[1] / "build" / "voice-models" / "installed"
    if not voice_input.model_ready("en", root=model_root):
        pytest.skip("Ignored, downloaded English model is not installed for this smoke.")
    destination = tmp_path / "synthetic_en.wav"
    quoted = str(destination).replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, "
        "[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, "
        "[System.Speech.AudioFormat.AudioChannel]::Mono); "
        f"$speaker.SetOutputToWaveFile('{quoted}', $format); "
        "$speaker.Speak('I need a little time to think'); $speaker.Dispose()"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert result.returncode == 0
    with wave.open(str(destination), "rb") as audio:
        assert (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (16000, 1, 2)
        pcm = audio.readframes(audio.getnframes())
    text = voice_input.transcribe_pcm(pcm, language="en", root=model_root)
    assert "need a little time" in text
