"""Opt-in real local portrait/interview/report chain; synthetic data only."""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path


def run_chain(model: str, timeout: float, output: Path) -> int:
    """Record each stage without retaining generated reports or exception contents."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "apps" / "desktop_pyqt"))
    started = time.monotonic()
    result = {
        "synthetic_only": True,
        "local_only": True,
        "model": model,
        "validation_scope": "structure, quote presence, and localization coverage",
        "semantic_review": "manual review still required",
        "status": "running",
        "stage": "initializing",
        "steps": [],
    }

    def record(stage: str | None = None) -> None:
        if stage is not None:
            result["stage"] = stage
        result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Replace an earlier success before any provider call or temporary-vault setup.
    record()
    previous_env = {
        key: os.environ.get(key) for key in ("HOME", "USERPROFILE", "ADS_NO_AUTOCONNECT")
    }
    try:
        with tempfile.TemporaryDirectory(prefix="slowmatch-desktop-synthetic-") as sandbox:
            os.environ.update(HOME=sandbox, USERPROFILE=sandbox, ADS_NO_AUTOCONNECT="1")
            from anti_dating_scam_desktop import ai_backend
            from anti_dating_scam_desktop.profile_store import ProfileStore

            from anti_dating_scam.ai.chat_backends import _default_http
            from anti_dating_scam.ai.privacy import BackendError

            def bounded_transport(url, payload, headers, request_timeout):
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise BackendError("Synthetic local smoke reached its time limit.")
                return _default_http(url, payload, headers, min(request_timeout, remaining))

            record("notes")
            store = ProfileStore(Path(sandbox) / "vault")
            store.save_import_text(
                "FICTIONAL ADULT TEST NOTES: I am 30. I value honesty and patient communication. "
                "I want a long-term relationship, with time to build trust. When upset I pause "
                "and discuss calmly later. I will not send money to an online-only contact. "
                "These limited notes do not establish stable personality traits.",
                "synthetic_notes.md",
            )
            result["steps"].append("notes")
            backend = ai_backend.OllamaChatBackend(
                model=model, timeout=timeout, transport=bounded_transport
            )
            record("portrait_generation_and_validation")
            portrait = ai_backend.run_self_portrait(backend, store)
            assert portrait.is_file()
            result["steps"].extend(["portrait", "validate_and_save"])
            print("Validated report structure; saved in temporary vault.", flush=True)
            record("interview_turn")
            history = [
                {
                    "role": "user",
                    "content": "I am a fictional adult aged 30. "
                    "I value honesty and patient communication. "
                    "Ask one question about my relationship boundaries.",
                }
            ]
            system = ai_backend.build_interview_system(store)
            reply = backend.chat(history, system=system)
            assert reply.strip()
            result["steps"].append("interview_turn")
            history.extend(
                [
                    {"role": "assistant", "content": reply},
                    {
                        "role": "user",
                        "content": "I will not send money to online-only contacts. "
                        "I prefer taking time to meet in a public place. "
                        "This is synthetic test data.",
                    },
                ]
            )
            record("criteria_generation_and_validation")
            criteria = ai_backend.run_criteria_synthesis(backend, store, history, system)
            record("final_artifact_checks")
            assert criteria.is_file() and store.ideal_profiles_json_path.is_file()
            result["steps"].extend(
                ["criteria_synthesis", "validate_and_save_criteria_and_profiles"]
            )
            result["status"] = "passed"
            record("complete")
    except Exception as exc:
        result["status"] = "failed"
        # Exception strings can contain generated/private content in future adapters.
        result["error_type"] = type(exc).__name__
        record()
        print(json.dumps(result), flush=True)
        return 1
    finally:
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    print(json.dumps(result), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--timeout", type=float, default=240, help="Total provider time budget (s)."
    )
    args = parser.parse_args(argv)
    if not 0 < args.timeout <= 600:
        parser.error("--timeout must be greater than 0 and at most 600 seconds")
    output = Path(__file__).resolve().parents[1] / "build" / "desktop-ai-journey.json"
    return run_chain(args.model, args.timeout, output)


if __name__ == "__main__":
    raise SystemExit(main())
