"""Build and exercise a wheel outside the checkout in a clean virtual environment.

Runs no model, imports no personal data, and binds the browser server to loopback.
Package downloads may be needed; no commercial services or credentials are used.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import venv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROBE = r'''
import json
import sys
from importlib.metadata import distribution
from pathlib import Path
from fastapi.testclient import TestClient
import anti_dating_scam
import anti_dating_scam_desktop
from anti_dating_scam.api.rendezvous_app import create_client_app
from anti_dating_scam.reports.schema_validator import load_schema
from anti_dating_scam.resources import web_directory

for module in (anti_dating_scam, anti_dating_scam_desktop):
    assert Path(module.__file__).is_relative_to(Path(sys.prefix)), module.__file__
assets = web_directory()
assert assets.is_relative_to(Path(sys.prefix)), assets
assert (assets / 'index.html').is_file()
for name in ('personal_profile', 'risk_report', 'trust_ladder'):
    assert load_schema(name + '.schema.json')['type'] == 'object'
entries = {entry.name for entry in distribution('anti-dating-scam').entry_points}
assert {'slowmatch', 'slowmatch-web'} <= entries
with TestClient(create_client_app(), base_url='http://127.0.0.1') as client:
    response = client.get('/')
    assert response.status_code == 200, response.text
    assert 'text/html' in response.headers['content-type']
    denied = client.get('/', headers={'Origin': 'https://untrusted.example.test'})
    assert denied.status_code == 403, denied.text
print(json.dumps({'wheel_resources': 'ok', 'local_browser_boundary': 'ok'}))
'''


def run(command: list[str], *, cwd: Path, environment: dict[str, str], timeout=180) -> None:
    result = subprocess.run(
        command, cwd=cwd, env=environment, text=True,
        encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}):\n{result.stdout}")


def smoke_web(command: str, *, cwd: Path, environment: dict[str, str]) -> None:
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        port = reserve.getsockname()[1]
    process = subprocess.Popen(
        [command, "--no-browser", "--port", str(port)], cwd=cwd, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        errors="replace",
    )
    try:
        deadline = time.monotonic() + 30
        # Never use an inherited proxy for the loopback smoke request.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Browser launcher exited early:\n{process.communicate()[0]}")
            try:
                with opener.open(f"http://127.0.0.1:{port}/", timeout=1) as response:
                    assert response.status == 200
                    assert "text/html" in response.headers["Content-Type"]
                    return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        raise RuntimeError("Browser launcher did not become ready within 30 seconds")
    finally:
        if process.poll() is None:
            # Frozen Windows launchers have a bootloader child. End only this
            # test-owned process tree so no loopback server remains running.
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                )
            else:
                process.terminate()
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=10)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, help="test an existing wheel instead of building")
    args = parser.parse_args()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"
    # Keep package downloads reusable while application data remains isolated.
    # Changing HOME otherwise causes repeated large Qt downloads in each smoke run.
    if not environment.get("PIP_CACHE_DIR"):
        cache = subprocess.run(
            [sys.executable, "-m", "pip", "cache", "dir"], capture_output=True,
            text=True, env=environment, timeout=15,
        )
        if cache.returncode == 0:
            environment["PIP_CACHE_DIR"] = cache.stdout.strip()
    environment.setdefault("PIP_DEFAULT_TIMEOUT", "120")
    with tempfile.TemporaryDirectory(prefix="slowmatch-wheel-smoke-") as temporary:
        root = Path(temporary)
        home = root / "home"
        home.mkdir()
        environment.update({
            "HOME": str(home), "USERPROFILE": str(home), "ADS_NO_AUTOCONNECT": "1",
            "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8",
        })
        if args.wheel:
            wheel = args.wheel.resolve(strict=True)
        else:
            print("Building a wheel from the source distribution ...", flush=True)
            wheels = root / "wheels"
            run([sys.executable, "-m", "build", "--outdir", str(wheels)],
                cwd=REPO, environment=environment)
            wheel, = wheels.glob("*.whl")
        print("Installing wheel into a fresh environment ...", flush=True)
        target = root / "venv"
        venv.EnvBuilder(with_pip=True).create(target)
        scripts = target / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        suffix = ".exe" if os.name == "nt" else ""
        run([str(python), "-m", "pip", "install", "--progress-bar", "off",
             "--disable-pip-version-check", f"{wheel}[desktop]", "httpx"],
            cwd=root, environment=environment, timeout=300)
        run([str(python), "-I", "-c", PROBE], cwd=root, environment=environment)
        print("Wheel schema, desktop imports, browser HTML and origin boundary passed.", flush=True)
        run([str(scripts / f"slowmatch{suffix}"), "--smoke-test"],
            cwd=root, environment=environment, timeout=45)
        print("Installed desktop event loop passed.", flush=True)
        smoke_web(str(scripts / f"slowmatch-web{suffix}"), cwd=root, environment=environment)
        print("Installed browser launcher HTTP startup passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
