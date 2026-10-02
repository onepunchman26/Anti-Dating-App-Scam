"""Run destructive Qt lifecycle cases in a subprocess, using only synthetic work."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROGRAM = r'''
import sys
import time
sys.path.insert(0, "apps/desktop_pyqt")
from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid
from anti_dating_scam_desktop.main_window import MainWindow
from anti_dating_scam_desktop.workers import has_pending_workers, run_async

action = sys.argv[1]
app = QApplication([])
app.setQuitOnLastWindowClosed(False)
window = MainWindow()
window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
window.show()
owner = window.navigator._screens["self_portrait"]
observed = {"ok": [], "errors": [], "ticks": 0, "callbacks_on_ui": [], "alive_during": False}

def result(value):
    observed["ok"].append(value)
    observed["callbacks_on_ui"].append(QThread.currentThread() == app.thread() and isValid(owner))

def error(message):
    observed["errors"].append(message)
    observed["callbacks_on_ui"].append(QThread.currentThread() == app.thread() and isValid(owner))

def first():
    time.sleep(0.20)
    if action == "error_close":
        raise ValueError("synthetic failure")
    return "first"

def second():
    time.sleep(0.38)
    return "second"

# Two workers on one owner also cover the overwritten _active_worker reference.
run_async(owner, first, result, error)
run_async(owner, second, result, error)
pulse = QTimer()
pulse.setInterval(15)
def tick():
    observed["ticks"] += 1
pulse.timeout.connect(tick)
pulse.start()

def request_change():
    if action in ("language", "language_then_close"):
        window._toggle_language()
    if action != "language":
        window.close()
QTimer.singleShot(30, request_change)

def inspect_pending():
    observed["alive_during"] = isValid(owner) and isValid(window) and has_pending_workers(window)
QTimer.singleShot(100, inspect_pending)
def inspect_finished():
    observed["owner_final_valid"] = isValid(owner)
    observed["window_final_valid"] = isValid(window)
    if isValid(window):
        observed["pending_final"] = has_pending_workers(window)
        observed["pending_language_final"] = window._pending_language_change
    app.quit()
QTimer.singleShot(850, inspect_finished)
app.exec()

assert observed["alive_during"], observed
assert observed["ticks"] >= 20, observed
assert observed["callbacks_on_ui"] == [True, True], observed
assert "second" in observed["ok"], observed
if action == "error_close":
    assert observed["errors"] == ["synthetic failure"], observed
else:
    assert observed["ok"] == ["first", "second"], observed
assert not observed["owner_final_valid"], observed
if action == "language":
    assert observed["window_final_valid"] and not observed["pending_final"], observed
    assert not observed["pending_language_final"], observed
else:
    assert not observed["window_final_valid"], "Deferred close did not finish"
'''


@pytest.mark.parametrize("action", ["language", "close", "error_close", "language_then_close"])
def test_active_workers_survive_language_rebuild_and_window_close(tmp_path, action):
    environment = {
        **os.environ,
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
        "ADS_NO_AUTOCONNECT": "1",
        "QT_QPA_PLATFORM": "offscreen",
    }
    result = subprocess.run(
        [sys.executable, "-c", PROGRAM, action],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    assert result.returncode == 0, f"exit={result.returncode}\n{result.stderr}"
