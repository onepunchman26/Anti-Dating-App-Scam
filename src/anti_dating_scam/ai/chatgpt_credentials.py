"""App-owned, Windows-user-protected ChatGPT credentials, never a vault file."""

from __future__ import annotations

import ctypes
import json
import os
import stat
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from anti_dating_scam.ai.privacy import BackendError

ISSUER = "https://auth.openai.com"
MAX_CREDENTIAL_BYTES = 1_048_576


class ChatGPTCredential(BaseModel):
    """Separate registration and credentials for each verified client/subject."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    client_id: str = Field(pattern=r"^oaiapp_[A-Za-z0-9_-]{1,240}$")
    subject: SecretStr
    issuer: str = ISSUER
    access_token: SecretStr
    refresh_token: SecretStr | None = None
    id_token: SecretStr | None = None
    scopes: tuple[str, ...]
    expires_at: float = Field(gt=0)
    earliest_refresh_at: float = Field(default=0, ge=0)


class ChatGPTCredentialState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    host_id: str = Field(pattern=r"^urn:uuid:[0-9a-f-]{36}$")
    registrations: tuple[ChatGPTCredential, ...] = Field(default=(), max_length=20)
    # Issued ID retained after a failed exchange, before any identity is trusted.
    pending_client_id: str | None = Field(default=None, pattern=r"^oaiapp_[A-Za-z0-9_-]{1,240}$")
    active_client_id: str | None = Field(default=None, pattern=r"^oaiapp_[A-Za-z0-9_-]{1,240}$")


class CredentialProtector(Protocol):
    def protect(self, plaintext: bytes) -> bytes: ...

    def unprotect(self, ciphertext: bytes) -> bytes: ...


class WindowsDPAPIProtector:
    """DPAPI current-user protection; no plaintext or machine-wide fallback."""

    class _Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_uint32), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    @classmethod
    def _crypt(cls, value: bytes, *, decrypt: bool) -> bytes:
        if os.name != "nt":
            raise BackendError("Protected ChatGPT credential storage requires Windows.")
        if not value or len(value) > MAX_CREDENTIAL_BYTES:
            raise BackendError("Invalid protected ChatGPT credential file.")
        buffer = ctypes.create_string_buffer(value)
        source = cls._Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
        entropy_buffer = ctypes.create_string_buffer(b"AI-SlowMatch ChatGPT credentials v1")
        entropy = cls._Blob(
            len(entropy_buffer) - 1,
            ctypes.cast(entropy_buffer, ctypes.POINTER(ctypes.c_ubyte)),
        )
        destination = cls._Blob()
        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
        function.argtypes = [
            ctypes.POINTER(cls._Blob),
            ctypes.c_void_p,
            ctypes.POINTER(cls._Blob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(cls._Blob),
        ]
        function.restype = ctypes.c_int
        # CRYPTPROTECT_UI_FORBIDDEN. No CRYPTPROTECT_LOCAL_MACHINE flag.
        if not function(
            ctypes.byref(source),
            None,
            ctypes.byref(entropy),
            None,
            None,
            1,
            ctypes.byref(destination),
        ):
            raise BackendError("Windows could not protect or unlock the ChatGPT connection.")
        try:
            return ctypes.string_at(destination.data, destination.size)
        finally:
            kernel32.LocalFree(ctypes.cast(destination.data, ctypes.c_void_p))

    def protect(self, plaintext: bytes) -> bytes:
        return self._crypt(plaintext, decrypt=False)

    def unprotect(self, ciphertext: bytes) -> bytes:
        return self._crypt(ciphertext, decrypt=True)


def default_chatgpt_store_path() -> Path:
    # Path.home also follows the test suite's isolated HOME/USERPROFILE.
    return Path.home() / ".ai_slowmatch" / "chatgpt" / "credentials.bin"


class ChatGPTCredentialStore:
    """Atomic encrypted writes and process-serialized token rotation.

    Construction is inert. Reading is limited to this app-owned file; other
    ChatGPT apps, browser cookies, CLI credentials and vault files are untouched.
    """

    def __init__(
        self, path: Path | None = None, protector: CredentialProtector | None = None
    ) -> None:
        self.path = (Path(path) if path is not None else default_chatgpt_store_path()).absolute()
        if ".." in self.path.parts:
            raise BackendError("ChatGPT credentials need an unambiguous app-owned path.")
        self._protector = protector or WindowsDPAPIProtector()
        self._thread_lock = threading.RLock()
        self._depth = threading.local()

    @staticmethod
    def _safe_path(path: Path) -> None:
        """Refuse redirected parent folders, reparse files and linked secrets."""
        for candidate in (path, *path.parents):
            try:
                details = candidate.lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise BackendError(
                    "The ChatGPT credential location could not be checked."
                ) from None
            if stat.S_ISLNK(details.st_mode) or (getattr(details, "st_file_attributes", 0) & 0x400):
                raise BackendError("ChatGPT credentials cannot use linked or redirected paths.")
            if stat.S_ISREG(details.st_mode) and details.st_nlink != 1:
                raise BackendError("ChatGPT credentials cannot use a file with multiple links.")
            if candidate != path and not stat.S_ISDIR(details.st_mode):
                raise BackendError("The ChatGPT credential parent must be an ordinary folder.")

    @contextmanager
    def exclusive(self) -> Iterator[None]:
        with self._thread_lock:
            if getattr(self._depth, "value", 0):
                self._depth.value += 1
                try:
                    yield
                finally:
                    self._depth.value -= 1
                return
            self._safe_path(self.path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._safe_path(self.path)
            self._safe_path(self.path.with_suffix(".lock"))
            with self.path.with_suffix(".lock").open("a+b") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                deadline = time.monotonic() + 10
                while True:
                    try:
                        handle.seek(0)
                        if os.name == "nt":
                            import msvcrt

                            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        else:
                            import fcntl

                            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise BackendError(
                                "Another ChatGPT connection update is in progress."
                            ) from None
                        time.sleep(0.05)
                self._depth.value = 1
                try:
                    yield
                finally:
                    self._depth.value = 0
                    handle.seek(0)
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def load(self, *, create: bool = False) -> ChatGPTCredentialState | None:
        # A status check on a never-connected app does not create files.
        self._safe_path(self.path)
        if not create and not self.path.exists():
            return None
        with self.exclusive():
            if not self.path.exists():
                state = ChatGPTCredentialState(host_id=f"urn:uuid:{uuid.uuid4()}")
                self.save(state)
                return state
            try:
                self._safe_path(self.path)
                if self.path.stat().st_size > MAX_CREDENTIAL_BYTES:
                    raise ValueError
                plaintext = self._protector.unprotect(self.path.read_bytes())
                return ChatGPTCredentialState.model_validate_json(plaintext)
            except BackendError:
                raise
            except (OSError, ValueError, ValidationError):
                raise BackendError("The protected ChatGPT connection could not be read.") from None

    def save(self, state: ChatGPTCredentialState) -> None:
        with self.exclusive():
            try:
                self._safe_path(self.path)
                checked = ChatGPTCredentialState.model_validate(state.model_dump())
                data = checked.model_dump(mode="json")
                for index, credential in enumerate(checked.registrations):
                    for field in ("subject", "access_token", "refresh_token", "id_token"):
                        secret = getattr(credential, field)
                        data["registrations"][index][field] = (
                            secret.get_secret_value() if secret is not None else None
                        )
                plaintext = json.dumps(data, separators=(",", ":"), allow_nan=False).encode()
                if len(plaintext) > MAX_CREDENTIAL_BYTES:
                    raise ValueError
                ciphertext = self._protector.protect(plaintext)
                if not ciphertext or len(ciphertext) > MAX_CREDENTIAL_BYTES:
                    raise ValueError
                descriptor, temporary = tempfile.mkstemp(
                    prefix="chatgpt-", suffix=".tmp", dir=self.path.parent
                )
                try:
                    with os.fdopen(descriptor, "wb") as handle:
                        handle.write(ciphertext)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, self.path)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
            except BackendError:
                raise
            except (OSError, TypeError, ValueError, ValidationError):
                raise BackendError("The ChatGPT connection could not be saved securely.") from None
