"""Locate bundled browser assets without depending on the working directory."""

from importlib.resources import files
from pathlib import Path


def web_directory() -> Path:
    """Find assets in an installed wheel or a source checkout.

    Wheels and PyInstaller bundles unpack package resources to the filesystem,
    as required by Starlette's static file server.
    """
    try:
        return Path(str(files("rendezvous_web")))
    except ModuleNotFoundError:
        # Direct source launchers add src, but need not add apps to sys.path.
        return Path(__file__).resolve().parents[2] / "apps" / "rendezvous_web"
