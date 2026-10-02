"""Explicit offline microphone capture; recognized text is editable, never sent."""

from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSource, QMediaDevices
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from anti_dating_scam.services import voice_input
from anti_dating_scam_desktop.i18n import bi, current_language
from anti_dating_scam_desktop.workers import run_async

_FORMATS = {
    QAudioFormat.SampleFormat.Int16: "int16",
    QAudioFormat.SampleFormat.Int32: "int32",
    QAudioFormat.SampleFormat.Float: "float32",
    QAudioFormat.SampleFormat.UInt8: "uint8",
}


class VoiceInputDialog(QDialog):
    """User starts/stops capture; caller receives text only after Use text."""

    transcript_ready = Signal(str)

    def __init__(self, parent=None, *, language: str | None = None, service=voice_input):
        super().__init__(parent)
        self.setObjectName("voice_input_dialog")
        self.setWindowTitle(bi("Voice input", "语音输入"))
        self.resize(580, 430)
        self.service = service
        self._source = None
        self._io = None
        self._capture_format = None
        self._recording = False
        self._busy = False
        self._activity = ""
        self._close_after_worker = False
        self._download_cancel = threading.Event()
        self._download_bytes = 0
        self._audio = bytearray()
        self._overflow_stop_scheduled = False

        layout = QVBoxLayout(self)
        title = QLabel(bi(
            "Recording starts only when you press Start. Speech stays on this device. "
            "Review and edit the words before using them; nothing is sent automatically.",
            "只有点击“开始录音”才会录音。语音留在本机。使用前请检查和修改文字；不会自动发送。",
        ))
        title.setWordWrap(True)
        title.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(title)

        self.language_choice = QComboBox()
        self.language_choice.setObjectName("voice_language")
        self.language_choice.addItem(bi("English", "英语"), "en")
        self.language_choice.addItem(bi("Simplified Chinese", "简体中文"), "zh")
        selected = "zh" if (language or current_language()).startswith("zh") else "en"
        self.language_choice.setCurrentIndex(self.language_choice.findData(selected))
        self.language_choice.currentIndexChanged.connect(self._refresh_model_status)
        layout.addWidget(self.language_choice)

        self.model_note = QLabel()
        self.model_note.setWordWrap(True)
        self.model_note.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.model_note)
        self.install_button = QPushButton()
        self.install_button.setProperty("actionKind", "primary")
        self.install_button.setObjectName("voice_install_model")
        self.install_button.clicked.connect(self._install_model)
        layout.addWidget(self.install_button)

        controls = QHBoxLayout()
        self.start_button = QPushButton(bi("Start recording", "开始录音"))
        self.start_button.setProperty("actionKind", "primary")
        self.start_button.setObjectName("voice_start_recording")
        self.start_button.clicked.connect(self._start_recording)
        controls.addWidget(self.start_button)
        self.stop_button = QPushButton(bi("Stop and transcribe", "停止并转成文字"))
        self.stop_button.setProperty("actionKind", "secondary")
        self.stop_button.setObjectName("voice_stop_recording")
        self.stop_button.clicked.connect(self._stop_recording)
        controls.addWidget(self.stop_button)
        layout.addLayout(controls)

        self.status = QLabel()
        self.status.setObjectName("voice_status")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.transcript = QPlainTextEdit()
        self.transcript.setObjectName("voice_transcript")
        self.transcript.setPlaceholderText(bi(
            "Recognized words appear here. You can edit them.",
            "识别出的文字会显示在这里，可直接修改。",
        ))
        self.transcript.textChanged.connect(self._controls)
        layout.addWidget(self.transcript, 1)

        actions = QHBoxLayout()
        self.use_button = QPushButton(bi("Use this text", "使用这些文字"))
        self.use_button.setProperty("actionKind", "primary")
        self.use_button.setObjectName("voice_use_text")
        self.use_button.clicked.connect(self._use_text)
        actions.addWidget(self.use_button)
        self.cancel_button = QPushButton(bi("Cancel", "取消"))
        self.cancel_button.setProperty("actionKind", "secondary")
        self.cancel_button.setObjectName("voice_cancel")
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)

        self._limit_timer = QTimer(self)
        self._limit_timer.setSingleShot(True)
        self._limit_timer.timeout.connect(self._stop_recording)
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(250)
        self._progress_timer.timeout.connect(self._show_progress)
        self._refresh_model_status()

    @property
    def language(self) -> str:
        return self.language_choice.currentData()

    def _set_status(self, english: str, chinese: str) -> None:
        self.status.setText(bi(english, chinese))

    def _controls(self) -> None:
        ready = self.service.model_ready(self.language)
        available = self.service.recognizer_available()
        self.language_choice.setEnabled(not self._recording and not self._busy)
        self.install_button.setEnabled(
            not self._recording and not self._busy and available and not ready
        )
        self.start_button.setEnabled(not self._recording and not self._busy and available and ready)
        self.stop_button.setEnabled(self._recording)
        self.use_button.setEnabled(not self._recording and not self._busy and bool(
            self.transcript.toPlainText().strip()
        ))

    def _refresh_model_status(self) -> None:
        spec = self.service.model_spec(self.language)
        self.model_note.setText(bi(
            f"Offline {spec.language.upper()} model: about {spec.download_mb} MB, "
            f"{spec.license}, from {spec.url}. Download happens only if you click below.",
            f"离线{('英语' if spec.language == 'en' else '中文')}模型：约 {spec.download_mb} MB，"
            f"{spec.license} 许可，来源 {spec.url}。只有点击下方按钮才会下载。",
        ))
        self.install_button.setText(bi("Download offline model", "下载离线模型"))
        if not self.service.recognizer_available():
            self._set_status(
                "The offline speech component is missing from this installation.",
                "当前安装缺少离线语音组件。",
            )
        elif self.service.model_ready(self.language):
            self._set_status(
                "Offline model ready. No microphone is opened until you press Start.",
                "离线模型已就绪。点击“开始录音”前不会打开麦克风。",
            )
        else:
            self._set_status(
                "Install this language model once before recording.",
                "首次录音前，请先安装这个语言的模型。",
            )
        self._controls()

    def _install_model(self) -> None:
        if self._busy or self._recording or self.service.model_ready(self.language):
            return
        language = self.language
        self._download_cancel.clear()
        self._download_bytes = 0
        self._busy = True
        self._activity = "download"
        self._controls()
        self._set_status("Downloading the official model…", "正在下载官方模型……")
        self._progress_timer.start()

        def work():
            return self.service.install_model(
                language,
                progress=lambda count: setattr(self, "_download_bytes", count),
                cancel=self._download_cancel,
            )

        run_async(self, work, self._installed, self._work_failed)

    def _show_progress(self) -> None:
        amount = self._download_bytes / 1_000_000
        self._set_status(
            f"Downloading the official model… {amount:.1f} MB received.",
            f"正在下载官方模型……已接收 {amount:.1f} MB。",
        )

    def _installed(self, _path) -> None:
        self._busy = False
        self._activity = ""
        self._progress_timer.stop()
        self._refresh_model_status()
        self._finish_if_closing()

    def _work_failed(self, error: str) -> None:
        activity = self._activity
        self._busy = False
        self._activity = ""
        self._progress_timer.stop()
        if activity == "download":
            self._set_status(
                "The offline model could not be installed. Check your connection and try again.",
                "离线模型未能安装。请检查网络连接后重试。",
            )
        else:
            self._set_status(
                "Speech could not be recognized. Try again or type your answer.",
                "语音未能识别。请重试或直接输入回答。",
            )
        self._controls()
        self._finish_if_closing()

    def _start_recording(self) -> None:
        if self._busy or self._recording or not self.service.model_ready(self.language):
            return
        devices = QMediaDevices.audioInputs()
        if not devices:
            self._set_status(
                "No microphone was detected. Connect one and try again; you can still type.",
                "未检测到麦克风。连接后可重试，也可以直接打字。",
            )
            return
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            self._set_status(
                "No microphone was detected. Connect one and try again; you can still type.",
                "未检测到麦克风。连接后可重试，也可以直接打字。",
            )
            return
        requested = QAudioFormat()
        requested.setSampleRate(voice_input.SAMPLE_RATE)
        requested.setChannelCount(1)
        requested.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        capture_format = (
            requested if device.isFormatSupported(requested) else device.preferredFormat()
        )
        if (
            capture_format.sampleFormat() not in _FORMATS
            or not 8_000 <= capture_format.sampleRate() <= 96_000
            or not 1 <= capture_format.channelCount() <= 2
        ):
            self._set_status(
                "This microphone format is not supported for offline transcription.",
                "这个麦克风格式暂不支持离线转写。",
            )
            return
        self._capture_format = capture_format
        try:
            self._source = QAudioSource(device, capture_format, self)
            self._io = self._source.start()
        except Exception:
            if self._source is not None:
                self._source.stop()
                self._source.deleteLater()
            self._source = self._io = None
            self._set_status(
                "The microphone could not start. Check device access and try again.",
                "麦克风无法启动。请检查设备权限后重试。",
            )
            return
        if self._io is None or self._source.error() != QAudio.Error.NoError:
            self._source.stop()
            self._source.deleteLater()
            self._source = self._io = None
            self._set_status(
                "The microphone could not start. Check device access and try again.",
                "麦克风无法启动。请检查设备权限后重试。",
            )
            return
        self._audio.clear()
        self._overflow_stop_scheduled = False
        self._io.readyRead.connect(self._read_audio)
        self._source.stateChanged.connect(self._on_source_state)
        self._recording = True
        self._limit_timer.start(voice_input.MAX_RECORD_SECONDS * 1000)
        self._set_status(
            "Recording locally… Press Stop when finished (30-second limit).",
            "正在本机录音……说完后点击“停止”（最长 30 秒）。",
        )
        self._controls()

    def _read_audio(self) -> None:
        if self._io is None or not self._recording:
            return
        chunk = bytes(self._io.readAll())
        format_ = self._capture_format
        maximum = (
            format_.sampleRate() * format_.channelCount() * format_.bytesPerSample()
            * voice_input.MAX_RECORD_SECONDS
        )
        if len(self._audio) + len(chunk) > maximum:
            frame_bytes = format_.channelCount() * format_.bytesPerSample()
            remaining = maximum - len(self._audio)
            remaining -= remaining % frame_bytes
            self._audio.extend(chunk[:remaining])
            self._set_status(
                "Recording reached the 30-second limit.",
                "录音已达到 30 秒上限。",
            )
            if not self._overflow_stop_scheduled:
                self._overflow_stop_scheduled = True
                QTimer.singleShot(0, self._stop_recording)
            return
        self._audio.extend(chunk)

    def _on_source_state(self, state) -> None:
        if (
            self._recording
            and state == QAudio.State.StoppedState
            and self._source is not None
        ):
            self._discard_recording()
            self._set_status(
                "The microphone stopped unexpectedly. No audio was transcribed.",
                "麦克风意外停止。本次录音未转写。",
            )

    def _discard_recording(self) -> None:
        self._recording = False
        self._limit_timer.stop()
        if self._source is not None:
            self._source.stop()
            self._source.deleteLater()
        self._source = self._io = None
        self._audio.clear()
        self._controls()

    def _stop_recording(self) -> None:
        if not self._recording:
            return
        self._read_audio()
        self._recording = False
        self._limit_timer.stop()
        had_error = self._source.error() != QAudio.Error.NoError
        self._source.stop()
        self._source.deleteLater()
        self._source = self._io = None
        if had_error:
            self._audio.clear()
            self._set_status(
                "The microphone failed. No audio was transcribed.",
                "麦克风发生错误。本次录音未转写。",
            )
            self._controls()
            return
        raw = bytes(self._audio)
        self._audio.clear()
        format_ = self._capture_format
        frame_bytes = format_.channelCount() * format_.bytesPerSample()
        raw = raw[: len(raw) - len(raw) % frame_bytes]
        language = self.language
        self._busy = True
        self._activity = "transcribe"
        self._controls()
        self._set_status("Transcribing locally…", "正在本机转成文字……")

        def work():
            pcm = self.service.normalize_capture(
                raw,
                sample_rate=format_.sampleRate(),
                channels=format_.channelCount(),
                sample_format=_FORMATS[format_.sampleFormat()],
            )
            return self.service.transcribe_pcm(pcm, language=language)

        run_async(self, work, self._transcribed, self._work_failed)

    def _transcribed(self, text: str) -> None:
        self._busy = False
        self._activity = ""
        prior = self.transcript.toPlainText().rstrip()
        self.transcript.setPlainText((prior + " " if prior else "") + text)
        self._set_status(
            "Review and edit the words. Use text adds them to your draft only.",
            "请核对并修改文字。点击“使用这些文字”只会放入草稿。",
        )
        self._controls()
        self._finish_if_closing()

    def _use_text(self) -> None:
        text = self.transcript.toPlainText().strip()
        if self._busy or self._recording or not text:
            return
        self.transcript_ready.emit(text)
        self.accept()

    def _finish_if_closing(self) -> None:
        if self._close_after_worker and not self._busy:
            self.close()

    def reject(self) -> None:
        if self._busy:
            self._download_cancel.set()
            self._close_after_worker = True
            self._set_status("Stopping local work…", "正在停止本机处理……")
            return
        if self._recording:
            self._discard_recording()
        super().reject()

    def closeEvent(self, event) -> None:
        if self._busy:
            self.reject()
            event.ignore()
            return
        if self._recording:
            self.reject()
        super().closeEvent(event)
