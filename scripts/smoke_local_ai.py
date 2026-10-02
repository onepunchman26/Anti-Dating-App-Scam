"""Opt-in live loopback AI journey using a disposable, entirely synthetic vault."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="An already installed Ollama chat model")
    args = parser.parse_args()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="slowmatch-live-synthetic-") as sandbox:
        # Isolate before importing modules that resolve application paths.
        os.environ.update(HOME=sandbox, USERPROFILE=sandbox, ADS_NO_AUTOCONNECT="1")
        from fastapi.testclient import TestClient

        from anti_dating_scam.api.rendezvous_app import create_client_app

        with TestClient(create_client_app(), base_url="http://127.0.0.1:8471") as client:
            connected = client.post(
                "/local/ai/config",
                json={
                    "backend": "ollama",
                    "base_url": "http://127.0.0.1:11434",
                    "model": args.model,
                },
            )
            assert connected.status_code == 200 and connected.json()["ok"], "Local AI unavailable"
            print("Connected to local model; generating from synthetic notes.", flush=True)
            response = client.post(
                "/local/ai/synthesize",
                json={
                    "source_text": (
                        "FICTIONAL TEST NOTES: I am a 30-year-old adult. "
                        "I value honesty and patient communication. I want a long-term "
                        "relationship and eventually a shared home. "
                        "When conflict happens I prefer a pause and a calm discussion. "
                        "I will not send money or intimate images to an online-only contact. "
                        "These few notes cannot establish stable traits or predict compatibility."
                    ),
                    "language": "English",
                },
            )
            assert response.status_code == 200, (
                f"Synthesis failed: HTTP {response.status_code}: {response.json().get('detail')}"
            )
            card = {
                "schema_version": "0.1",
                "tier2_summary": response.json()["model"],
                "source": "self_model_from_ai_analysis_of_own_data",
            }
            saved = client.post("/local/profile/save", json={"profile": card})
            assert saved.status_code == 200, "Validated save failed"
            restored = client.get("/local/profile/load").json()
            assert restored["profile"] == card
            assert restored["fingerprint"] == saved.json()["fingerprint"]
            registration = client.post(
                "/matchmaking/register",
                json={
                    "pseudonym": "SyntheticAdult",
                    "age": 30,
                    "geohash": "wtw3",
                    "contact": "synthetic@example.test",
                    "consent_confirmed": True,
                },
            )
            assert registration.status_code == 200, "Synthetic registration failed"
            attested = client.post(
                "/matchmaking/attest",
                json={
                    "pseudonym": "SyntheticAdult",
                    "fingerprint": saved.json()["fingerprint"],
                },
                headers={"Authorization": "Bearer " + registration.json()["token"]},
            )
            assert attested.status_code == 200, "Fingerprint-only attestation failed"
            assert "synthetic@example.test" not in client.get("/local/status").text
            result = {
                "local_only": True,
                "synthetic_only": True,
                "model": args.model,
                "steps": [
                    "connect",
                    "synthesize",
                    "schema_validate",
                    "save",
                    "reload",
                    "fingerprint",
                    "adult_registration",
                    "attest_fingerprint_only",
                ],
                "elapsed_seconds": round(time.monotonic() - started, 2),
            }
            output = Path(__file__).resolve().parents[1] / "build" / "local-ai-journey.json"
            output.parent.mkdir(exist_ok=True)
            output.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
