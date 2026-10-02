"""Exercise the real launcher and Qt event loop with no personal data or AI calls."""

import os
import subprocess
import sys
from pathlib import Path


def test_desktop_launcher_starts_and_exits_cleanly(tmp_path):
    environment = {
        **os.environ,
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
        "ADS_NO_AUTOCONNECT": "1",
        "QT_QPA_PLATFORM": "offscreen",
    }
    program = """
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
import run_desktop
import sys
sys.path.insert(0, "apps/desktop_pyqt")
from anti_dating_scam_desktop import app
class SmokeApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        QTimer.singleShot(250, self.quit)
app.QApplication = SmokeApplication
raise SystemExit(run_desktop.main())
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
