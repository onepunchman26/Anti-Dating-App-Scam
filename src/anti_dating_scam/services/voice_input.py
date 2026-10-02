"""Explicit local speech input with pinned, user-installed Vosk models.

Only user-supplied PCM is transcribed. Audio never leaves this process, is not
written to a vault, and is not fed to an AI provider by this service. The model
download is a separate user action with fixed official URLs and archive hashes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import struct
import tempfile
import threading
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from urllib.parse import urlsplit

SAMPLE_RATE = 16_000
MAX_RECORD_SECONDS = 30
MAX_PCM_BYTES = SAMPLE_RATE * 2 * MAX_RECORD_SECONDS
MAX_ARCHIVE_BYTES = 100_000_000
MAX_EXTRACT_BYTES = 120_000_000
MAX_MODEL_FILES = 64
MAX_MODEL_FILE_BYTES = 50_000_000


class VoiceInputError(ValueError):
    """Safe, user-facing error without utterance, token, or raw model data."""


@dataclass(frozen=True)
class ModelSpec:
    language: str
    name: str
    url: str
    sha256: str
    download_mb: int
    license: str = "Apache-2.0"


# Sources and licenses: https://alphacephei.com/vosk/models
# Archive digests were calculated from the fixed official ZIPs on 2026-09-30.
MODELS = {
    "en": ModelSpec(
        "en",
        "vosk-model-small-en-us-0.15",
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498",
        40,
    ),
    "zh": ModelSpec(
        "zh",
        "vosk-model-small-cn-0.22",
        "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
        "3af8b0e7e0f835ae9d414ce5df580237a3cfb08d586c9fbbb0f7ff29ad5b14ba",
        42,
    ),
}

_model_lock = threading.Lock()
_model_cache: dict[str, object] = {}


def model_spec(language: str) -> ModelSpec:
    try:
        return MODELS[language]
    except (KeyError, TypeError):
        raise VoiceInputError("Choose English or Simplified Chinese for voice input.") from None


def default_model_dir() -> Path:
    return Path.home() / ".ai_slowmatch" / "speech_models"


def _safe_path(path: Path) -> None:
    for candidate in (path, *path.parents):
        try:
            details = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            raise VoiceInputError("The local speech-model path could not be checked.") from None
        if stat.S_ISLNK(details.st_mode) or getattr(details, "st_file_attributes", 0) & 0x400:
            raise VoiceInputError("Speech models cannot use linked or redirected paths.")
        if stat.S_ISREG(details.st_mode) and details.st_nlink != 1:
            raise VoiceInputError("Speech-model files cannot have multiple links.")
        if candidate != path and not stat.S_ISDIR(details.st_mode):
            raise VoiceInputError("The speech-model parent must be an ordinary folder.")


def _root(root: Path | None) -> Path:
    selected = Path(root) if root is not None else default_model_dir()
    if ".." in selected.parts:
        raise VoiceInputError("Choose an unambiguous speech-model location.")
    selected = selected.absolute()
    _safe_path(selected)
    return selected


def model_path(language: str, *, root: Path | None = None) -> Path:
    return _root(root) / model_spec(language).name


def model_ready(language: str, *, root: Path | None = None) -> bool:
    spec = model_spec(language)
    try:
        path = model_path(language, root=root)
        for item in (path, path / "am", path / "conf", path / "graph"):
            _safe_path(item)
        marker = path / ".installed_sha256"
        for item in (marker, path / "am" / "final.mdl", path / "conf" / "model.conf"):
            _safe_path(item)
            if not item.is_file():
                return False
        return marker.read_text(encoding="ascii") == spec.sha256
    except (OSError, UnicodeError, VoiceInputError):
        return False


def recognizer_available() -> bool:
    return importlib.util.find_spec("vosk") is not None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise VoiceInputError("Speech-model download redirected unexpectedly.")


def _open_official(spec: ModelSpec):
    parsed = urlsplit(spec.url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "alphacephei.com"
        or parsed.port not in {None, 443}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise VoiceInputError("Only the fixed official Vosk model source is allowed.")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    return opener.open(spec.url, timeout=30)


def _copy_download(
    source: BinaryIO,
    destination: Path,
    spec: ModelSpec,
    progress: Callable[[int], None] | None,
    cancel: threading.Event | None,
) -> None:
    digest = hashlib.sha256()
    total = 0
    with destination.open("wb") as output:
        while True:
            if cancel is not None and cancel.is_set():
                raise VoiceInputError("Speech-model download was cancelled.")
            chunk = source.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise VoiceInputError("Speech-model download exceeded its size limit.")
            digest.update(chunk)
            output.write(chunk)
            if progress is not None:
                progress(total)
        output.flush()
        os.fsync(output.fileno())
    if digest.hexdigest() != spec.sha256:
        raise VoiceInputError("Speech-model download failed its integrity check.")


def _extract_verified_archive(archive: Path, staging: Path, spec: ModelSpec) -> Path:
    """Bound both ZIP metadata and actual extracted bytes; never use extractall."""
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            if len(members) > MAX_MODEL_FILES:
                raise VoiceInputError("Speech-model archive has too many files.")
            if sum(item.file_size for item in members) > MAX_EXTRACT_BYTES:
                raise VoiceInputError("Speech-model archive expands beyond its limit.")
            total_written = 0
            for item in members:
                name = PurePosixPath(item.filename)
                mode = item.external_attr >> 16
                if (
                    not item.filename
                    or "\\" in item.filename
                    or name.is_absolute()
                    or (len(name.parts) < 2 and not (len(name.parts) == 1 and item.is_dir()))
                    or name.parts[0] != spec.name
                    or any(part in {"", ".", ".."} or ":" in part for part in name.parts)
                    or stat.S_ISLNK(mode)
                    or item.file_size > MAX_MODEL_FILE_BYTES
                ):
                    raise VoiceInputError("Speech-model archive contains an unsafe entry.")
                target = staging.joinpath(*name.parts)
                _safe_path(target)
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(item) as source, target.open("xb") as output:
                    while True:
                        chunk = source.read(64 * 1024)
                        if not chunk:
                            break
                        total_written += len(chunk)
                        if total_written > MAX_EXTRACT_BYTES:
                            raise VoiceInputError("Speech-model archive expands beyond its limit.")
                        output.write(chunk)
            directory = staging / spec.name
            for required in ("am/final.mdl", "conf/model.conf", "graph/HCLr.fst"):
                path = directory / required
                _safe_path(path)
                if not path.is_file():
                    raise VoiceInputError("Speech-model archive is incomplete.")
            (directory / ".installed_sha256").write_text(spec.sha256, encoding="ascii")
            return directory
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        raise VoiceInputError("Speech-model archive could not be opened safely.") from None


def _cleanup_temporary(path: Path, root: Path) -> None:
    if path.parent != root or not path.name.startswith(".voice-"):
        raise VoiceInputError("Speech-model cleanup path was invalid.")
    _safe_path(path)
    if path.is_dir():
        def make_writable_and_retry(operation, failed, _error):
            selected = Path(failed).absolute()
            if selected != path and path not in selected.parents:
                raise VoiceInputError("Speech-model cleanup left its temporary folder.")
            _safe_path(selected)
            os.chmod(selected, stat.S_IRWXU)
            operation(failed)

        shutil.rmtree(path, onerror=make_writable_and_retry)
    elif path.exists():
        path.unlink()


def install_model(
    language: str,
    *,
    root: Path | None = None,
    progress: Callable[[int], None] | None = None,
    cancel: threading.Event | None = None,
    source_factory: Callable[[ModelSpec], BinaryIO] | None = None,
) -> Path:
    """Download only after a user click; injectable source supports offline tests."""
    spec = model_spec(language)
    base = _root(root)
    destination = base / spec.name
    if model_ready(language, root=base):
        return destination
    _safe_path(destination)
    if destination.exists():
        raise VoiceInputError("An incomplete model folder exists; remove it before retrying.")
    base.mkdir(parents=True, exist_ok=True)
    _safe_path(base)
    archive: Path | None = None
    staging: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".voice-", suffix=".zip", dir=base)
        os.close(descriptor)
        archive = Path(name)
        staging = Path(tempfile.mkdtemp(prefix=".voice-", dir=base))
        factory = source_factory or _open_official
        with factory(spec) as source:
            _copy_download(source, archive, spec, progress, cancel)
        if cancel is not None and cancel.is_set():
            raise VoiceInputError("Speech-model download was cancelled.")
        extracted = _extract_verified_archive(archive, staging, spec)
        _safe_path(destination)
        os.replace(extracted, destination)
        return destination
    except VoiceInputError:
        raise
    except Exception:
        raise VoiceInputError("The speech model could not be installed locally.") from None
    finally:
        for temporary in (archive, staging):
            if temporary is not None:
                _cleanup_temporary(temporary, base)


def transcribe_pcm(pcm16: bytes, *, language: str, root: Path | None = None) -> str:
    """Recognize at most 30 seconds of 16-kHz mono signed-int16 PCM, in memory."""
    if type(pcm16) is not bytes or not 3_200 <= len(pcm16) <= MAX_PCM_BYTES or len(pcm16) % 2:
        raise VoiceInputError("Record between 0.1 and 30 seconds of voice before transcribing.")
    path = model_path(language, root=root)
    if not model_ready(language, root=root):
        raise VoiceInputError("Install the selected offline language model first.")
    try:
        from vosk import KaldiRecognizer, Model, SetLogLevel
    except ImportError:
        raise VoiceInputError("The offline speech component is not installed.") from None
    try:
        SetLogLevel(-1)
        with _model_lock:
            model = _model_cache.get(str(path))
            if model is None:
                model = Model(str(path))
                _model_cache[str(path)] = model
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        parts = []
        for offset in range(0, len(pcm16), 8_000):
            if recognizer.AcceptWaveform(pcm16[offset : offset + 8_000]):
                parts.append(json.loads(recognizer.Result())["text"])
        parts.append(json.loads(recognizer.FinalResult())["text"])
        transcript = " ".join(part.strip() for part in parts if part.strip())
        if language == "zh":
            transcript = transcript.replace(" ", "")
        if not transcript or len(transcript) > 4_000:
            raise VoiceInputError("No clear speech was recognized. Please type or try again.")
        return transcript
    except VoiceInputError:
        raise
    except Exception:
        raise VoiceInputError("Local speech recognition could not finish.") from None


def normalize_capture(
    raw: bytes, *, sample_rate: int, channels: int, sample_format: str
) -> bytes:
    """Convert a supported microphone format to 16-kHz mono int16 PCM."""
    widths = {"int16": 2, "int32": 4, "float32": 4, "uint8": 1}
    width = widths.get(sample_format)
    if (
        type(raw) is not bytes
        or width is None
        or not 8_000 <= sample_rate <= 96_000
        or not 1 <= channels <= 2
        or len(raw) % (width * channels)
        or len(raw) > sample_rate * channels * width * MAX_RECORD_SECONDS
    ):
        raise VoiceInputError("The microphone returned an unsupported audio format.")
    frames = len(raw) // (width * channels)
    if frames < sample_rate // 10:
        raise VoiceInputError("Record at least a moment of voice before transcribing.")
    if sample_rate == SAMPLE_RATE and channels == 1 and sample_format == "int16":
        return raw
    format_char = {"int16": "h", "int32": "i", "float32": "f", "uint8": "B"}[sample_format]
    samples = struct.iter_unpack("<" + format_char, raw)
    mono = []
    chunk = []
    for (sample,) in samples:
        if sample_format == "int32":
            value = sample / 65536
        elif sample_format == "float32":
            value = sample * 32767 if -1.0 <= sample <= 1.0 else 0
        elif sample_format == "uint8":
            value = (sample - 128) * 256
        else:
            value = sample
        chunk.append(value)
        if len(chunk) == channels:
            mono.append(sum(chunk) / channels)
            chunk.clear()
    output_frames = min(MAX_RECORD_SECONDS * SAMPLE_RATE, round(frames * SAMPLE_RATE / sample_rate))
    output = bytearray(output_frames * 2)
    for index in range(output_frames):
        position = index * sample_rate / SAMPLE_RATE
        left = min(int(position), frames - 1)
        right = min(left + 1, frames - 1)
        fraction = position - left
        value = round(mono[left] * (1 - fraction) + mono[right] * fraction)
        struct.pack_into("<h", output, index * 2, max(-32768, min(32767, value)))
    return bytes(output)
