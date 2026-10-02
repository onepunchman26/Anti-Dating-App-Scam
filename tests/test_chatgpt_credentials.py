"""Synthetic credential storage tests; no real account or browser state is read."""

import os
import secrets
import stat
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from anti_dating_scam.ai.chatgpt_credentials import (
    ChatGPTCredential,
    ChatGPTCredentialState,
    ChatGPTCredentialStore,
    WindowsDPAPIProtector,
    default_chatgpt_store_path,
)
from anti_dating_scam.ai.privacy import BackendError


class SyntheticProtector:
    """Reversible test encoding, deliberately not production encryption."""

    def protect(self, plaintext: bytes) -> bytes:
        return b"SYNTHETIC:" + bytes(value ^ 0xA5 for value in plaintext)

    def unprotect(self, ciphertext: bytes) -> bytes:
        if not ciphertext.startswith(b"SYNTHETIC:"):
            raise BackendError("Synthetic protected bytes are invalid.")
        return bytes(value ^ 0xA5 for value in ciphertext[len(b"SYNTHETIC:") :])


class FailingProtector(SyntheticProtector):
    def protect(self, plaintext: bytes) -> bytes:
        raise BackendError("Synthetic protection is unavailable.")


@pytest.mark.skipif(os.name != "nt", reason="Windows-only protected storage")
def test_native_windows_protection_round_trip_and_tamper_rejection():
    # Only newly generated synthetic bytes are sealed; no saved account is read.
    original = b"synthetic-native-round-trip-" + secrets.token_bytes(32)
    protector = WindowsDPAPIProtector()
    protected = protector.protect(original)
    assert original not in protected
    assert protector.unprotect(protected) == original
    corrupted = protected[:-1] + bytes([protected[-1] ^ 0x01])
    with pytest.raises(BackendError):
        protector.unprotect(corrupted)


def _state(token: str) -> ChatGPTCredentialState:
    account = ChatGPTCredential(
        client_id="oaiapp_synthetic_account",
        subject=SecretStr("synthetic-subject"),
        access_token=SecretStr(token),
        refresh_token=SecretStr("synthetic-refresh-" + token),
        id_token=SecretStr("synthetic-id-" + token),
        scopes=("resource.invoke", "chatgpt.tokens.use.direct"),
        expires_at=4_000_000_000,
    )
    return ChatGPTCredentialState(
        host_id=f"urn:uuid:{uuid.uuid4()}",
        registrations=(account,),
        active_client_id=account.client_id,
    )


def test_default_store_uses_isolated_home_not_localappdata(tmp_path, monkeypatch):
    alternate = tmp_path / "synthetic-localappdata"
    alternate.mkdir()
    monkeypatch.setenv("LOCALAPPDATA", str(alternate))
    # conftest sets the process's temporary HOME and USERPROFILE before import.
    home = Path.home()
    assert home != alternate
    path = default_chatgpt_store_path()
    assert path == home / ".ai_slowmatch" / "chatgpt" / "credentials.bin"
    store = ChatGPTCredentialStore(protector=SyntheticProtector())
    assert store.path == path
    assert store.load() is None
    assert not path.exists() and list(alternate.iterdir()) == []


def test_atomic_replace_read_and_explicit_clear_have_no_plaintext(tmp_path):
    path = tmp_path / "app" / "credentials.bin"
    store = ChatGPTCredentialStore(path, SyntheticProtector())
    first = "synthetic-access-" + secrets.token_urlsafe(24)
    second = "synthetic-access-" + secrets.token_urlsafe(24)
    original = _state(first)
    store.save(original)
    previous_bytes = path.read_bytes()
    assert previous_bytes.startswith(b"SYNTHETIC:")
    assert all(
        secret.encode() not in previous_bytes
        for secret in (first, "synthetic-refresh-" + first, "synthetic-id-" + first)
    )
    assert first not in repr(original) and first not in repr(store.load())
    assert store.load().registrations[0].access_token.get_secret_value() == first

    replacement = _state(second)
    store.save(replacement)
    assert path.read_bytes() != previous_bytes
    assert first.encode() not in path.read_bytes()
    assert store.load().registrations[0].access_token.get_secret_value() == second
    assert not list(path.parent.glob("chatgpt-*.tmp"))

    cleared = replacement.model_copy(
        update={"registrations": (), "active_client_id": None}
    )
    store.save(cleared)
    assert store.load().registrations == ()
    assert store.load().active_client_id is None
    assert second.encode() not in path.read_bytes()


def test_missing_default_protection_fails_closed_without_plaintext(tmp_path, monkeypatch):
    def unavailable(self, plaintext):
        raise BackendError("Windows protection is unavailable.")

    monkeypatch.setattr(WindowsDPAPIProtector, "protect", unavailable)
    path = tmp_path / "app" / "credentials.bin"
    store = ChatGPTCredentialStore(path)
    token = "synthetic-access-" + secrets.token_urlsafe(24)
    with pytest.raises(BackendError) as error:
        store.save(_state(token))
    assert token not in str(error.value)
    assert not path.exists()
    assert not list(path.parent.glob("chatgpt-*.tmp"))


def test_failed_protection_preserves_previous_ciphertext(tmp_path):
    path = tmp_path / "app" / "credentials.bin"
    working = ChatGPTCredentialStore(path, SyntheticProtector())
    first = "synthetic-access-" + secrets.token_urlsafe(24)
    working.save(_state(first))
    previous_bytes = path.read_bytes()
    failing = ChatGPTCredentialStore(path, FailingProtector())
    second = "synthetic-access-" + secrets.token_urlsafe(24)
    with pytest.raises(BackendError) as error:
        failing.save(_state(second))
    assert first not in str(error.value) and second not in str(error.value)
    assert path.read_bytes() == previous_bytes
    assert working.load().registrations[0].access_token.get_secret_value() == first
    assert not list(path.parent.glob("chatgpt-*.tmp"))


def test_corrupt_protected_file_has_safe_error(tmp_path):
    path = tmp_path / "app" / "credentials.bin"
    store = ChatGPTCredentialStore(path, SyntheticProtector())
    token = "synthetic-access-" + secrets.token_urlsafe(24)
    store.save(_state(token))
    path.write_bytes(b"synthetic-corrupt-ciphertext")
    with pytest.raises(BackendError) as error:
        store.load()
    assert token not in str(error.value)


@pytest.mark.parametrize("kind", ["file", "parent"])
def test_symlink_file_or_parent_is_rejected_without_touching_target(tmp_path, kind):
    outside = tmp_path / "synthetic-outside"
    outside.mkdir()
    marker = outside / "untouched.txt"
    marker.write_text("synthetic marker", encoding="utf-8")
    if kind == "parent":
        link = tmp_path / "linked-app"
        target = outside / "credentials.bin"
        path = link / "credentials.bin"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("This Windows session cannot create directory symlinks.")
    else:
        directory = tmp_path / "app"
        directory.mkdir()
        target = outside / "credentials.bin"
        target.write_bytes(b"synthetic original")
        path = directory / "credentials.bin"
        try:
            path.symlink_to(target)
        except OSError:
            pytest.skip("This Windows session cannot create file symlinks.")
    store = ChatGPTCredentialStore(path, SyntheticProtector())
    with pytest.raises(BackendError):
        store.save(_state("synthetic-access-never-written"))
    assert marker.read_text(encoding="utf-8") == "synthetic marker"
    if kind == "file":
        assert target.read_bytes() == b"synthetic original"
    else:
        assert not target.exists()


def test_hardlinked_credential_file_is_rejected_without_overwriting_target(tmp_path):
    outside = tmp_path / "synthetic-existing.bin"
    outside.write_bytes(b"synthetic original")
    directory = tmp_path / "app"
    directory.mkdir()
    path = directory / "credentials.bin"
    try:
        os.link(outside, path)
    except OSError:
        pytest.skip("This filesystem cannot create hard links.")
    store = ChatGPTCredentialStore(path, SyntheticProtector())
    with pytest.raises(BackendError):
        store.load()
    with pytest.raises(BackendError):
        store.save(_state("synthetic-access-never-written"))
    assert outside.read_bytes() == b"synthetic original"


def test_reparse_attribute_is_rejected_before_access(tmp_path, monkeypatch):
    parent = tmp_path / "app"
    parent.mkdir()
    path = parent / "credentials.bin"
    original_lstat = Path.lstat

    def reparse_lstat(self, *args, **kwargs):
        details = original_lstat(self, *args, **kwargs)
        if self == parent:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR,
                st_nlink=details.st_nlink,
                st_file_attributes=0x400,
            )
        return details

    monkeypatch.setattr(Path, "lstat", reparse_lstat)
    store = ChatGPTCredentialStore(path, SyntheticProtector())
    with pytest.raises(BackendError):
        store.load()
    assert not path.exists()
