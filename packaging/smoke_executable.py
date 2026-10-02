"""Check a Windows portable artifact from outside the repository, with temporary data."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from smoke_install import smoke_web


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--target", choices=["Desktop", "Web"], required=True)
    args = parser.parse_args()
    artifact = args.artifact.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="slowmatch-executable-smoke-") as temporary:
        root = Path(temporary)
        copied = root / artifact.name
        shutil.copy2(artifact, copied)
        home = root / "home"
        home.mkdir()
        environment = {
            **os.environ, "HOME": str(home), "USERPROFILE": str(home),
            "APPDATA": str(home), "LOCALAPPDATA": str(home),
            "ADS_NO_AUTOCONNECT": "1", "QT_QPA_PLATFORM": "offscreen",
            "PYTHONIOENCODING": "utf-8",
        }
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        if args.target == "Web":
            smoke_web(str(copied), cwd=root, environment=environment)
        else:
            process = subprocess.Popen(
                [str(copied), "--smoke-test"], cwd=root, env=environment,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                output, _ = process.communicate(timeout=60)
                if process.returncode:
                    raise RuntimeError(f"Desktop smoke failed ({process.returncode}):\n{output}")
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                    )
                else:
                    process.kill()
                process.communicate(timeout=10)
                raise RuntimeError("Desktop startup exceeded 60 seconds") from None
        # Windows can retain an executable mapping briefly after its process
        # tree exits. Retry this test-owned file before removing the temp home.
        for attempt in range(50):
            try:
                copied.unlink()
                break
            except PermissionError:
                if attempt == 49:
                    raise
                time.sleep(0.1)
        print(f"{args.target} executable startup passed outside the source checkout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
