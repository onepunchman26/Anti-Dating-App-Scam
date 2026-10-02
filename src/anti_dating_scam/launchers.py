"""Installed command-line entry points; application behavior remains in the engine."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import threading
import time
import webbrowser


def _configure_console() -> None:
    # Frozen Windows programs can use an ANSI code page when output is piped.
    # Bilingual help and startup messages must not prevent the app from opening.
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def _desktop_run(*, smoke_test: bool = False) -> int:
    try:
        from anti_dating_scam_desktop import app
    except ModuleNotFoundError as exc:
        if exc.name not in {"PySide6", "anti_dating_scam_desktop"}:
            raise
        print(
            'Install desktop dependencies: pip install "anti-dating-scam[desktop]"\n'
            '请安装桌面依赖：pip install "anti-dating-scam[desktop]"',
            file=sys.stderr,
        )
        return 1
    if not smoke_test:
        return app.run()

    import vosk
    from PySide6.QtCore import QTimer
    from PySide6.QtMultimedia import QMediaDevices

    # Importing the installed recognizer loads its native DLL dependencies.
    # No language model, microphone or network request is opened by this check.
    vosk.SetLogLevel(-1)

    original_application = app.QApplication

    class SmokeApplication(original_application):
        def __init__(self, argv):
            super().__init__(argv)
            QMediaDevices.audioInputs()  # Read-only platform audio enumeration.
            QTimer.singleShot(750, self.quit)

    app.QApplication = SmokeApplication
    try:
        return app.run()
    finally:
        app.QApplication = original_application


def desktop_main(argv: list[str] | None = None) -> int:
    _configure_console()
    parser = argparse.ArgumentParser(description="AI-SlowMatch desktop / 桌面应用")
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="start with temporary data and exit automatically / 临时数据启动检查后自动退出",
    )
    parser.add_argument("--invitation", help="Open an invitation for review / 打开邀请供审阅")
    args = parser.parse_args(argv)
    if args.invitation:
        # Carry opaque text to the review field only. Never connect, claim or consent here.
        if len(args.invitation) > 2048:
            parser.error("Invalid invitation / 邀请过长")
        os.environ["ADS_PENDING_INVITATION"] = args.invitation
    if not args.smoke_test:
        return _desktop_run()
    # Set isolation before importing any module that resolves the user's vault.
    with tempfile.TemporaryDirectory(prefix="slowmatch-desktop-smoke-") as home:
        environment = {
            "HOME": home, "USERPROFILE": home,
            "APPDATA": home, "LOCALAPPDATA": home,
            "ADS_NO_AUTOCONNECT": "1", "QT_QPA_PLATFORM": "offscreen",
        }
        previous = {key: os.environ.get(key) for key in environment}
        os.environ.update(environment)
        try:
            from jsonschema import Draft202012Validator

            from anti_dating_scam.reports.schema_validator import load_schema
            from anti_dating_scam.resources import web_directory

            for name in ("personal_profile", "risk_report", "trust_ladder"):
                Draft202012Validator.check_schema(load_schema(f"{name}.schema.json"))
            if not (web_directory() / "index.html").is_file():
                raise FileNotFoundError("Packaged browser interface is missing")
            return _desktop_run(smoke_test=True)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def web_main(argv: list[str] | None = None) -> int:
    _configure_console()
    parser = argparse.ArgumentParser(description="AI-SlowMatch local browser app / 本地网页应用")
    parser.add_argument("--port", type=int, default=8471)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535 / 端口必须在 1 到 65535 之间")

    import uvicorn

    from anti_dating_scam.api.rendezvous_app import create_client_app

    url = f"http://127.0.0.1:{args.port}/"
    server = uvicorn.Server(uvicorn.Config(
        create_client_app(), host="127.0.0.1", port=args.port, access_log=False,
    ))
    print(f"AI-SlowMatch: {url}")
    print("Local app; remote AI and matching require your explicit choices.")
    print("本地应用；远程 AI 与匹配服务需要你明确选择。")
    print("Keep this window open. Ctrl+C to quit. / 请保留此窗口，按 Ctrl+C 退出。")

    if not args.no_browser:
        def open_when_ready():
            for _ in range(100):
                if server.started:
                    webbrowser.open(url)
                    return
                if server.should_exit:
                    return
                time.sleep(0.1)

        threading.Thread(target=open_when_ready, daemon=True).start()
    server.run()
    return 0
