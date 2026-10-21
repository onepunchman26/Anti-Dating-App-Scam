"""Start/reuse the bounded loopback helper; never read a vault or infer permissions."""

from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser

from anti_dating_scam.version import build_info


class LaunchError(ValueError):
    """Stable, non-sensitive launch status only."""


def launch(*, state_root=None, open_browser=True):
    try:
        return _launch(state_root=state_root, open_browser=open_browser)
    except LaunchError:
        raise
    except Exception as error:
        raise LaunchError("local_launch_" + type(error).__name__.lower()) from None


def _launch(*, state_root=None, open_browser=True):
    url = "http://127.0.0.1:8911"
    expected = build_info()["version"]
    def health():
        connection = http.client.HTTPConnection("127.0.0.1", 8911, timeout=2)
        try:
            # A fixed plain loopback request needs neither proxies nor TLS/CA setup.
            # Never follow redirects to another destination.
            connection.request("GET", "/health")
            response = connection.getresponse()
            return json.loads(response.read(2048)) if response.status == 200 else None
        except (OSError, ValueError, http.client.HTTPException):
            return None
        finally:
            connection.close()

    current = health()
    started = False
    if current is None:
        with socket.socket() as probe:
            probe.settimeout(0.5)
            if probe.connect_ex(("127.0.0.1", 8911)) == 0:
                raise LaunchError("local_port_in_use_close_old_assistant")
        command = (
            [sys.executable, "companion"]
            if getattr(sys, "frozen", False)
            else [sys.executable, "-m", "anti_dating_scam.api.web_companion"]
        )
        command += ["--no-browser"]
        if state_root is not None:
            command += ["--state-root", str(state_root)]
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        started = True
        for _ in range(30):
            if process.poll() is not None:
                raise LaunchError("local_assistant_start_failed")
            current = health()
            if current:
                break
            time.sleep(0.2)
    if not current or current.get("service") != "slowmatch-local":
        raise LaunchError("local_assistant_not_ready")
    if current.get("version") != expected or not current.get("ui_ready"):
        raise LaunchError("restart_updated_assistant_required")
    opened = bool(webbrowser.open(url + "/app")) if open_browser else False
    return {
        "ok": True,
        "version": expected,
        "assistant": "started" if started else "already_running",
        "url": url + "/app",
        "browser_opened": opened,
        "model_calls": 0,
        "private_storage": "awaiting_owner_selection",
        "inference": "not_checked",
    }
