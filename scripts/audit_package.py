"""Verify the promoted desktop's embedded code, version and native dependencies."""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path

from scripts.release_support import ReleaseError, digest


def audit_package(root: Path, executable: Path, metadata: dict) -> dict:
    import pefile
    import vosk
    from PyInstaller.archive.readers import CArchiveReader

    pe = pefile.PE(str(executable))
    try:
        if pe.OPTIONAL_HEADER.Subsystem != 2:
            raise ReleaseError("Desktop is not a windowed executable.")
        strings = {}
        for group in pe.FileInfo:
            for item in group:
                for table in getattr(item, "StringTable", []):
                    strings.update(table.entries)
        if (
            strings.get(b"ProductVersion", b"").decode() != metadata["version"]
            or strings.get(b"FileVersion", b"").decode() != metadata["version"]
            or strings.get(b"ProductName") != b"AI-SlowMatch"
        ):
            raise ReleaseError("Windows version metadata mismatch.")
    finally:
        pe.close()
    archive = CArchiveReader(str(executable))
    names = {name.replace("\\", "/"): name for name in archive.toc}
    info = json.loads(archive.extract(names["anti_dating_scam/build_info.json"]))
    if info != metadata:
        raise ReleaseError("Embedded build provenance mismatch.")
    for name in ("goutoujunshi-MIT.txt", "goutoujunshi-MIT-zh.txt"):
        resource = "anti_dating_scam/licenses/" + name
        if resource not in names or archive.extract(names[resource]) != (
            root / "src" / resource
        ).read_bytes():
            raise ReleaseError("Coaching attribution license missing or changed.")
    pyz = archive.open_embedded_archive("PYZ.pyz")
    verified = {}
    for name in pyz.toc:
        if name == "anti_dating_scam" or name.startswith("anti_dating_scam."):
            base = root / "src"
        elif name == "anti_dating_scam_desktop" or name.startswith("anti_dating_scam_desktop."):
            base = root / "apps" / "desktop_pyqt"
        else:
            continue
        path = base.joinpath(*name.split("."))
        path = (
            path.with_suffix(".py") if path.with_suffix(".py").is_file() else path / "__init__.py"
        )
        embedded = pyz.extract(name)
        if (
            not isinstance(embedded, types.CodeType)
            or compile(path.read_bytes(), embedded.co_filename, "exec", dont_inherit=True)
            != embedded
        ):
            raise ReleaseError("Embedded application code mismatch: " + name)
        verified[name] = digest(path)
    for required in (
        "anti_dating_scam.version",
        "anti_dating_scam.services.reflection_chat",
        "anti_dating_scam.services.relationship_exchange",
        "anti_dating_scam.services.relationship_comparison",
        "anti_dating_scam.ai.chatgpt_backend",
        "anti_dating_scam.services.voice_input",
    ):
        if required not in verified:
            raise ReleaseError("Missing required application module: " + required)
    for required in (
        "jwt",
        "jwt.algorithms",
        "cryptography.hazmat.primitives.ciphers.aead",
        "vosk",
    ):
        if required not in pyz.toc:
            raise ReleaseError("Missing authentication/encryption/voice dependency.")
    native = {}
    for filename in ("libvosk.dll", "libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll"):
        source = Path(vosk.__file__).parent / filename
        matches = [
            value for name, value in names.items() if name.lower().endswith("vosk/" + filename)
        ]
        if len(matches) != 1 or archive.extract(matches[0]) != source.read_bytes():
            raise ReleaseError("Voice dependency mismatch.")
        native[filename] = digest(source)
    rust = Path(importlib.util.find_spec("cryptography.hazmat.bindings._rust").origin)
    matches = [
        value
        for name, value in names.items()
        if "cryptography/hazmat/bindings/_rust" in name and name.endswith(".pyd")
    ]
    if len(matches) != 1 or archive.extract(matches[0]) != rust.read_bytes():
        raise ReleaseError("Cryptographic native dependency mismatch.")
    if "PySide6/QtMultimedia.pyd" not in names or not any(
        "/plugins/multimedia/" in name for name in names
    ):
        raise ReleaseError("Audio capture plugin missing.")
    if any("speech_models/" in name or "vosk-model-small" in name for name in names):
        raise ReleaseError("Unexpected downloaded speech model in package.")
    return {
        "embedded_modules": verified,
        "voice_dlls": native,
        "windows_version": metadata["version"],
        "embedded_metadata_matches": True,
    }
