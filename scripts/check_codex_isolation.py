"""Opt-in installed-runtime check against a loopback fake provider; no real AI/auth."""

from __future__ import annotations

import json
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from anti_dating_scam.ai.codex_connection import CodexRPC, isolated_config


def main():
    requests = []
    canary = "SYNTHETIC_PRIVATE_CANARY_NOT_APPROVED_FOR_DISCLOSURE"
    with tempfile.TemporaryDirectory(prefix="slowmatch-runtime-isolation-") as folder:
        root = Path(folder)
        home, work = root / "home", root / "work"
        home.mkdir()
        work.mkdir()
        private = root / "unapproved.txt"
        private.write_text(canary, encoding="utf-8")

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                requests.append(request)
                first = len(requests) == 1
                item = (
                    {
                        "id": "synthetic_tool",
                        "type": "function_call",
                        "call_id": "synthetic_call",
                        "name": "exec_command",
                        "arguments": json.dumps(
                            {
                                "cmd": f"Get-Content -LiteralPath '{private}'",
                            }
                        ),
                        "status": "completed",
                    }
                    if first
                    else {
                        "id": "synthetic_message",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": "Synthetic reply"}],
                    }
                )
                response = {
                    "id": f"synthetic_response_{len(requests)}",
                    "model": "gpt-6-luna",
                    "status": "completed",
                    "output": [item],
                    "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                }
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                events = [
                    {
                        "type": "response.created",
                        "response": {**response, "status": "in_progress", "output": []},
                    },
                    {"type": "response.output_item.added", "output_index": 0, "item": item},
                    {"type": "response.output_item.done", "output_index": 0, "item": item},
                    {"type": "response.completed", "response": response},
                ]
                for event in events:
                    self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
                self.wfile.flush()

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        config = {
            **isolated_config(),
            "cli_auth_credentials_store": "ephemeral",
            "model_provider": "synthetic",
            "model_providers.synthetic.name": "Synthetic",
            "model_providers.synthetic.base_url": f"http://127.0.0.1:{server.server_port}/v1",
            "model_providers.synthetic.wire_api": "responses",
            "model_providers.synthetic.requires_openai_auth": False,
            "model_providers.synthetic.request_max_retries": 0,
            "model_providers.synthetic.stream_max_retries": 0,
        }
        rpc = CodexRPC(home, work, config=config)
        try:
            thread = rpc.call(
                "thread/start",
                {
                    "model": "gpt-6-luna",
                    "cwd": str(work),
                    "ephemeral": True,
                    "baseInstructions": "Answer only the supplied synthetic message; no tools.",
                    "developerInstructions": "",
                    "sandbox": "read-only",
                    "approvalPolicy": "never",
                },
            )
            assert not thread.get("instructionSources")
            rpc.call(
                "turn/start",
                {
                    "threadId": thread["thread"]["id"],
                    "input": [
                        {"type": "text", "text": "Synthetic hello"},
                    ],
                },
            )
            deadline = time.monotonic() + 20
            while True:
                event = rpc.event(deadline)
                if event.get("method") == "item/completed":
                    assert event["params"]["item"]["type"] in {
                        "userMessage",
                        "agentMessage",
                        "reasoning",
                    }
                if event.get("method") == "turn/completed":
                    assert event["params"]["turn"]["status"] == "completed"
                    break
            assert len(requests) == 2, (
                "Injected unsupported tool should get one rejected-tool reply."
            )
            assert all(not request.get("tools") for request in requests)
            assert canary not in json.dumps(requests)
            tool_replies = [
                item for item in requests[1]["input"] if item.get("type") == "function_call_output"
            ]
            assert tool_replies and "unsupported call: exec_command" in json.dumps(tool_replies)
            assert not (home / "auth.json").exists()
            print(
                json.dumps(
                    {
                        "loopback_only": True,
                        "tool_catalog_empty": True,
                        "injected_shell_call_rejected": True,
                        "private_canary_not_disclosed": True,
                        "no_auth_file": True,
                        "requests": len(requests),
                    }
                )
            )
        finally:
            rpc.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
