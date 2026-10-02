"""Source-checkout launcher for the loopback-only browser application."""

import sys
from pathlib import Path


def main() -> int:
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    from anti_dating_scam.launchers import web_main

    return web_main()


if __name__ == "__main__":
    raise SystemExit(main())
