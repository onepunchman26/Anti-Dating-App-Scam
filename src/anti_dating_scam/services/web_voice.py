"""Bounded, ephemeral dictation on the paired local companion only."""

import base64
import binascii
from typing import Literal

from pydantic import Field

from anti_dating_scam.services import voice_input
from anti_dating_scam.services.web_companion import CompanionError, Input


class VoiceInput(Input):
    language: Literal["en", "zh"]
    confirmed: Literal[True]


class DictationInput(VoiceInput):
    pcm_base64: str = Field(min_length=4268, max_length=1_280_000)


def dispatch(companion, operation, data):
    companion._ready()
    root = companion.state.root.parent / "speech-models"
    if operation == "voice-status":
        if data:
            raise CompanionError("invalid_arguments")
        return {
            "runtime": voice_input.recognizer_available(),
            "max_seconds": voice_input.MAX_RECORD_SECONDS,
            "languages": {
                key: {
                    "ready": voice_input.model_ready(key, root=root),
                    "download_mb": spec.download_mb,
                }
                for key, spec in voice_input.MODELS.items()
            },
        }
    request = (DictationInput if operation == "voice-transcribe" else VoiceInput).model_validate(
        data
    )
    if not companion.lock.acquire(blocking=False):
        raise CompanionError("request_in_progress")
    try:
        vault = companion._ready()
        companion.cancel.clear()
        if not voice_input.recognizer_available():
            raise CompanionError("voice_runtime_missing")
        if operation == "voice-install":
            voice_input.install_model(request.language, root=root, cancel=companion.cancel)
            result = {"ready": True}
        else:
            try:
                pcm = base64.b64decode(request.pcm_base64, validate=True)
            except (ValueError, binascii.Error):
                raise CompanionError("voice_invalid_audio") from None
            text = voice_input.transcribe_pcm(
                pcm, language=request.language, root=root, cancel=companion.cancel
            )
            result = {"text": text, "stored": False, "cloud": False}
        if companion._ready().root != vault.root or companion.cancel.is_set():
            raise CompanionError("cancelled")
        return result
    except voice_input.VoiceInputError:
        raise CompanionError(
            "voice_cancelled" if companion.cancel.is_set() else "voice_unavailable"
        ) from None
    finally:
        companion.lock.release()
