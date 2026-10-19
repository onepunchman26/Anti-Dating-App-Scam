"""Explicitly paired loopback bridge. Never mounted on the hosted Site."""

from __future__ import annotations

import html
import json
import secrets
import threading
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from anti_dating_scam.ai.privacy import BackendError
from anti_dating_scam.services.web_companion import CompanionError, WebCompanion
from anti_dating_scam.services.work_profile import WorkProfileError

SITE_ORIGIN = "https://slowmatch-private-pilot.fizzydeer7.chatgpt.site"
PORT = 8911


def create_companion_app(companion: WebCompanion, *, pairing_token=None, site_origin=SITE_ORIGIN):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    token = pairing_token or secrets.token_urlsafe(32)
    expires = time.monotonic() + 8 * 3600
    login_thread = None
    login_error = ""
    local_origin = f"http://127.0.0.1:{PORT}"

    @app.middleware("http")
    async def boundary(request, call_next):
        host = request.headers.get("host")
        origins = request.headers.getlist("origin")
        origin = origins[0] if len(origins) == 1 else ""
        allowed = origin in {site_origin, local_origin}
        if host != f"127.0.0.1:{PORT}" or len(origins) > 1:
            return JSONResponse({"error": "origin_denied"}, status_code=403)
        if request.method == "OPTIONS":
            response = JSONResponse({"ok": True}, status_code=200 if allowed else 403)
        elif request.url.path == "/" and request.method == "GET":
            top_level_click = (
                request.headers.get("sec-fetch-mode") == "navigate"
                and request.headers.get("sec-fetch-dest") == "document"
                and request.headers.get("sec-fetch-user") == "?1"
            )
            if origin not in {"", local_origin} or (
                request.headers.get("sec-fetch-site")
                in {
                    "cross-site",
                    "same-site",
                }
                and not top_level_click
            ):
                return JSONResponse({"error": "local_open_required"}, status_code=403)
            response = await call_next(request)
        else:
            if (
                not allowed
                or time.monotonic() >= expires
                or not secrets.compare_digest(
                    request.headers.get("authorization", ""), "Bearer " + token
                )
            ):
                return JSONResponse({"error": "pairing_required"}, status_code=403)
            response = await call_next(request)
        if allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'"
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    def pair():
        # Only this local page shows the temporary capability. Never log it or
        # put it in a URL, installer manifest, remote request or persistent file.
        return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>SlowMatch · Local assistant</title>
<style>body{{font:18px system-ui;background:#faf8f6;color:#29242a;max-width:720px;
margin:8vh auto;padding:24px}}code{{display:block;background:white;padding:20px;
overflow-wrap:anywhere}}a{{color:#6d3b5f}}</style>
<h1>Your local assistant is running</h1><p>Open SlowMatch, choose Start with yourself,
and paste this temporary pairing code. It allows this Site to access the local assistant.
It expires after 8 hours or when you close the assistant. Keep it private.</p>
<code>{html.escape(token)}</code><p>
<a href="{site_origin}/#start" target="_blank" rel="noreferrer">Open SlowMatch</a></p>
<hr><section lang="zh-CN"><h1>本机助手已启动</h1>
<p>打开慢慢相识，选择“开始了解自己”，粘贴上面的临时配对码。
它允许本站访问本机助手，请勿分享；八小时后或关闭助手后失效。</p>
<p>首次配对可能需要浏览器批准本机网络访问。
完整记录保存在本机，单独批准的摘要才会发布。</p></section></html>"""

    @app.post("/v1")
    async def operation(request: Request):
        nonlocal login_thread, login_error
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return JSONResponse({"error": "json_required"}, status_code=415)
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 64000:
                return JSONResponse({"error": "input_limit"}, status_code=413)
        try:
            body = json.loads(raw)
            if (
                not isinstance(body, dict)
                or set(body) != {"operation", "arguments"}
                or not isinstance(body["arguments"], dict)
            ):
                raise CompanionError("invalid_arguments")
            name, args = body["operation"], body["arguments"]
            if name == "login" and set(args) == {"confirmed"} and args["confirmed"] is True:
                if companion.lock.locked():
                    raise CompanionError("request_in_progress")
                if login_thread and login_thread.is_alive():
                    return {"ok": True, "result": {"login_pending": True}}
                # Account changes require reconnecting the vault and refreshing models.
                companion.cancel.set()
                companion.vault = None
                companion.models = []
                companion.inference_passed = False
                login_error = ""

                def connect():
                    nonlocal login_error
                    try:
                        companion.connection.connect()
                    except Exception:
                        login_error = "login_not_completed"

                login_thread = threading.Thread(target=connect, daemon=True)
                login_thread.start()
                result = {"login_pending": True}
            else:
                if login_thread and login_thread.is_alive() and name != "status":
                    raise CompanionError("login_pending")
                result = await run_in_threadpool(companion.dispatch, name, args)
                if name == "status":
                    result["login_error"] = login_error
            return {"ok": True, "result": result}
        except BackendError as error:
            return JSONResponse(
                {
                    "error": "ai_" + error.category,
                    "http_status": getattr(error, "http_status", None),
                },
                status_code=502,
            )
        except (CompanionError, WorkProfileError) as error:
            return JSONResponse({"error": str(error)}, status_code=409)
        except Exception:
            # Never echo request bodies, paths, raw provider output or secrets.
            return JSONResponse({"error": "invalid_or_unavailable"}, status_code=400)

    return app


def main(argv=None):
    import argparse
    import os
    import webbrowser

    import uvicorn

    parser = argparse.ArgumentParser(description="SlowMatch local web assistant / 本机网页助手")
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    root = args.state_root or Path(os.environ["LOCALAPPDATA"]) / "AI-SlowMatch" / "web-companion"
    companion = WebCompanion(root)
    app = create_companion_app(companion)
    if not args.no_browser:
        threading.Timer(1, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/")).start()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        access_log=False,
        log_level="warning",
        loop="asyncio",
        http="h11",
        ws="none",
    )


if __name__ == "__main__":
    main()
