"""One-way, allowlisted Site source mirror; original repository stays authoritative.

No vault, repo metadata, credentials, logs or runtime state can enter the mirror.
The Sites workflow manages the mirror's own Git repository separately.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps" / "matching_site"
FILES = {
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "next.config.ts",
    "vite.config.ts",
    "postcss.config.mjs",
    "cloudflare-env.d.ts",
    "drizzle.config.ts",
    "eslint.config.mjs",
    "components.json",
    ".gitignore",
    ".npmrc",
    "README.md",
}
DIRS = {
    "app",
    "build",
    "db",
    "drizzle",
    "scripts",
    "lib",
    "components",
    "hooks",
    "public",
    "vendor",
}


def main():
    contract = ROOT / "src/anti_dating_scam/schemas/shareable_profile.schema.json"
    if json.loads(contract.read_text(encoding="utf-8")) != json.loads(
        (SOURCE / "lib/shareable-profile.schema.json").read_text(encoding="utf-8")
    ):
        raise ValueError("site_contract_out_of_sync")
    parent = Path(os.environ["LOCALAPPDATA"]) / "AI-SlowMatch" / "site-build"
    parent.mkdir(parents=True, exist_ok=True)
    parent = parent.resolve()
    destination = parent / "source"
    if destination.is_symlink():
        raise ValueError("unsafe_mirror")
    destination.mkdir(exist_ok=True)
    previous = destination / "source-map.json"
    selected = []
    for path in SOURCE.rglob("*"):
        rel = path.relative_to(SOURCE)
        if rel.parts[0] not in DIRS and rel.as_posix() not in FILES | {".openai/hosting.json"}:
            continue
        if path.is_symlink():
            raise ValueError("source_link_rejected")
        if path.is_file() and "__pycache__" not in rel.parts:
            selected.append(path)
    names = {p.relative_to(SOURCE).as_posix() for p in selected}
    if previous.exists():
        for name in json.loads(previous.read_text())["files"]:
            stale = (destination / name).resolve()
            if not stale.is_relative_to(destination) or stale == destination:
                raise ValueError("unsafe_previous_manifest")
            if name not in names and stale.is_file():
                stale.unlink()
    hashes = {}
    for path in selected:
        rel = path.relative_to(SOURCE)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = {
        "authority": "onepunchman26/Anti-Dating-App-Scam:apps/matching_site",
        "files": hashes,
    }
    previous.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    # Deployment output comes from this exact source, never from a private directory.
    if (SOURCE / "dist").exists():
        built = SOURCE / "dist"
        output = destination / "dist"
        # Never retain a previous release's assets in the next deployment archive.
        if output.is_symlink() or output.resolve().parent != destination.resolve():
            raise ValueError("unsafe_build_mirror")
        if built.is_symlink() or any(p.is_symlink() for p in built.rglob("*")):
            raise ValueError("build_link_rejected")
        if output.exists():
            if any(p.is_symlink() for p in output.rglob("*")):
                raise ValueError("mirror_link_rejected")
            # The packaging helper can mark generated directories read-only on Windows.
            for generated in [*output.rglob("*"), output]:
                generated.chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            shutil.rmtree(output)
        shutil.copytree(built, output)
    print(json.dumps({"checkout": str(destination), "source_files": len(hashes)}))


if __name__ == "__main__":
    main()
