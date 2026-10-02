"""Run your own rendezvous node — the "private server" model (docs/14, ADR-013).

Anyone can host a node for their own community, like a private game server:

    python run_rendezvous_node.py [--host 127.0.0.1] [--port 8470]

The node now also serves the built-in web demo UI at "/" (apps/rendezvous_web),
so users only need a browser — no Python on their side. Runtime dependencies
are deliberately minimal (fastapi + uvicorn; a Raspberry Pi is enough): the
node is a bulletin board + notary only. It stores pseudonyms, coarse location
buckets, Tier-1 gates, blinded contacts, and card fingerprints — never
profiles, cards, chats, or analysis. All AI/data processing happens on each
user's own device with their own AI.

Flags:
    --no-ui             API-only node (no static UI mount).
    --demo-seed BUCKET  Register a few clearly-marked synthetic users in the
                        given geohash bucket so a single tester sees a live
                        "nearby" list. Synthetic data only; they never accept
                        introductions.

P0 note: state is in-memory (lost on restart) and the bind defaults to
localhost. Before exposing a node beyond localhost, put TLS in front of it and
read `docs/12_rendezvous_matchmaking_plan.md` §6 (P2 hardening). Browsers only
allow geolocation on secure contexts (https:// or localhost); on plain http
the UI falls back to manual location entry.
"""

import argparse
import sys
import threading
import webbrowser
from pathlib import Path


def _seed_demo_users(bucket: str) -> None:
    """Synthetic ambiance users (no real user data — see AGENTS.md privacy rule)."""
    from anti_dating_scam.api.routes_matchmaking import get_service
    from anti_dating_scam.matchmaking.rendezvous import MatchmakingError

    service = get_service()
    seeds = [
        ("demo_star", "woman", None, 31),
        ("demo_river", "man", ["woman"], 34),
        ("demo_moon", "nonbinary", None, 29),
    ]
    for pseudonym, gender, seeking, age in seeds:
        try:
            service.register(
                pseudonym=pseudonym,
                geohash=bucket,
                contact=f"{pseudonym}@example.test (synthetic demo user — will never reply)",
                consent_confirmed=True,
                age=age,
                # No seeking-age range: the mutual gate would otherwise hide the
                # seeds from any tester who leaves the optional age field empty.
                seeking_age_min=None,
                seeking_age_max=None,
                gender=gender,
                seeking_genders=seeking,
            )
        except MatchmakingError as exc:
            print(f"--demo-seed failed for bucket '{bucket}': {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        service.attest_card(
            pseudonym,
            {
                "schema_version": "0.1",
                "synthetic_demo": True,
                "tier2_summary": {
                    "values": ["honesty", "curiosity"],
                    "note": f"Synthetic demo card for {pseudonym}; not a real person.",
                },
            },
        )
    print(f"Seeded {len(seeds)} synthetic demo users in bucket '{bucket}'.")


def main() -> int:
    if not getattr(sys, "frozen", False):
        # Running from the repo: make src/ importable. In a PyInstaller bundle
        # the package is already baked into the executable.
        repo_root = Path(__file__).resolve().parent
        sys.path.insert(0, str(repo_root / "src"))

    parser = argparse.ArgumentParser(description="AI-SlowMatch rendezvous node")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8470)
    parser.add_argument("--no-ui", action="store_true", help="serve the API only, no web UI")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="do not auto-open the web UI in the default browser",
    )
    parser.add_argument(
        "--demo-seed",
        metavar="BUCKET",
        default=None,
        help="register synthetic demo users in this geohash bucket (e.g. wtw3)",
    )
    args = parser.parse_args()

    try:
        import uvicorn
    except ModuleNotFoundError:
        print("uvicorn is required: pip install fastapi uvicorn", file=sys.stderr)
        return 1

    from anti_dating_scam.api.rendezvous_app import DEFAULT_WEB_DIR, create_rendezvous_app

    web_dir = None if args.no_ui else DEFAULT_WEB_DIR
    app = create_rendezvous_app(web_dir=web_dir)

    if args.demo_seed:
        _seed_demo_users(args.demo_seed)

    # 0.0.0.0 is a bind address, not a browsable URL.
    shown_host = "localhost" if args.host == "0.0.0.0" else args.host
    url = f"http://{shown_host}:{args.port}/"
    if web_dir is not None:
        print(f"Web demo UI:     {url}")
        if args.host == "0.0.0.0":
            print("                 (listening on all interfaces - others on your "
                  "network use http://<this-machine's-IP>:%d/)" % args.port)
    print(f"Matchmaking API: http://{shown_host}:{args.port}/matchmaking")
    print("This node stores rendezvous metadata only - never profiles or cards.")

    if web_dir is not None and not args.no_browser:
        # Double-click UX for the packaged .exe/.app: open the UI once the
        # server has had a moment to bind. Daemon thread: never blocks exit.
        opener = threading.Timer(1.5, webbrowser.open, [url])
        opener.daemon = True
        opener.start()

    # Even rejected legacy query-token requests must not put credentials in logs.
    uvicorn.run(app, host=args.host, port=args.port, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
