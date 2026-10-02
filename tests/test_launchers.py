import os
import subprocess
import sys
from pathlib import Path

import pytest
import uvicorn

from anti_dating_scam import launchers


def test_bilingual_launcher_help_survives_ansi_output_encoding():
    result = subprocess.run(
        [sys.executable, "run_local_app.py", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
        capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "本地网页应用" in result.stdout.decode("utf-8")


def test_browser_launcher_binds_loopback_without_access_logging(monkeypatch):
    captured = {}

    class FakeServer:
        def __init__(self, config):
            captured["config"] = config

        def run(self):
            captured["ran"] = True

    monkeypatch.setattr(uvicorn, "Server", FakeServer)
    assert launchers.web_main(["--no-browser", "--port", "8472"]) == 0
    assert captured["ran"]
    assert captured["config"].host == "127.0.0.1"
    assert captured["config"].port == 8472
    assert captured["config"].access_log is False


@pytest.mark.parametrize("port", ["0", "-1", "65536"])
def test_browser_launcher_rejects_invalid_ports(port):
    with pytest.raises(SystemExit) as caught:
        launchers.web_main(["--no-browser", "--port", port])
    assert caught.value.code == 2


def test_desktop_smoke_isolates_home_and_disables_auto_connection(monkeypatch):
    prior_home = os.environ.get("USERPROFILE")
    prior_auto = os.environ.get("ADS_NO_AUTOCONNECT")
    captured = {}

    def fake_run(*, smoke_test):
        assert smoke_test
        assert os.environ["ADS_NO_AUTOCONNECT"] == "1"
        assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
        home = Path(os.environ["USERPROFILE"])
        assert home != Path(prior_home)
        assert home.is_dir()
        assert os.environ["HOME"] == str(home)
        captured["home"] = home
        return 0

    monkeypatch.setattr(launchers, "_desktop_run", fake_run)
    assert launchers.desktop_main(["--smoke-test"]) == 0
    assert os.environ.get("USERPROFILE") == prior_home
    assert os.environ.get("ADS_NO_AUTOCONNECT") == prior_auto
    assert not captured["home"].exists()
