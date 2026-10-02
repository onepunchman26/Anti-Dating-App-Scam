#!/usr/bin/env bash
# Build the self-contained macOS binary (and optionally a .app) for the
# rendezvous node demo. Must be run ON macOS — PyInstaller cannot cross-compile.
#
#   bash packaging/build_macos.sh          # console binary: dist/AI-SlowMatch-Node
#   APP=1 bash packaging/build_macos.sh    # windowed .app:  dist/AI-SlowMatch-Node.app
#
# The console binary prints logs and stops with Ctrl+C — recommended for a
# server. The .app variant has no console; quit it from the Dock. Both start
# the server on localhost:8470 and open the browser automatically.
#
# Note: unsigned binaries trigger Gatekeeper on other people's Macs. For
# personal/demo use: right-click -> Open the first time, or
#   xattr -d com.apple.quarantine dist/AI-SlowMatch-Node
# Proper distribution needs codesign + notarization (Apple Developer account).

set -euo pipefail
cd "$(dirname "$0")/.."

EXTRA=()
if [[ "${APP:-0}" == "1" ]]; then
  EXTRA+=(--windowed)
fi

python3 -m PyInstaller \
  --noconfirm --clean --onefile \
  --name "AI-SlowMatch-Node" \
  --paths "src" \
  --paths "apps" \
  --hidden-import rendezvous_web \
  --add-data "apps/rendezvous_web/index.html:rendezvous_web" \
  --add-data "src/anti_dating_scam/schemas:anti_dating_scam/schemas" \
  --add-data "src/anti_dating_scam/skills:anti_dating_scam/skills" \
  --add-data "src/anti_dating_scam/licenses:anti_dating_scam/licenses" \
  --workpath "${TMPDIR:-/tmp}/slowmatch-build" \
  --specpath "${TMPDIR:-/tmp}/slowmatch-build" \
  "${EXTRA[@]}" \
  run_rendezvous_node.py

echo
echo "Built into dist/ — run ./dist/AI-SlowMatch-Node (or open the .app)."
