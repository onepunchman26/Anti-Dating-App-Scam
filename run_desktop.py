import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root / "apps" / "desktop_pyqt"))

    from anti_dating_scam.launchers import desktop_main

    return desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
