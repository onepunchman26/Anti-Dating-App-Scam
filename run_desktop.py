import sys
from pathlib import Path


def main() -> int:
    try:
        import PySide6  # noqa: F401
    except ModuleNotFoundError:
        print(
            'PySide6 is required. Install dependencies with: pip install -e ".[desktop]"',
            file=sys.stderr,
        )
        return 1

    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root / "apps" / "desktop_pyqt"))

    from anti_dating_scam_desktop.app import run

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
