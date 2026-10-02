"""Isolate home before collection: modules resolve vault pointers at import time."""

import tempfile
from pathlib import Path

import pytest

_home = None
_environment = None


def pytest_configure(config):
    global _home, _environment
    _home = tempfile.TemporaryDirectory(prefix="slowmatch-tests-")
    if config.option.basetemp is None:
        config.option.basetemp = str(Path(_home.name) / "cases")
    _environment = pytest.MonkeyPatch()
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
        _environment.setenv(key, _home.name)
    _environment.setenv("ADS_NO_AUTOCONNECT", "1")
    _environment.setenv("QT_QPA_PLATFORM", "offscreen")


def pytest_unconfigure(config):
    if _environment is not None:
        _environment.undo()
    if _home is not None:
        _home.cleanup()
