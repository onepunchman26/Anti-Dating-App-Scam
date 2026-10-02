"""Explicit local node lifecycle and protected per-vault device sessions."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from uuid import uuid4

from anti_dating_scam.ai.chatgpt_credentials import WindowsDPAPIProtector
from anti_dating_scam.matchmaking.peer_client import node_origin
from anti_dating_scam.services.report_review import ReportReviewService


class PeerSessionStore:
    def __init__(self, vault, *, protector=None):
        self.vault = Path(vault)
        self.protector = protector or WindowsDPAPIProtector()

    def _path(self, origin):
        return (
            self.vault
            / ".peer-session"
            / (hashlib.sha256(node_origin(origin).encode()).hexdigest() + ".dpapi")
        )

    def load(self, origin):
        store = ReportReviewService(self.vault)
        try:
            raw = store._read(self._path(origin), 8192)
        except FileNotFoundError:
            return None
        result = json.loads(self.protector.unprotect(raw))
        if result["origin"] != node_origin(origin):
            raise ValueError("session_scope")
        return result

    def save(self, origin, identity):
        store = ReportReviewService(self.vault)
        path = self._path(origin)
        store._mkdir(path.parent)
        data = {"origin": node_origin(origin), **identity}
        raw = self.protector.protect(json.dumps(data).encode())
        with store._writer(path.parent):
            if path.exists():
                store._check(path, directory=False)
            temporary = path.parent / (uuid4().hex + ".tmp")
            try:
                store._write_new(temporary, raw)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)

    def clear(self, origin):
        path = self._path(origin)
        store = ReportReviewService(self.vault)
        if path.exists():
            store._check(path, directory=False)
            path.unlink()


class LocalPeerNode:
    def __init__(self, directory=None, port=8766):
        self.directory = (
            Path(directory)
            if directory
            else Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
            / "AI-SlowMatch/matching-node"
        )
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        if self.server and self.server.started and self.thread.is_alive():
            return self.origin
        import socket

        import uvicorn

        from anti_dating_scam.api.rendezvous_app import create_rendezvous_app

        # Reserve the actual loopback socket before starting; never bind a LAN interface.
        listener = socket.socket()
        listener.bind(("127.0.0.1", self.port))
        listener.listen(64)
        self.port = listener.getsockname()[1]
        try:
            application = create_rendezvous_app(peer_directory=self.directory, public_cors=False)
            self.server = uvicorn.Server(
                uvicorn.Config(
                    application,
                    host="127.0.0.1",
                    port=self.port,
                    access_log=False,
                    log_config=None,
                    log_level="error",
                    loop="asyncio",
                )
            )
            self.thread = threading.Thread(
                target=self.server.run, kwargs={"sockets": [listener]}, daemon=True
            )
            self.thread.start()
            for _ in range(100):
                if self.server.started:
                    return self.origin
                if not self.thread.is_alive():
                    break
                time.sleep(0.05)
            raise ValueError("node_start_failed")
        except Exception:
            listener.close()
            raise

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        if self.server:
            self.server.should_exit = True


def register_invitation_handler(executable):
    """Called only by the user's explicit Install app-link handler action."""
    import winreg

    executable = Path(executable).resolve()
    if executable.suffix.lower() != ".exe" or not executable.is_file():
        raise ValueError("packaged_app_required")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\slowmatch") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:AI-SlowMatch invitation")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, r"Software\Classes\slowmatch\shell\open\command"
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{executable}" --invitation "%1"')
